from django.conf import settings
from django.core.management.base import BaseCommand

from elasticsearch import Elasticsearch


class Command(BaseCommand):
    args = 'None.'
    help = 'Deletes and recreates petal-search-base Elasticsearch index'

    def empty_elasticsearch(self):
        es = Elasticsearch(settings.ELASTIC_SEARCH_HOST)
        es.indices.delete(index='petal-search-base', ignore=[400, 404])
        es.indices.create(index='petal-search-base')
        print("Emptied petal-search-base data")

    def handle(self, *args, **options):
        self.empty_elasticsearch()
