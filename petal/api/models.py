import pytz
from datetime import datetime
from uuid import uuid1
from django.conf import settings

from neomodel import (StructuredNode, UniqueIdProperty, IntegerProperty,
                      DateTimeProperty, StringProperty, BooleanProperty,
                      StructuredRel, RelationshipTo, db)
from neo4j import CypherError

def get_time():
    return datetime.now(pytz.utc)


def get_long_time():
    return int(datetime.now(pytz.utc).strftime("%s")) * 1000

def get_current_time():
    return datetime.now(pytz.utc)

class RelationshipWeight(StructuredRel):
    weight = IntegerProperty(default=150)
    status = StringProperty(default='seen')
    seen = BooleanProperty(default=True)


class EditRelationshipModel(StructuredRel):
    time_edited = DateTimeProperty(default = lambda: datetime.now(pytz.utc))

class SharedOnRel(StructuredRel):
    shared_on = DateTimeProperty(default = get_current_time)

class PetalObject(StructuredNode):
    # object_uuid = UniqueIdProperty(default = uuid1, unique_index = True)
    object_uuid = UniqueIdProperty()
    created = DateTimeProperty(default = get_time)
    timestamp = IntegerProperty(default = get_long_time)

    def get_labels(self):
        query = 'MATCH n WHERE id(n)=%d RETURN DISTINCT labels(n)' % self._id
        response, columns = db.cypher_query(query)
        return response[0][0]

    def get_child_label(self):
        return list(set(self.get_labels()) - set(settings.REMOVE_CLASSES))[0]

# class Entities:
#     content = StringProperty()
#     owned_by = RelationshipTo('petalusers.models.PetalUser', 'OWNED_BY', model = SharedOnRel)

# class PetalEntities(Entities):
#
#     relationship_weight = RelationshipTo('petalusers.models.PetalUser', 'HAS_WEIGHT',
#                                          model = RelationshipWeight)
#
#     @classmethod
#     def get_model_name(cls):
#         return cls.__name__
#
#     def update(self, instance):
#         pass
#
# def get_parent_entity(object_uuid):
#     try:
#         query = 'MATCH (a:Entities {object_uuid:"%s"}) RETURN a' % (
#             object_uuid)
#         response, column = db.cypher_query(query)
#         try:
#             entity = Entities.inflate(response[0][0])
#         except ValueError:
#             entity = Entities.inflate(response[0][0][0])
#         return entity
#     except(CypherError, IOError, IndexError) as exception:
#         return exception
