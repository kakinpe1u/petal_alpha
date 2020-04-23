from celery import shared_task
from django.core.cache import cache
from api.utils import generate_summary

from neomodel import DoesNotExist, db
from neo4j import CypherError


@shared_task()
def get_articles(object_uuid):
    query = 'MATCH (article:Article {object_uuid: "%s"}) ' \
            'RETURN article' % object_uuid
    result, _ = db.cypher_query(query)
    return result
