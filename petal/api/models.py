import pytz
from datetime import datetime
from uuid import uuid1
from django.conf import settings

from neomodel import (StructuredNode, UniqueIdProperty,
                      DateTimeProperty, db)
from neo4j import CypherError

def get_time():
    return datetime.now(pytz.utc)


class AbstractNode(StructuredNode):
    object_uuid = UniqueIdProperty()
    created = DateTimeProperty(default = get_time)

    def get_labels(self):
        query = 'MATCH n WHERE id(n)=%d RETURN DISTINCT labels(n)' % self._id
        result, columns = db.cypher_query(query)
        return result[0][0]

    def get_child_label(self):
        return list(set(self.get_labels()) - set(settings.REMOVE_CLASSES))[0]
