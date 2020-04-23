import pytz
from uuid import uuid1
from datetime import datetime

from django.core.cache import cache
from django.utils.text import slugify

from rest_framework import serializers
from rest_framework.reverse import reverse
from neomodel import db

from api.utils import (collect_request_data, generate_job)
from content.serializers import PetalContentSerializer, validate_reader
from petalusers.models import PetalUser
from bird.serializers import BirdSolutionSerializer
from bird.models import BirdSolution
from articles.models import Article

from .models import Species


def article_count(species_uuid):
    query = 'MATCH (a:Species {object_uuid: "%s"})-' \
            '[:MENTIONS_SPECIES]->(mentioned_in:Article) ' \
            'RETURN count(DISTINCT mentioned_in)' % species_uuid
    result, col = db.cypher_query(query)
    try:
        count = result[0][0]
    except IndexError:
        count = 0
    return count


class SpeciesSerializer(PetalContentSerializer):
    order = serializers.CharField()
    catalogsource = serializers.CharField()
    phylum = serializers.CharField()
    genus = serializers.CharField()
    family = serializers.CharField()
    clazz = serializers.CharField()
    name = serializers.CharField(required=True)
    article = serializers.SerializerMethodField()
    article_count = serializers.SerializerMethodField()
    views = serializers.SerializerMethodField()

    def create(self, validated_data):
        request = self.context["request"]
        article = None
        reader = PetalUser.get(request.user.username)
        article_id = validated_data.get('article', '')
        if article_id:
            article = Article.get(article_id)
        validated_data['reader_username'] = reader.username
        uuid = str(uuid1())
        href = reverse('species-detail', kwargs={'object_uuid': uuid},
                       request=request)
        species = Species(href=href, object_uuid=uuid,
                          **validated_data).save()
        if article is not None:
            article.associated_with.connect(species)
        species.refresh()
        cache.set(species.object_uuid, species)
        return species

    def update(self, instance, validated_data):
        validate_reader(self.context.get('request', None), instance)
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        cache.delete(instance.object_uuid)
        return super(SpeciesSerializer, self).update(
            instance, validated_data)

    def get_article_count(self, obj):
        return article_count(obj.object_uuid)

    def get_articles(self, object):
        expand_param = self.context.get('expand_param', None)
        request, expand, _, relations, expedite = collect_request_data(
            self.context,
            expedite_param=self.context.get('expedite_param', None),
            expand_param=expand_param)
        if expedite == "true":
            return []
        articles = []
        if expand == "true" and relations != "hyperlink":
            query = 'MATCH (a:Species {object_uuid: "%s"})' \
                '-[:MENTIONS_SPECIES]->(articles_mentioned_in:Article) ' \
                'RETURN articles' % object.object_uuid
            result, _ = db.cypher_query(query)
            articles = BirdSolutionSerializer(
                [BirdSolution.inflate(row[0]) for row in result], many=True,
                context={"request": request, "expand_param": expand_param}).data
        else:
            if relations == "hyperlink":
                articles = [
                    reverse('solution-detail',
                            kwargs={'object_uuid': solution_uuid},
                            request=request)
                    for solution_uuid in object.get_solution_ids()
                ]
            else:
                return articles

        return articles

    def get_href(self, obj):
        request, _, _, _, _ = gather_request_data(
            self.context,
            expedite_param=self.context.get('expedite_param', None),
            expand_param=self.context.get('expand_param', None))
        return reverse(
            'question-detail', kwargs={'object_uuid': obj.object_uuid},
            request=request)





















