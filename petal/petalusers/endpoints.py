import stripe
import pytz
from datetime import datetime, timedelta
from dateutil import parser
from operator import attrgetter
from elasticsearch import Elasticsearch, NotFoundError

from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.core.cache import cache
from django.template import RequestContext
from django.conf import settings

from rest_framework.throttling import UserRateThrottle
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.generics import (RetrieveUpdateDestroyAPIView, mixins)

from neomodel import db

from api import errors

from api.permissions import (IsSelfOrReadOnly,
                             IsAnonCreateReadOnlyOrIsAuthenticated)
from api.utils import get_filter_params, NeoQuerySet
from content.models import PetalContent
from content.serializers import PetalContentSerializer
from species.models import Species


from articles.serializers import ArticleSerializer
from .serializers import (UserSerializer, PetalUserSerializer,
                          ResetPasswordEmailSerializer,
                          EmailVerificationSerializer)
from .models import PetalUser
from .utils import get_filter_by


class LimitPerDayUserThrottle(UserRateThrottle):
    rate = '10/day'


class PasswordReset(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = ResetPasswordEmailSerializer
    throttle_classes = (LimitPerDayUserThrottle, )


class ResendEmailVerification(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = EmailVerificationSerializer
    throttle_classes = (LimitPerDayUserThrottle, )
    authentication_classes = (IsAuthenticated, )


def get_public_content(api, username, request):
        then = (datetime.now(pytz.utc) - timedelta(days=120)).strftime("%s")
        query = \
            '// Retrieve all the current users questions\n' \
            'MATCH (a:Pleb {username: "%s"})<-[:OWNED_BY]-' \
            '(questions:Question) ' \
            'WHERE questions.to_be_deleted = False AND questions.created > %s' \
            ' AND questions.is_closed = False ' \
            'RETURN questions, NULL AS solutions, ' \
            'questions.created AS created, NULL AS s_question UNION ' \
            '// Retrieve all the current users solutions\n' \
            'MATCH (a:Pleb {username: "%s"})<-' \
            '[:OWNED_BY]-(solutions:BirdSolution)<-' \
            '[:POSSIBLE_ANSWER]-(s_question:Question) ' \
            'WHERE s_question.to_be_deleted = False ' \
            'AND solutions.created > %s' \
            ' AND solutions.is_closed = False ' \
            'AND s_question.is_closed = False ' \
            'AND solutions.to_be_deleted = False ' \
            'RETURN solutions, NULL AS questions, ' \
            'solutions.created AS created, s_question AS s_question' \
            % (username, then, username, then)
        news = []
        res, _ = db.cypher_query(query)
        # Profiled with ~50 objects and it was still performing under 1 ms.
        # By the time sorting in python becomes an issue the above mentioned
        # ticket should be resolved.
        res = sorted(res, key=attrgetter('created'), reverse=True)[:5]
        page = api.paginate_queryset(res)
        for row in page:
            news_article = None
            if row.questions is not None:
                row.questions.pull()
                news_article = QuestionSerializerNeo(
                    Question.inflate(row.questions),
                    context={'request': request}).data
            elif row.solutions is not None:
                row.s_question.pull()
                row.solutions.pull()
                question_data = QuestionSerializerNeo(
                    Question.inflate(row.s_question)).data
                news_article = SolutionSerializerNeo(
                    Solution.inflate(row.solutions),
                    context={'request': request}).data
                news_article['question'] = question_data
            news.append(news_article)
        return api.get_paginated_response(news)


class UserViewSet(viewsets.ModelViewSet):
    """
    This ViewSet provides interactions with the base framework user. If you
    need to create/destroy/modify this is where it should be done.

    Limitations:
    Currently we still manage user creation through a different interface
    in the registration application. Eventually we'll look to utilize this
    endpoint from the registration application to create the user and create
    a more uniform user creation process that can be used throughout our
    different systems.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'

    permission_classes = (IsAuthenticated, IsSelfOrReadOnly)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
        es = Elasticsearch(settings.ELASTIC_SEARCH_HOST)
        try:
            es.delete(index="full-search-base", doc_type='profile',
                      id=instance.username)
        except NotFoundError:
            pass
        logout(self.request)
        # TODO we can also go and delete the pleb and content from here
        # or require additional requests but think we could spawn a task
        # that did all that deconstruction work rather than requiring an
        # app the hit a thousand endpoints.


class ProfileViewSet(viewsets.ModelViewSet):
    """
    This endpoint provides information for each of the registered users. It
    should not be used for creating users though as we lean on the Framework
    to accomplish user creation and authentication. This however is where all
    non-base attributes can be accessed. Users can access any other user's
    information as long as their authenticated but are limited to Read access
    if they are not the owner of the profile.

    Limitations:
    Currently we don't have fine grained permissions that enable us to restrict
    access to certain fields based on friendship status or user set permissions.
    We instead manage this in the frontend and only allow users browsing the
    web interface to see certain information. This is all done in the template
    though and any tech savvy person will still be able to check out the
    endpoint for the information. We'll want to eventually limit that here
    or in the serializer rather than higher up on the stack.
    """
    serializer_class = PlebSerializerNeo
    lookup_field = "username"
    queryset = NeoQuerySet(Pleb)
    permission_classes = (IsAnonCreateReadOnlyOrIsAuthenticated, )

    def get_object(self):
        return Pleb.get(self.kwargs[self.lookup_field])

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = Pleb.get(username=request.user.username, cache_buster=True)
        serializer = self.get_serializer(instance, data=request.data,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "TBD"},
                        status=status.HTTP_501_NOT_IMPLEMENTED)



    @action(methods=['get'], serializer_class=PetalContentSerializer)
    def public_content(self, request, username=None):
        filter_by = request.query_params.get('filter', "")
        try:
            additional_params = get_filter_params(filter_by, SBContent())
        except(IndexError, KeyError, ValueError):
            return Response(errors.QUERY_DETERMINATION_EXCEPTION,
                            status=status.HTTP_400_BAD_REQUEST)
        query = '(res:SBPublicContent)-[:OWNED_BY]->(a:Pleb ' \
                '{username: "%s"})' % username
        queryset = NeoQuerySet(
            SBContent, query=query).filter(
            'WHERE res.to_be_deleted=false %s' % additional_params)
        return self.get_paginated_response(
            self.serializer_class(self.paginate_queryset(queryset), many=True,
                                  context={'request': request}).data)

    @action(methods=['get'],
                  permission_classes=(IsAuthenticatedOrReadOnly,))
    def public(self, request, username=None):
        return get_public_content(self, username, request)


    @action(methods=['get'], serializer_class=ArticleSerializer,
                  permission_classes=(IsAuthenticatedOrReadOnly,))
    def articles(self, request, username):
        query = '(article:Article {reader_username: "%s"})-' \
                '[:OPENS]->(result:Article)' % username
        queryset = NeoQuerySet(Article, query=query).filter('WHERE result.active')
        return self.get_paginated_response(
            self.serializer_class(self.paginate_queryset(queryset), many=True,
                                  context={'request': request}).data)

