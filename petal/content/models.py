
import pytz
import logging
from datetime import datetime

from django.core.cache import cache


from neomodel import (StringProperty, IntegerProperty,
                      Relationship, RelationshipTo, RelationshipFrom, StructuredRel,
                      BooleanProperty, FloatProperty, DateTimeProperty,
                      DoesNotExist, db)

from neo4j import CypherError
from bird.models import Searchable

class PetalContent(Searchable):
    content = StringProperty()
    url = StringProperty()  # non api location
    href = StringProperty()  # api location
    user_username = StringProperty()
    is_removed = BooleanProperty(default=False)
    to_be_deleted = BooleanProperty(default=False)
    added_to_search_index = BooleanProperty(default=False)

    owned_by = RelationshipTo('petaluser.models.PetalUser', 'USED_BY')

    @classmethod
    def get_model_name(cls):
        return cls.__name__

    def update(self, instance):
        pass

    def get_url(self, request):
        return None

def get_content(object_uuid):
    try:
        query = 'MATCH (a:PetalContent {object_uuid:"%s"}) return a' \
                % object_uuid
        result, _ = db.cypher_query(query)
        try:
            content = PetalContent.inflate(result.one)
        except AttributeError as e:
            return e
        return content
    except (CypherError, IOError, IndexError) as e:
        return e