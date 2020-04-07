import pytz
from datetime import datetime

from django.conf import settings
from django.core.cache import cache

from celery import shared_task

from elasticsearch import Elasticsearch
from neomodel import DoesNotExist, db
from elasticsearch.exceptions import (ElasticsearchException, TransportError,
                                      ConflictError, RequestError)

from api.utils import generate_job
from petalusers.models import PetalUser