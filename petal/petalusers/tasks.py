from uuid import uuid1

from django.core import signing
from django.core.cache import cache

from celery import shared_task

from neomodel import DoesNotExist, db

from search.tasks import update_query_object
from neo4j import CypherError
from .models import PetalUser, OauthUser
from api.utils import generate_job

@shared_task()
def finalize_user_creation(username):
    try:
        petaluser = PetalUser.get(username=username, cache_buster=True)
    except (DoesNotExist, Exception) as e:
        raise finalize_user_creation.retry(
            exc=e, countdown=10, max_retries=None)
    task_list = {}
    task_data = {
        "object_uuid": petaluser.object_uuid,
        "label": "pleb"
    }
    task_list["add_object_to_search_index"] = generate_job(
        job_func=update_query_object,
        job_param=task_data,
        countdown=30)

    cache.delete(petaluser.username)
    return task_list


