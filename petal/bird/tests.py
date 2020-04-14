import time
import pickle
from uuid import uuid1
from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User
from django.test.client import RequestFactory

from elasticsearch import Elasticsearch

from bird.tasks import (update_query, update_query_object)

from petalusers.serializers import PetalUserSerializer
from registration.utils import create_user_util_test

# class TestUpdateSearchQuery(TestCase):
#
#     def setUp(self):
#         settings.CELERY_ALWAYS_EAGER = True
#         self.username = "ooa3603"
#         self.petalusers = create_user_util_test(self.username)
#         self.user = User.objects.get(username=self.username)
#
#     def test_update_query_user_does_not_exist(self):
#         from bird.models import Query
#
#         test_query = Query(search_query=str(uuid1()))
#         test_query.save()
#
#         task_data = {
#             "username": str(uuid1()), "query_param": test_query.search_query,
#             "keywords": ['fake', 'keywords']
#         }
#
#         response = update_query.apply_async(kwargs=task_data)
#
#         while not response.ready():
#             time.sleep(1)
#         res = response.result
#
#         self.assertIsInstance(res, Exception)

def test_create_keyword_task_success_keyword_exists(self):
    from bird.models import Query, KeyWord

    query = Query(search_query=str(uuid1()))
    query.save()
    keyword = KeyWord(keyword="test")
    keyword.save()

    data = {
        "text": "test", "relevance": ".9",
        "query_param": query.search_query
    }