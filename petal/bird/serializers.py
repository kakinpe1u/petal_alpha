import pytz
from bs4 import BeautifulSoup

from uuid import uuid1
from datetime import datetime

from rest_framework import serializers
from rest_framework.reverse import reverse

from api.utils import (collect_request_data, generate_job)
from content.serializers import PetalContentSerializer
from petalusers.models import PetalUser
from content.serializers import validate_reader
from .models import BirdSolution


class BirdSolutionSerializer(PetalContentSerializer):
    content = serializers.CharField(min_length=15)
    href = serializers.HyperlinkedIdentityField(view_name='solution-detail',
                                                lookup_field="object_uuid")
    parent_id = serializers.CharField(read_only=True)
    species = serializers.SerializerMethodField()
    article = serializers.SerializerMethodField()

    def create(self, validated_data):
        request = self.context["request"]
        species = validated_data.pop('species', None)
        reader = PetalUser.get(request.user.username)
        validated_data['reader_username'] = reader.username
        uuid = str(uuid1())

        href = reverse('solution-detail', kwargs={"object_uuid": uuid},
                       request=request)
        solution = BirdSolution(url=species.url, href=href, object_uuid=uuid,
                                parent_id=species.object_uuid,
                                **validated_data).save()
        solution.owned_by.connect(reader)
        species.solutions.connect(solution)
        return solution

    def update(self, instance, validated_data):
        validate_reader(self.context.get('request', None), instance)
        instance.last_edited_on = datetime.now(pytz.utc)
        instance.save()
        return instance

    def get_url(self, obj):
        return obj.get_url(self.context.get('request', None))

    def get_question(self, obj):
        from species.models import Species
        from species.serializers import SpeciesSerializer
        request, expand, _, relations, expedite = collect_request_data(
            self.context,
            expedite_param=self.context.get('expedite_param', None),
            expand_param=self.context.get('expand_param', None))
        species = Species.get(object_uuid=obj.parent_id)
        if expand:
            return SpeciesSerializer(species).data
        return reverse('question-detail',
                       kwargs={'object_uuid': species.object_uuid},
                       request=self.context.get('request', None))

    def get_article(self, obj):
        request, _, _, _, _ = collect_request_data(self.context)
        return obj.get_article(obj.object_uuid, request)