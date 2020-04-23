from celery import shared_task
from django.core.cache import cache
from api.utils import generate_summary

from neomodel import DoesNotExist, db
from neo4j import CypherError
from .models import Article


@shared_task()
def get_articles(object_uuid):
    query = 'MATCH (article:Article {object_uuid: "%s"}) ' \
            'RETURN article' % object_uuid
    result, _ = db.cypher_query(query)
    return result

@shared_task()
def create_article_summary(object_uuid):
    try:
        article = Article.nodes.get(object_uuid=object_uuid)
    except (DoesNotExist, Article.DoesNotExist, CypherError, IOError) as e:
        raise create_article_summary.retry(exc=e, countdown=5,
                                           max_retries=None)
    summary = generate_summary(article.content)
    if summary is not None and summary != "":
        article.summary = summary
    article.save()
    cache.delete(article.object_uuid)

    return article
