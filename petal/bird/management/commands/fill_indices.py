from django.core.management.base import BaseCommand
from django.conf import settings

from elasticsearch import Elasticsearch


class Command(BaseCommand):
    args = 'None.'
    help = 'Fills with placeholder representatives.'

    def fill_indices(self):
        es = Elasticsearch(settings.ELASTIC_SEARCH_HOST)
        es.indices.create('petal-search-base')
        print("populated all data")

    def handle(self, *args, **options):
        self.fill_indices()
