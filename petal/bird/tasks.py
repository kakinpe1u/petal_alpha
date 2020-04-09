import pytz
from datetime import datetime
import logging

from django.conf import settings
from django.core.cache import cache

from celery import shared_task
from petalusers.models import PetalUser
from .models import Query
from elasticsearch import Elasticsearch
from neomodel import DoesNotExist, db
from neo4j import CypherError
from elasticsearch.exceptions import (ElasticsearchException, TransportError,
                                      ConflictError, RequestError)

db.set_connection('bolt://neo4j:testing@139.88.179.199:7667')

log = logging.getLogger(__name__)

@shared_task()
def update_query(username, query_param):
    try:
        response, _ = db.cypher_query("MATCH (a:PetalUser {username:'%s'}) RETURN a" % username)

        if response.one:
            response.one.pull()
            petalUser = PetalUser(response.one)
        else:
            raise update_query.retry(
                exc=DoesNotExist("That username: " "%s does not exist" % username),
                countdown=3, max_retries=None)
    except (CypherError, IOError) as exception:
        raise update_query.retry(exc=exception, countdown=3, max_retries=None)
    try:
        query = Query.nodes.get(query=query_param)
        if petalUser.searches.is_connected(query):
            relation = petalUser.searches.relationship(query)
            relation.times_searched += 1
            relation.last_searched += datetime.now(pytz.utc)
            relation.save()
            return True
        else:
            relation = petalUser.searches.connect(query)
            relation.save()
            query.searched_by.connect(petalUser)
            return True
    except (Query.DoesNotExist, DoesNotExist):
        query = Query(query=query_param)
        query.save()
        query.searched_by.connect(petalUser)
        relation = petalUser.searches.connect(query)
        relation.save()
        return True
    except (CypherError, IOError) as exception:
        raise update_query.retry(exc=exception, countdown=3, max_retries=None)
    except Exception as exception:
        raise update_query.retry(exc=exception, countdown=3, max_retries=None)


@shared_task()
def update_query_object(object_uuid, label=None, object_data=None, index="full-search-base"):
    from petalusers.serializers import PetalUserSerializer
    from api.models import get_parent_entity

    if label is None:
        label = get_parent_entity(
            object_uuid).get_child_label().lower()
    log.critical("Updating Query Object")
    log.critical({"object_uuid": object_uuid})
    query = 'MATCH (a:%s {object_uuid:"%s"}) RETURN a' % \
            (label.title(), object_uuid)
    response, _ = db.cypher_query(query)

    if response.one:
        response.one.pull()
    else:
        raise update_query_object.retry(
            exception=DoesNotExist('Object with uuid: %s ' 'does not exist' % object_uuid),
            countdown=3, max_retries=None)

    if label == "petaluser":
        instance = PetalUser.inflate(response.one)
        object_data = PetalUserSerializer(instance).data
    else:
        error_dict = {
            "message": "Search False setup. "
                       "Object Data None, Instance not None",
            "instance_label": label,
            "instance_uuid": object_uuid,
        }
        log.critical(error_dict)
        return False
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
    return response
