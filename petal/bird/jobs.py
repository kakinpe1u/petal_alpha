import pytz
from datetime import datetime

from django.conf import settings
from django.core.cache import cache

from celery import shared_task

from elasticsearch import Elasticsearch
from neomodel import DoesNotExist, db
from neo4j import CypherError
db.set_connection('bolt://neo4j:testing@139.88.179.199:7667')
from elasticsearch.exceptions import (ElasticsearchException, TransportError,
                                      ConflictError, RequestError)

from api.utils import generate_job
from petalusers.models import PetalUser
from bird.ontology import Article

from .models import Query, Keyword

@shared_task()
def update_query(username, query_param, keywords):

    """
    Creates a query node then calls the job to create and
    attach keyword nodes to the query node

    :param username:
    :param query_param:
    :param keywords:
    :return:
    """
    try:
        response, _ = db.cypher_query("MATCH (a:PetalUser {username:'%s'}) RETURN a" % username)

        if response.one:
            response.one.pull()
            petalUser = PetalUser(response.one)
        else:
            raise update_query.retry(
                exc = DoesNotExist("That username: " "%s does not exist" % username),
                countdown = 3, max_retries = None)
    except (CypherError, IOError) as exception:
        raise update_query.retry(exc = exception, countdown = 3, max_retries = None)
    try:
        query = Query.nodes.get(query = query_param)
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
        query = Query (query = query_param)
        query.save()
        query.searched_by.connect(petalUser)
        relation = petalUser.searches.connect(query)
        relation.save()

        for keyword in keywords:
            keyword["query_param"] = query_param
            generated = generate_job(job_func=generate_keyword, job_param = keyword)
            if isinstance(generated, Exception) is True:
                return generated
        return True
    except (CypherError, IOError) as exception:
        raise update_query.retry(exc=exception, countdown=3, max_retries=None)
    except Exception as exception:
        raise update_query.retry(exc=exception, countdown=3, max_retries=None)


@shared_task()
def generate_keyword(text, relevance, query_param):

    try:
        try:
            query = Query.nodes.get(query = query_param)
        except (Query.DoesNotExist, DoesNotExist) as exception:
            raise generate_keyword.retry(exc = exception, countdown = 3, max_retries = None)
        try:
            keyword = Keyword.nodes.get(keyword = text)
            relation = query.keywords.connect(keyword)
            relation.relevance = relevance
            relation.save()
            keyword.queries.connect(query)
            query.save()
            keyword.save()
            return True
        except (Keyword.DoesNotExist, DoesNotExist):
            keyword = Keyword(keyword = text).save()
            relation = query.keywords.connect(keyword)
            relation.relevance = relevance
            relation.save()
            keyword.queries.connect(query)
            query.save()
            keyword.save()
            return True
    except (CypherError, IOError) as exception:
        raise generate_keyword.retry(exc = exception, countdown = 3, max_retries = None)


@shared_task()
def update_query_object(object_uuid, label=None, object_data = None, index = "full-search-base"):
    from petalusers.serializers import PetalUserSerializer
    from bird.serializers import ArticleSerializer
    from api.models import get_parent_entity

    if label is None:
        label = get_parent_entity(
            object_uuid).get_child_label().lower()
    query = 'MATCH (a:%s {object_uuid:"%s"}) RETURN a' % \
            (label.title(), object_uuid)
    response, _ = db.cypher_query(query)
    if response.one:
        response.one.pull()
    else:
        raise update_query_object.retry(
            exception = DoesNotExist('Object with uuid: %s ' 'does not exist' % object_uuid),
            countdown = 3, max_retries=None)
    if label == "article":
        instance = Article.inflate(response.one)
        object_data = ArticleSerializer(instance).data
        if 'species' in object_data:
            object_data.pop('species')
        elif label == "petaluser":
            instance = PetalUser.inflate(response.one)
            object_data = PetalUserSerializer(instance).data
        else:
            error_dict = {
                "message": "Search False setup. "
                           "Object Data None, Instance not None",
                "instance_label": label,
                "instance_uuid": object_uuid,
            }
            return False






















