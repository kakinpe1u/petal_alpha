from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.cache import cache

from elasticsearch import Elasticsearch

from petalusers.models import PetalUser
from petalusers.serializers import PetalUserSerializer


class Command(BaseCommand):
    args = 'None.'

    def update_pleb_search(self):
        es = Elasticsearch(settings.ELASTIC_SEARCH_HOST)
        petaluser = PetalUser.nodes.get(username="chris_cunningham")
        result = es.index(index='petal-search-base', doc_type='profile',
                          id=petaluser.object_uuid, body=PetalUserSerializer(petaluser).data)
        petaluser.search_id = result['_id']
        petaluser.populated_es_index = True
        petaluser.save()
        cache.delete(petaluser.username)

    def handle(self, *args, **options):
        self.update_pleb_search()
