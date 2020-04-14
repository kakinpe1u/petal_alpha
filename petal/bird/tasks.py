import pytz
from datetime import datetime
import logging

from django.conf import settings
from django.core.cache import cache

from celery import shared_task
from petalusers.models import PetalUser
from .models import Query, Keyword
from elasticsearch import Elasticsearch
from neomodel import DoesNotExist, db
from neo4j import CypherError
from elasticsearch.exceptions import (ElasticsearchException, TransportError,
                                      ConflictError, RequestError)

db.set_connection('bolt://neo4j:testing@139.88.179.199:7667')

log = logging.getLogger(__name__)

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
def create_keyword(text, relevance, query_param):
    """
    This function takes

    :param text:
    :param relevance:
    :param query_param:
    :return:
    """
    try:
        try:
            search_query = Query.nodes.get(search_query=query_param)
        except (Query.DoesNotExist, DoesNotExist) as e:
            raise create_keyword.retry(exc=e, countdown=3, max_retries=None)
        try:
            keyword = Keyword.nodes.get(keyword=text)
            rel = search_query.keywords.connect(keyword)
            rel.relevance = relevance
            rel.save()
            keyword.search_queries.connect(search_query)
            search_query.save()
            keyword.save()
            return True
        except (Keyword.DoesNotExist, DoesNotExist):
            keyword = Keyword(keyword=text).save()
            rel = search_query.keywords.connect(keyword)
            rel.relevance = relevance
            rel.save()
            keyword.search_queries.connect(search_query)
            search_query.save()
            keyword.save()
            return True
    except (CypherError, IOError) as e:
        log.exception("Cypher Exception: ")
        raise create_keyword.retry(exc=e, countdown=3, max_retries=None)


@shared_task()
def update_query_object(object_uuid, label=None, object_data=None, index="petal-search-base"):
    # from petalusers.serializers import PetalUserSerializer
    from bird.models import get_parent_entity

    if label is None:
        label = get_parent_entity(object_uuid).get_child_label().lower()
    log.critical("Updating Query Object")
    log.critical({"object_uuid": object_uuid})
    query = 'MATCH (a:%s {object_uuid:"%s"}) RETURN a' % \
            (label.title(), object_uuid)
    result, _ = db.cypher_query(query)

    if result.one:
        result.one.pull()
    else:
        raise update_query_object.retry(
            exception=DoesNotExist('Object with uuid: %s ' 'does not exist' % object_uuid),
            countdown=3, max_retries=None)

    # if label == "petaluser":
    #     instance = PetalUser.inflate(result.one)
    #     object_data = PetalUserSerializer(instance).data
    # else:
    #     error_dict = {
    #         "message": "Search False setup. "
    #                    "Object Data None, Instance not None",
    #         "instance_label": label,
    #         "instance_uuid": object_uuid,
    #     }
    #     log.critical(error_dict)
    #     return False
    if label == "article":
    try:
        es = Elasticsearch(settings.ELASTIC_SEARCH_HOST)
        res = es.index(index=index, doc_type=object_data['type'],
                       id=object_uuid, body=object_data)
    except (ElasticsearchException, TransportError,
            ConflictError, RequestError) as exception:
        raise update_query_object.retry(exc=exception, countdown=5, max_retries=None)
    except KeyError:
        error_dict = {
            "message": "Search: KeyError False creation",
            "instance_uuid": object_uuid,
            "object_data": object_data
        }
        log.critical(error_dict)
        return False
    try:
        if instance.search_id is None:
            instance.search_id = res['_id']
            instance.populated_es_index = True
            instance.save()
    except AttributeError:
        pass

    cache.delete("%s_search_update" % object_uuid)
    return result
