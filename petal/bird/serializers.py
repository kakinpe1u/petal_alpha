import pytz
from uuid import uuid1
from datetime import datetime
from django.core.cache import cache

from rest_framework import serializers
from rest_framework.reverse import reverse
from api.utils import (generate_job, collect_request_data, render_content)
from neomodel import db
from petalusers.models import PetalUser
from api.serializers import PetalSerializer

from bird.ontology import Article


def entity_count(question_uuid):
    query = 'MATCH (a:Question {object_uuid: "%s"})-' \
            '[:POSSIBLE_ANSWER]->(solutions:Solution) ' \
            'WHERE solutions.to_be_deleted = false ' \
            'RETURN count(DISTINCT solutions)' % question_uuid
    response, col = db.cypher_query(query)
    try:
        count = response[0][0]
    except IndexError:
        count = 0
    return count


class ArticleSerializer(PetalSerializer):
    summary = serializers.CharField(read_only=True)
    images = serializers.CharField(read_only=True)
    references = serializers.CharField(read_only=True)
    links = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    content = serializers.CharField(read_only=True)

    # def create(self, data):
    #     request = self.context["request"]
    #
    #     owner = PetalUser.get(request.user.username)
    #     data['owner_username'] = owner.username
    #     uuid = str(uuid1())
    #     data['content'] = render_content(
    #         data.get('content', ""))
    #
    #     article = Article.get(uuid)
    #     article.save()
    #     cache.set(article.object_uuid, article)
    #     return article
