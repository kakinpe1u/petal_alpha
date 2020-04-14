import pytz
from datetime import datetime
from django.conf import settings

from neomodel import (StructuredNode, UniqueIdProperty, IntegerProperty,
                      DateTimeProperty, StringProperty, BooleanProperty,
                      StructuredRel, db)

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

class AbstractNode(StructuredNode):
    # object_uuid = UniqueIdProperty(default = uuid1, unique_index = True)
    object_uuid = UniqueIdProperty()
    created = DateTimeProperty(default = get_time)
    timestamp = IntegerProperty(default = get_long_time)

    def get_labels(self):
        query = 'MATCH n WHERE id(n)=%d RETURN DISTINCT labels(n)' % self._id
        result, columns = db.cypher_query(query)
        return result[0][0]

    def get_child_label(self):
        return list(set(self.get_labels()) - set(settings.REMOVE_CLASSES))[0]

