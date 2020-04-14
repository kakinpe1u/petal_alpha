import time
import pickle
from uuid import uuid1
from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User
from django.test.client import RequestFactory

from elasticsearch import Elasticsearch

from bird.tasks import (update_query, update_query_object)

import pytz
from datetime import datetime
from django.core.cache import cache

from neomodel import UniqueProperty
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import TransportError

