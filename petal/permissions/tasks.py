from celery import shared_task

from .utils import manage_permission_relation


@shared_task()
def check_permissions(username):
    res = manage_permission_relation(username)
    if isinstance(res, Exception):  # pragma: no cover

        raise check_permissions.retry(exc=res, countdown=3, max_retries=None)
    return True