import logging
from django.core.management.base import BaseCommand
from django.conf import settings

from elasticsearch import Elasticsearch

log = logging.getLogger(__name__)


class Command(BaseCommand):
    args = 'None.'

    def populate_indices(self):
        es = Elasticsearch(settings.ELASTIC_SEARCH_HOST)
        if not es.indices.exists('petal-search-base'):
            es.indices.create('petal-search-base')
        if not es.indices.exists('tags'):
            es.indices.create('tags')
        if not es.indices.exists('petal-search-user-specific-1'):
            es.indices.create('petal-search-user-specific-1')

    def handle(self, *args, **options):
        self.populate_indices()
        log.info("Completed index population")
