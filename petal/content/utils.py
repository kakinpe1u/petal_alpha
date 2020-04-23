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


def get_ordering(sort_by):
    ordering = ""
    if '-' in sort_by:
        ordering = "DESC"
        sort_by = sort_by.replace('-', '')
    if sort_by == "created" or sort_by == "last_edited_on":
        sort_by = "ORDER BY res.%s" % sort_by
    else:
        sort_by = ""

    return sort_by, ordering

def get_filter_params(filter_by, sb_instance):
    additional_params = ""
    if filter_by != "":
        query_param = filter_by.split(' ')
        query_property = query_param[0]
        if hasattr(sb_instance, query_property):
            # right now only support filtering by created/last_edited_on
            if(query_property == "created" or
                    query_property == "last_edited_on"):
                query_operation = settings.QUERY_OPERATIONS[
                    query_param[1]]
                query_condition = float(query_param[2])
                current_time = datetime.datetime.now(pytz.utc)
                time_diff = datetime.timedelta(seconds=query_condition)
                query_condition = (current_time -
                                   time_diff).strftime("%s")
                additional_params = "AND res.%s %s %s" % (
                    query_property, query_operation, query_condition)
        else:
            raise KeyError
    return additional_params


class DatabaseQuerySet(object):
    """
    DatabaseQuerySet requires that you treat `result` as a keyword in your query. This
    is used as the result value that will be used to run orders and filters
    on and will eventually be returned.
    DatabaseQuerySet does not support multiple responses currently.
    DatabaseQuerySet expects "query" to be set to the root of the query you're
    attempting to execute. So there shouldn't be a MATCH or RETURN in it and
    it should use `result` to indicate the value that will be returned.
    """
    def __init__(self, model=None, query=None, using=None, hints=None,
                 distinct=None, descending=None, query_order=None):
        self.model = model
        self.distinct = distinct
        self.descending = descending
        self._db = using
        self._hints = hints or {}
        self.query = query or "(result:%s)" % \
                              self.model.__name__
        self.query_order = query_order or ""
        self._result_cache = None
        self._sticky_filter = False
        self._for_write = False
        self._prefetch_related_lookups = []
        self._prefetch_done = False
        self._known_related_objects = {}  # {rel_field, {pk: rel_obj}}
        self._fields = None

    def __getitem__(self, k):
        """
        Retrieves an item or slice from the set of results.
        """
        if not isinstance(k, (slice,) + six.integer_types):
            raise TypeError
        assert ((not isinstance(k, slice) and (k >= 0)) or
                (isinstance(k, slice) and (k.start is None or k.start >= 0) and
                 (k.stop is None or k.stop >= 0))), \
            "Negative indexing is not supported."
        if isinstance(k, slice):
            if k.start is not None:
                start = int(k.start)
            else:
                start = 0
            if k.stop is not None:
                stop = int(k.stop)
            else:
                stop = 0
            limit = stop - start
            exe_query = "MATCH %s WITH %s result %s %s " \
                        "RETURN result " \
                        "SKIP %d LIMIT %d" % (
                            self.query, self.is_distinct(), self.query_order,
                            self.reverse_order(), start, limit)
            qs, _ = db.cypher_query(exe_query)
            [row[0].pull() for row in qs]
            qs = [self.model.inflate(neoinstance[0]) for neoinstance in qs]
            return qs[::k.step] if k.step else qs
        qs, _ = db.cypher_query("MATCH %s RETURN result SKIP %d LIMIT %d" % (
            self.query, k, 1))
        [row[0].pull() for row in qs]
        return [self.model.inflate(neoinstance[0]) for neoinstance in qs][0]

    def count(self):
        result, _ = db.cypher_query("MATCH %s RETURN COUNT(%sres)" %
                                 (self.query, self.is_distinct()))
        return result.one

    def filter(self, query_filter):
        return self._filter_or_exclude(query_filter)

    def _filter_or_exclude(self, query_filter):
        return self._clone("%s %s" % (self.query, query_filter))

    def order_by(self, query_order):
        return self._clone(self.query, query_order=query_order)

    def is_distinct(self):
        if self.distinct:
            return "DISTINCT "
        else:
            return ""

    def reverse_order(self):
        if self.descending:
            return "DESC"
        else:
            return ""

    def _clone(self, query, query_order=None):
        clone = self.__class__(
            model=self.model, query=query, using=self._db,
            hints=self._hints, distinct=self.distinct,
            descending=self.descending,
            query_order=query_order or self.query_order)
        clone._for_write = self._for_write
        clone._prefetch_related_lookups = self._prefetch_related_lookups[:]
        clone._known_related_objects = self._known_related_objects
        clone._fields = self._fields

        return clone