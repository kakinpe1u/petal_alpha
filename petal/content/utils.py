import pytz
import datetime
import logging
from json import dumps
from copy import deepcopy

import six
from django.conf import settings

from rest_framework import serializers
from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.response import Response

from neomodel.exception import DoesNotExist
from neomodel import db
from neo4j import CypherError
from elasticsearch import exceptions as es_exceptions


# def get_filter_params(filter_by, instance):
#     additional_params = ""
#     if filter_by != "":
#         query_param = filter_by.split(' ')
#         query_property = query_param[0]
#         if hasattr(instance, query_property):
#             if(query_property == "created" or
#                     query_property == "last_edited_on"):
#                 query_operation = settings.QUERY_OPERATIONS[
#                     query_param[1]]
#                 query_condition = float(query_param[2])
#                 current_time = datetime.datetime.now(pytz.utc)
#                 time_diff = datetime.timedelta(seconds=query_condition)
#                 query_condition = (current_time -
#                                    time_diff).strftime("%s")
#                 additional_params = "AND res.%s %s %s" % (
#                     query_property, query_operation, query_condition)
#         else:
#             raise KeyError
#     return additional_params
#
#
# class DatabaseQuerySet(object):
#     def __init__(self, model=None, query=None, distinct=None):
#         self.model = model
#         self.distinct = distinct
#         self.query = query
#         self._result_cache = None
#         self._sticky_filter = False
#         self._for_write = False
#         self._prefetch_related_lookups = []
#         self._prefetch_done = False
#         self._known_related_objects = {}
#         self._fields = None
#
#     def __getitem__(self, index):
#         """
#         Retrieves an item or slice from the set of results.
#         """
#         if not isinstance(index, (slice,) + six.integer_types):
#             raise TypeError
#         assert ((not isinstance(index, slice) and (index >= 0)) or
#                 (isinstance(index, slice) and (index.start is None or index.start >= 0) and
#                  (index.stop is None or index.stop >= 0))), \
#             "Negative indexing is not supported."
#         if isinstance(index, slice):
#             if index.start is not None:
#                 start = int(index.start)
#             else:
#                 start = 0
#             if index.stop is not None:
#                 stop = int(index.stop)
#             else:
#                 stop = 0
#             limit = stop - start
#             exe_query = "MATCH %s WITH %s RETURN result " \
#                         "SKIP %d LIMIT %d" % (self.query, self.is_distinct(), start, limit)
#             queryset, _ = db.cypher_query(exe_query)
#             [row[0].pull() for row in queryset]
#             queryset = [self.model.inflate(instance[0]) for instance in queryset]
#             return queryset[::index.step] if index.step else queryset
#         queryset, _ = db.cypher_query("MATCH %s RETURN result SKIP %d LIMIT %d" % (
#             self.query, index, 1))
#         [row[0].pull() for row in queryset]
#         return [self.model.inflate(instance[0]) for instance in queryset][0]
#
#     def count(self):
#         result, _ = db.cypher_query("MATCH %s RETURN COUNT(%sres)" %
#                                  (self.query, self.is_distinct()))
#         return result.one
#
#     def filter(self, query_filter):
#         return self._filter_or_exclude(query_filter)
#
#     def _filter_or_exclude(self, query_filter):
#         return self._clone("%s %s" % (self.query, query_filter))
#
#     def order_by(self, query_order):
#         return self._clone(self.query, query_order=query_order)
#
#     def is_distinct(self):
#         if self.distinct:
#             return "DISTINCT "
#         else:
#             return ""
#
#     def _clone(self, query, query_order=None):
#         clone = self.__class__(
#             model=self.model, query=query, distinct=self.distinct,
#             query_order=query_order or self.query_order)
#         clone._for_write = self._for_write
#         clone._prefetch_related_lookups = self._prefetch_related_lookups[:]
#         clone._known_related_objects = self._known_related_objects
#         clone._fields = self._fields
#
#         return clone