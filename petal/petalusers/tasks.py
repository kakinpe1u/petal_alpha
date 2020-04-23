from uuid import uuid1

from django.core import signing
from django.core.cache import cache

from celery import shared_task

from neomodel import DoesNotExist, db

from api.utils import generate_job, generate_oauth_user
from bird.tasks import update_query_object
from neo4j import CypherError
from .models import PetalUser, OauthUser


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


@shared_task()
def create_wall_task(username=None):
    from petalusers.models import Wall
    try:
        query = 'MATCH (petaluser:PetalUser {username: "%s"})' \
                '-[:OWNS_WALL]->(wall:Wall) RETURN wall' % username
        result, _ = db.cypher_query(query)
        if result.one is None:
            wall = Wall(wall_id=str(uuid1())).save()
            query = 'MATCH (petaluser:PetalUser {username: "%s"}),' \
                    '(wall:Wall {wall_id: "%s"}) ' \
                    'CREATE UNIQUE (petaluser)-[:OWNS_WALL]->(wall) ' \
                    'RETURN wall' % (username, wall.wall_id)
            result, _ = db.cypher_query(query)
        spawned = generate_job(job_func=finalize_user_creation,
                               job_param={"username": username})
        if isinstance(spawned, Exception) is True:
            raise create_wall_task.retry(exc=spawned, countdown=3,
                                         max_retries=None)
    except (CypherError, IOError) as e:
        raise create_wall_task.retry(exc=e, countdown=3, max_retries=None)
    return spawned


@shared_task
def generate_oauth_info(username, password, web_address=None):
    try:
        petaluser = PetalUser.get(username=username, cache_buster=True)
    except (DoesNotExist, CypherError, IOError) as e:
        raise generate_oauth_info.retry(exc=e, countdown=3, max_retries=None)
    credentials = generate_oauth_user(petaluser, password, web_address)

    if isinstance(credentials, Exception):
        raise generate_oauth_info.retry(exc=credentials, countdown=3,
                                        max_retries=None)
    try:
        oauth_object = OauthUser(access_token=signing.dumps(credentials['access_token']),
                                 token_type=credentials['token_type'],
                                 expires_in=credentials['expires_in'],
                                 refresh_token=signing.dumps(
                                     credentials['refresh_token']))
        oauth_object.save()
    except(CypherError, IOError) as e:
        return e

    try:
        petaluser.oauth.connect(oauth_object)
    except(CypherError, IOError) as e:
        return e

    return True
