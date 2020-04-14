from django.conf import settings

from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.exceptions import ValidationError

from elasticsearch import Elasticsearch
from api import errors
from api.utils import generate_job
from bird.tasks import update_query


class SearchViewSet(ListAPIView):

    def get_queryset(self):
        filter_type = self.request.query_params.get("filter", "general")
        query_param = self.request.query_params.get("query", "")
        search_type_dict = dict(settings.SEARCH_TYPES)
        es = Elasticsearch(settings.ELASTIC_SEARCH_HOST)
        # TODO run query_param through natural language processor

        if filter_type is None or filter_type == 'general':
            result = es.search(
                index='petal-search-base', size=50,
                body={
                    "query": {
                        "match": {
                            "query": query_param,
                        }
                    }
                })
        else:
            try:
                result = es.search(
                    index='petal-search-base', size=50,
                    doc_type=search_type_dict[filter_type],
                    body={
                        "query": {
                            "match": {
                                "query": query_param,

                            }
                        }
                    })
            except KeyError:
                raise ValidationError("Invalid filter parameter")

        job_param = {"username": self.request.user.username,
                     "query_param": query_param,
                     }
        generate_job(job_func=update_query, job_param=job_param)
        return result['hits']['hits']

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
        except ValidationError:
            return Response(errors.QUERY_FILTER_EXCEPTION,
                            status=status.HTTP_400_BAD_REQUEST)
        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(page)
