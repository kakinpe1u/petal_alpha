from neomodel import db
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response

from neo4j import GraphDatabase, basic_auth


def birdhome(request):
    context = dict(query='')
    return render(request, 'bird/bird_e2b.html', context)

def birdresults(request):
    query = request.GET.get('q')
    # neo_client = GraphDatabase.driver("bolt://localhost:7687", auth=basic_auth("neo4j", "life"))
    neo_client = GraphDatabase.driver("bolt://139.88.179.199:7667", auth=basic_auth("neo4j", "testing"))
    with neo_client.session() as session:
        result = session.run('MATCH (a:Article) WHERE a.abstract CONTAINS \'{test}\' RETURN a'.format(test=query))
    articles = [article['a'] for article in result.records()]
    context = dict(papers=articles)
    return render(request, 'bird_results.html', context)


# def search_result_view(request):
#     return render(request, 'search.html')