from django.conf import settings
from django.core.management.base import BaseCommand

from elasticsearch import Elasticsearch


class Command(BaseCommand):
    args = 'None.'
    help = 'Deletes and recreates petal-search-base Elasticsearch index'

    def remove_petal_search_base(self):
        es = Elasticsearch(settings.ELASTIC_SEARCH_HOST)
        es.indices.delete(index='petal-search-base')
        # es.indices.create(index='petal-search-base')
        print("Emptied petal-search-base data")

    def handle(self, *args, **options):
        self.remove_petal_search_base()
