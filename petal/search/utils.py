from django.conf import settings

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import TransportError, NotFoundError

def remove_query_object(object_uuid, object_type, index ="petal-search-base"):
    try:
        es = Elasticsearch(settings.ELASTIC_SEARCH_HOST)
        try:
            es.delete(index=index, doc_type=object_type, id=object_uuid)
        except NotFoundError:
            pass
        return True
    except TransportError:
        return False
