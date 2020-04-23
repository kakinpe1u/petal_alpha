from django.utils.text import slugify
from django.core.cache import cache
from rest_framework.reverse import reverse

from neomodel import (db, StringProperty, RelationshipTo)

from content.models import PetalContent


# class BirdSolution(PetalContent):
#     table = StringProperty(default='bird_solutions')
#     action_name = StringProperty(default="offered a solution to your query")
#     parent_id = StringProperty()
#
#     @classmethod
#     def get_article(cls, object_uuid, request=None):
#         from articles.models import Article
#         from articles.serializers import ArticleSerializer
#         article = cache.get("%s_article" % object_uuid)
#         if article is None:
#             query = 'MATCH (solution:BirdSolution {object_uuid:"%s"})<-' \
#                     '[:MENTIONED_IN]-(species:Species)' \
#                     '<-[:ASSOCIATED_WITH]-' \
#                     '(article:Article) RETURN article' % object_uuid
#             res, _ = db.cypher_query(query)
#             if res.one:
#                 article = ArticleSerializer(
#                     Article.inflate(res.one), context={"request": request}).data
#                 cache.set("%s_article" % object_uuid, article)
#         return article