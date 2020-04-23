from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from api.utils import generate_job
from content.utils import get_ordering, DatabaseQuerySet
from search.tasks import update_query_object

from .serializers import SpeciesSerializer, article_count
from .models import Species


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = SpeciesSerializer
    lookup_field = "object_uuid"
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        article = self.request.query_params.get('article', '')
        article_query = '(a:Article {object_uuid:"%s"})-' \
                        '[:MENTIONED_IN]->' % article

        queryset = DatabaseQuerySet(Species, query=article_query, distinct=True)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return self.get_paginated_response(
            self.get_serializer(
                self.paginate_queryset(queryset), many=True,
                context={"request": self.request}).data)

    def get_object(self):
        return Species.get(self.kwargs[self.lookup_field])

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data,
                                         context={"request": request})
        if serializer.is_valid():
            instance = serializer.save(article=request.data.get('article', ''))
            generate_job(job_func=update_query_object,
                         job_param={"object_uuid": instance.object_uuid,
                                    "label": "species"})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_object()
        single_object = SpeciesSerializer(
            queryset, context={'request': request, "expand_param": True}).data
        return Response(single_object, status=status.HTTP_200_OK)

    @action(methods=['get'])
    def article_count(self, request, object_uuid=None):
        count = article_count(self.kwargs[self.lookup_field])
        return Response({"article_count": count}, status=status.HTTP_200_OK)

    @action(methods=['get'])
    def close(self, request, object_uuid=None):
        return Response({"detail": "TBD"},
                        status=status.HTTP_501_NOT_IMPLEMENTED)
