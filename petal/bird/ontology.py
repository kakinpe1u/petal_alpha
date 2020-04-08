from django.core.cache import cache
from django.utils.text import slugify

from neomodel import (StructuredNode, StringProperty, db, DoesNotExist,
                      RelationshipTo, RelationshipFrom, Relationship)
from neo4j import CypherError

class Article(StructuredNode):
    __abstract_node__ = True
    __label__ = "Article"

    summary = StringProperty()
    images = StringProperty()
    references = StringProperty()
    links = StringProperty()
    title = StringProperty()
    content = StringProperty()
    uuid = StringProperty()
    # node_id = StringProperty(index = True)

    # Relationships
    article_relationship = Relationship(".article.Article", None)
    species_relationship = RelationshipTo(".species.Species", "MENTIONED_IN_ARTICLE")

    @classmethod
    def get(cls, object_uuid):
        article = cache.get(object_uuid)
        if article is None:
            response, _ = db.cypher_query(
                "MATCH (a:%s {object_uuid:'%s'}) RETURN a" % (
                    cls.__name__, object_uuid))
            try:
                try:
                    response[0][0].pull()
                except(CypherError, Exception):
                    pass
                article = cls.inflate(response[0][0])
            except IndexError:
                raise DoesNotExist('Article with id: %s '
                                   'does not exist' % object_uuid)
            cache.set(object_uuid, article)
        return article

class WikipediaArticle(Article):
    __label__ = "WikipediaArticle"
    pass

class Species(StructuredNode):
    Order = StringProperty()
    CatalogSource = StringProperty()
    Phylum = StringProperty()
    Genus = StringProperty()
    Family = StringProperty()
    Class = StringProperty()
    Name = StringProperty(required = True)
    uuid = StringProperty()
    # node_id = StringProperty(index = True)

    # Relationships (edges
    species_relationship = Relationship(".species.Species", None)
    article_relationship = RelationshipTo(".article.Article", "MENTIONS_SPECIES")

    @classmethod
    def get(cls, object_uuid):
        species = cache.get(object_uuid)
        if species is None:
            response, _ = db.cypher_query(
                "MATCH (a:%s {object_uuid:'%s'}) RETURN a" % (
                    cls.__name__, object_uuid))
            try:
                try:
                    response[0][0].pull()
                except(CypherError, Exception):
                    pass
                species = cls.inflate(response[0][0])
            except IndexError:
                raise DoesNotExist('Species with id: %s '
                                   'does not exist' % object_uuid)
            cache.set(object_uuid, species)
        return species
