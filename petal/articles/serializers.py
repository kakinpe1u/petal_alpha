import pytz
from uuid import uuid1
from datetime import datetime, timedelta
from django.conf import settings

from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.exceptions import ValidationError
from rest_framework import serializers, status

from neomodel import db

from .models import Article
from content.serializers import PetalContentSerializer
from .tasks import get_articles, create_article_summary
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

    def create(self, validated_data):
        request = self.context["request"]
        species = validated_data.pop('species', None)
        uuid = str(uuid1())
        href = reverse('article-detail', kwargs={"object_uuid": uuid},
                       request=request)
        article = Article(href=href, object_uuid=uuid,
                          parent_id=species.object_uuid,
                          **validated_data).save()
        species.articles_mentioned_in.connect(article)
        generate_job(job_func=create_article_summary, job_param={
            'object_uuid': article.object_uuid
        })
        return article

    # def create(self, validated_data):
    #     from species.models import Species
    #     request, _, _, _, _ = collect_request_data(self.context)
    #     query = 'MATCH (species:Species {reader_username: "%s"}) WITH article ' \
    #             'OPTIONAL MATCH (article)-[:OPENS]->' \
    #             '(article:Article) RETURN species, ' \
    #             'count(article) as article_count' % request.user.username
    #     result, _ = db.cypher_query(query)
    #     if result.one is not None:
    #         species = Species.inflate(result.one['species'])
    #     else:
    #         raise serializers.ValidationError(
    #             {"detail": "There's no species mentioned in this article.",
    #              "developer_message": "",
    #              "status_code": status.HTTP_404_NOT_FOUND})
    #     generate_job(job_func=get_articles,
    #                  job_param={"article_uuid": get_articles.object_uuid},
    #                  countdown=900)
    #     return query

    def update(self, instance, validated_data):
        instance.get('content', instance.content)
        instance.save()
        generate_job(job_func=create_article_summary,
                     job_param={
                         'object_uuid': instance.object_uuid
                     })
        return instance

    def get_url(self, obj):
        return obj.get_url(self.context.get('request', None))

    def get_species(self, obj):
        from species.models import Species
        from species.serializers import SpeciesSerializer
        request, expand, _, relations, expedite = collect_request_data(
            self.context,
            expedite_param=self.context.get('expedite_param', None),
            expand_param=self.context.get('expand_param', None))
        species = Species.get(object_uuid=obj.parent_id)
        if expand:
            return SpeciesSerializer(species).data
        return reverse('species-detail',
                       kwargs={'object_uuid': species.object_uuid},
                       request=self.context.get('request', None))

    def get_href(self, obj):
        return reverse('article',
                       kwargs={'object_uuid': obj.object_uuid},
                       request=self.context.get('request', None))
