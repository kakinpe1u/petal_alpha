from django.core.cache import cache
from rest_framework.reverse import reverse
from django.utils.text import slugify


from neomodel import (StringProperty, IntegerProperty,
                      Relationship, RelationshipTo, RelationshipFrom, StructuredRel,
                      BooleanProperty, FloatProperty, DateTimeProperty,
                      DoesNotExist, db)

from neo4j import CypherError
from search.models import Searchable


class Species(Searchable):
    Order = StringProperty()
    CatalogSource = StringProperty()
    Phylum = StringProperty()
    Genus = StringProperty()
    Family = StringProperty()
    Class = StringProperty()
    Name = StringProperty()

    # Relationships
    articles_mentioned_in = RelationshipTo("articles.models.Article", "MENTIONS_SPECIES")

    @classmethod
    def get(cls, object_uuid):
        species = cache.get(object_uuid)
        if species is None:
            result, _ = db.cypher_query(
                "MATCH (species:%s {object_uuid:'%s'}) RETURN species" % (
                    cls.__name__, object_uuid))
            try:
                try:
                    result[0][0].pull()
                except(CypherError, Exception):
                    pass
                species = cls.inflate(result[0][0])
            except IndexError:
                raise DoesNotExist('Species with id: %s does not exist' % object_uuid)
            cache.set(object_uuid, species)
        return species

    def get_article_mentions(self):
        query = 'MATCH (species:Species {object_uuid: "%s"})' \
                '-[:MENTIONS_SPECIES]->(articles_mentioned_in:Article) ' \
                'RETURN articles_mentioned_in.object_uuid' % self.object_uuid
        result, _ = db.cypher_query(query)
        return [row[0] for row in result]

    def get_url(self, request=None):
        return reverse('species_detail_page',
                       kwargs={'species_uuid': self.object_uuid,
                               'slug': slugify(self.title)},
                       request=request)
