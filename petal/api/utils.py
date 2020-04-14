from uuid import uuid1

import six
from django.conf import settings
from neomodel import db
from bs4 import BeautifulSoup


class NeoQuerySet(object):

    def __init__(self, model=None, query=None, using=None, hints=None,
                 distinct=None, descending=None, query_order=None):
        self.model = model
        self.distinct = distinct
        self.descending = descending
        self._db = using
        self._hints = hints or {}
        self.query = query or "(res:%s)" % \
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
            exe_query = "MATCH %s WITH %s res %s %s " \
                        "RETURN res " \
                        "SKIP %d LIMIT %d" % (
                            self.query, self.is_distinct(), self.query_order,
                            self.reverse_order(), start, limit)
            qs, _ = db.cypher_query(exe_query)
            [row[0].pull() for row in qs]
            qs = [self.model.inflate(neoinstance[0]) for neoinstance in qs]
            return qs[::k.step] if k.step else qs
        qs, _ = db.cypher_query("MATCH %s RETURN res SKIP %d LIMIT %d" % (
            self.query, k, 1))
        [row[0].pull() for row in qs]
        return [self.model.inflate(neoinstance[0]) for neoinstance in qs][0]

    def count(self):
        res, _ = db.cypher_query("MATCH %s RETURN COUNT(%sres)" %
                                 (self.query, self.is_distinct()))
        return res.one

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


def generate_job(job_func, job_param, countdown=0, job_id=None):
    if job_id is None:
        job_id = str(uuid1())
    try:
        return job_func.apply_async(kwargs=job_param, countdown=countdown,
                                    job_id=job_id)
    except (IOError, Exception) as exception:
        raise exception


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


def collect_request_data(context, expedite_param=None, expand_param=None):
    try:
        request = context['request']
        try:
            expand = request.query_params.get('expand', 'false').lower()
            expedite = request.query_params.get('expedite', "false").lower()
            relations = request.query_params.get(
                'relations', 'primaryKey').lower()
            html = request.query_params.get('html', 'false').lower()
            expand_array = request.query_params.get('expand_attrs', [])
            if html == 'true':
                expand = 'true'
        except AttributeError:
            try:
                expand = request.GET.get('expand', 'false').lower()
                expedite = request.GET.get('expedite', 'false').lower()
                relations = request.GET.get('relations', 'primaryKey').lower()
            except AttributeError:
                expand = 'false'
                expedite = 'false',
                relations = 'primaryKey'
                request = None
            expand_array = []
    except KeyError:
        expand = 'false'
        expedite = 'false'
        relations = "primaryKey"
        request = None
        expand_array = []

    if expedite_param is not None:
        expedite = 'true'
    if expand_param:
        expand = 'true'

    return request, expand, expand_array, relations, expedite

def truncate(content, length=100, suffix='...'):
    if len(content) <= length:
        return content
    return content[:length].rsplit(' ', 1)[0] + suffix

def remove_class_from_elements(soup, class_string, element='div'):
    [html_element['class'].remove(class_string)
     for html_element in soup.find_all(element, {'class': class_string})]
    return soup

def render_content(content):
    if content is not None:
        soup = BeautifulSoup(content, 'lxml')
        if content[:4] == "<h2>" or content[:4] == "<h2 ":
            # Only parse the content if we need to since it can be a long
            # process (lxml should make it pretty fast though)
            if "padding-top: 0; margin-top: 5px;" \
                    not in soup.h2.get('style', ''):
                soup.h2['style'] = soup.h2.get(
                    'style', '') + "padding-top: 0; margin-top: 5px;"
        elif content[:4] == "<h3>" or content[:4] == "<h3 ":
            if "padding-top: 0; margin-top: 5px;" \
                    not in soup.h3.get('style', ''):
                soup.h3['style'] = soup.h3.get(
                    'style', '') + "padding-top: 0; margin-top: 5px;"
        if 'medium-insert-buttons' in content:
            [div.extract() for div in soup.findAll(
                'div', {"class": "medium-insert-buttons"})]
        if 'medium-insert-caption-placeholder' in content:
            [div.extract() for div in soup.findAll(
                'figcaption', {"class": "medium-insert-caption-placeholder"})]
        if 'medium-insert-embeds-selected' in content:
            soup = \
                remove_class_from_elements(
                    soup, 'medium-insert-embeds-selected')
        return str(soup).replace("<html><body>", "")\
            .replace("</body></html>", "")
    else:
        return ""
