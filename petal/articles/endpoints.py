from uuid import uuid1

from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import (viewsets, status)
from rest_framework.response import Response
from rest_framework.generics import (ListCreateAPIView)
from rest_framework.reverse import reverse
from rest_framework.decorators import action
from neomodel import db
from api.utils import generate_job
from content.views import ObjectCRUD
from species.models import Species

from .serializers import ArticleSerializer
from .models import Article


class ArticleViewSet(viewsets.ModelViewSet):
    serializer_class = ArticleSerializer
    lookup_field = "object_uuid"
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_object(self):
        return Article.nodes.get(object_uuid=self.kwargs[self.lookup_field])

# class ArticleCRUD(ObjectCRUD):
#     serializer_class = ArticleSerializer
#     lookup_field = "object_uuid"
#     lookup_url_kwarg = "solution_uuid"
#
#     def get_object(self):
#         return Article.nodes.get(
#             object_uuid=self.kwargs[self.lookup_url_kwarg])
#
#
# class ArticleListCreate(ListCreateAPIView):
#     serializer_class = ArticleSerializer
#     permission_classes = (IsAuthenticatedOrReadOnly,)
#     lookup_field = "object_uuid"
#
#     def get_queryset(self):
#         query = "(a:Species {object_uuid:'%s'})-" \
#                 "[:MENTIONED_IN_ARTICLE]->" \
#                 "(result:Article)" % self.kwargs[self.lookup_field]
#         return DatabaseQuerySet(Article, query=query, distinct=True)
#
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data,
#                                          context={"request": request})
#         if serializer.is_valid():
#             species = Species.nodes.get(
#                 object_uuid=self.kwargs[self.lookup_field])
#             instance = serializer.save(species=species)
#             query = "MATCH (a:Species {object_uuid:'%s'})-[:MENTIONED_IN]->" \
#                     "(b:Pleb) RETURN b" % (self.kwargs[self.lookup_field])
#             result, col = db.cypher_query(query)
#             serializer = serializer.data
#             article = species.get_article_mentions(species.object_uuid)
#             generate_job(job_param={
#                 "sb_object": serializer['object_uuid'],
#             })
#             return Response(serializer, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
