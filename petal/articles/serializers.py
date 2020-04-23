import pytz
from datetime import datetime, timedelta
from django.conf import settings

from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.exceptions import ValidationError
from rest_framework import serializers, status

from neomodel import db

from .models import Article
from content.serializers import PetalContentSerializer
from api.utils import (collect_request_data, generate_job)

class ArticleSerializer(PetalContentSerializer):
    # provider = serializers.ChoiceField(choices=[
    #     ('sb_crawler', "Sagebrew Crawler"), ('webhose', "Webhose.io"),
    #     ('alchemyapi', 'IBM Alchemy API')
    # ])

    summary = serializers.CharField(read_only=True)
    images = serializers.URLField()
    references = serializers.CharField()
    links = serializers.ListField(child=serializers.URLField(),
                                  required=False)
    title = serializers.CharField()
    external_id = serializers.CharField()
    site = serializers.CharField()
    crawled = serializers.DateTimeField()

    # def validate_title(self, value):
    #     query = 'MATCH (article:Article {title: "%s"}) ' \
    #             'RETURN article' % value
    #     res, _ = db.cypher_query(query)
    #     if res.one is not None:
    #         raise ValidationError("This field must be unique")
    #     return value

    def create(self, validated_data):
        from species.models import Species
        request, _, _, _, _ = collect_request_data(self.context)
        query = 'MATCH (species:Species {reader_username: "%s"}) WITH article ' \
                'OPTIONAL MATCH (article)-[:OPENS]->' \
                '(article:Article) RETURN species, ' \
                'count(article) as article_count' % request.user.username

        result, _ = db.cypher_query(query)
        if result.one is not None:
            species = Species.inflate(result.one['species'])

        else:
            raise serializers.ValidationError(
                {"detail": "There's no species mentioned in this article.",
                 "developer_message": "",
                 "status_code": status.HTTP_404_NOT_FOUND})
        reader_username = request.user.username

        article = Article(reader_username=reader_username,
                          title=title,
                          wallpaper_pic=static(
                              'images/wallpaper_capitol_2.jpg'),
                          formatted_location_name=formatted_location_name) \
            .save()


    def get_href(self, obj):
        return reverse('article',
                       kwargs={'object_uuid': obj.object_uuid},
                       request=self.context.get('request', None))
