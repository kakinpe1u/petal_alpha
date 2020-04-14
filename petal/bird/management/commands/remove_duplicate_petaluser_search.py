from django.conf import settings
from django.core.management.base import BaseCommand

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError

from petalusers.models import PetalUser


class Command(BaseCommand):
    args = 'None.'

    def remove_duplicate_petaluser_search(self):
        es = Elasticsearch(settings.ELASTIC_SEARCH_HOST)
        for petaluser in PetalUser.nodes.all():
            try:
                es.delete(index='petal-search-base', doc_type='profile',
                          id=petaluser.username)
            except NotFoundError:
                pass

    def handle(self, *args, **options):
        self.remove_duplicate_petaluser_search()
