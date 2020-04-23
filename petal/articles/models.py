import pytz
from datetime import datetime

from django.core.cache import cache
from django.utils.text import slugify
from django.conf import settings
from django.templatetags.static import static
from django.template.loader import render_to_string

from rest_framework import serializers, status
from rest_framework.reverse import reverse

from neomodel import (StringProperty, IntegerProperty,
                      Relationship, RelationshipTo, RelationshipFrom, StructuredRel,
                      BooleanProperty, FloatProperty, DateTimeProperty,
                      DoesNotExist, db)

from api.utils import (collect_request_data, generate_job)
from species.serializers import SpeciesSerializer
from neo4j import CypherError
from search.models import Searchable

class Article(Searchable):
    __label__ = "Article"

    summary = StringProperty()
    images = StringProperty()
    references = StringProperty()
    links = StringProperty()
    title = StringProperty()
    content = StringProperty()
    external_id = StringProperty(unique_index=True)
    site = StringProperty()
    crawled = DateTimeProperty()

    reader_username = StringProperty()

    # Relationships
    # associated_with = RelationshipTo('.models.PetalContent', 'ASSOCIATED_WITH')
    # article = Relationship(".article.Article", None)
    mentions_species = RelationshipTo(".species.Species", "MENTIONED_IN_ARTICLE")

    @classmethod
    def get(cls, object_uuid):
        article = cache.get("%s_article" % object_uuid)
        if article is None:
            result, _ = db.cypher_query(
                "MATCH (a:%s {object_uuid:'%s'}) RETURN a" % (
                    cls.__name__, object_uuid))
            try:
                try:
                    result[0][0].pull()
                except(CypherError, Exception):
                    pass
                article = cls.inflate(result[0][0])
            except IndexError:
                raise DoesNotExist('Article with id: %s does not exist' % object_uuid)
            cache.set(object_uuid, article)
        return article

    def get_species_mentioned(self, request=None):

        from api.models import AbstractNode
        from species.models import Species

        query = 'MATCH (a:Article {object_uuid: "%s"})-[:MENTIONED_IN_ARTICLE]->(s)' \
                'RETURN s' % self.object_uuid

        result, _ = db.cypher_query(query)
        if result.one:
            child_label = AbstractNode.inflate(result.one).get_child_label()

            if child_label == "Species":
                return SpeciesSerializer(Species.inflate(result.one),
                                         context={'request': request}).data
        else:
            return None

    # def get_articles(cls, object_uuid):
    #
    #     article = cache.get("%s_article" % object_uuid)
    #     if article is None:
    #         query = 'MATCH (solution:BirdSolution {object_uuid:"%s"})<-' \
    #                 '[:POSSIBLE_ANSWER]-(question:Question)' \
    #                 '<-[:ASSOCIATED_WITH]-' \
    #                 '(mission:Mission) RETURN mission' % object_uuid
    #         res, _ = db.cypher_query(query)
    #         if res.one:
    #             article = ArticleSerializer(
    #                 Article.inflate(res.one), context={"request": request}).data
    #             cache.set("%s_mission" % object_uuid, article)
    #     return article

    def get_article_title(self):
        if self.title:
            title = self.title
        else:
            if self.focus_name:
                title = self.focus_name.title().replace(
                    '-', ' ').replace('_', ' ')
            else:
                title = None
        return title


class WikipediaArticle(Article):
    __label__ = "WikipediaArticle"
    pass
