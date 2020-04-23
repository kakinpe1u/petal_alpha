import pytz
import pickle
import operator
import logging

from django.conf import settings

from rest_framework import status

from datetime import datetime
from neomodel import (StringProperty, IntegerProperty,
                      DateTimeProperty, RelationshipTo, BooleanProperty)

from api.utils import request_to_api
from api.models import AbstractNode


log = logging.getLogger(__name__)


class Permission(AbstractNode):
    name = StringProperty(unique_index=True)

    # relationships
    actions = RelationshipTo('permissions.models.PetalAction', 'GRANTS')


class PetalAction(AbstractNode):
    resource = StringProperty(index=True)
    # If a user has write permission we assume they have read as well
    # this may change in the future but that should only require a search
    # for all write permissions and change to read/write or association of
    # read actions with the user. Write = POST, Read = GET, and PUT/PATCH can
    # always be performed by the user on their own content
    permission = StringProperty()
    url = StringProperty(index=True)

    # relationships
    privilege = RelationshipTo('permissions.models.Permission', 'PART_OF')
