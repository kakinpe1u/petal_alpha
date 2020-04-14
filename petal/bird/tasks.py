import pytz
from datetime import datetime

from django.conf import settings
from django.core.cache import cache

from celery import shared_task
from .models import Query
from elasticsearch import Elasticsearch
from neomodel import DoesNotExist, db
from neo4j import CypherError
from elasticsearch.exceptions import (ElasticsearchException, TransportError,
                                      ConflictError, RequestError)

db.set_connection('bolt://neo4j:testing@139.88.179.199:7667')

@shared_task()
def update_query(query_param):
    try:
        query = Query.nodes.get(query=query_param)
        query.save()
    except (Query.DoesNotExist, DoesNotExist, CypherError, IOError) as exception:
        raise update_query.retry(exc=exception, countdown=3, max_retries=None)
    except Exception as exception:
        raise update_query.retry(exc=exception, countdown=3, max_retries=None)

@shared_task()
def update_query_object(object_uuid, label=None, object_data=None, index="petal-search-base"):
    query = 'MATCH (a:%s {object_uuid:"%s"}) RETURN a' % \
            (label.title(), object_uuid)
    result, _ = db.cypher_query(query)

    if result.one:
        result.one.pull()
    else:
        raise update_query_object.retry(
            exception=DoesNotExist('Object with uuid: %s ' 'does not exist' % object_uuid),
            countdown=3, max_retries=None)
    try:
        es = Elasticsearch(settings.ELASTIC_SEARCH_HOST)
        result = es.index(index=index, doc_type=object_data['type'],
                          id=object_uuid, body=object_data)
    except (ElasticsearchException, TransportError,
            ConflictError, RequestError) as exception:
        raise update_query_object.retry(exc=exception, countdown=5, max_retries=None)

    cache.delete("%s_search_update" % object_uuid)
    return result
