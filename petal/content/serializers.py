from django.conf import settings

from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.exceptions import ValidationError

from api.serializers import PetalSerializer
from api.utils import collect_request_data, generate_job

from petalusers.models import PetalUser

class PetalContentSerializer(PetalSerializer):
    object_uuid = serializers.CharField(read_only=True)

    content = serializers.CharField()
    profile = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    href = serializers.SerializerMethodField()

    def get_profile(self, obj):
        from petalusers.serializers import PetalUserSerializer
        request, expand, _, relation, _ = collect_request_data(
            self.context,
            expedite_param=self.context.get('expedite_param', None),
            expand_param=self.context.get('expand_param', None))
        owner_username = obj.owner_username
        if expand == "true":
            owner = PetalUser.get(username=owner_username)
            profile_dict = PetalUserSerializer(
                owner, context={'request': request}).data
        elif relation == 'hyperlink':
            profile_dict = reverse('profile-detail',
                                   kwargs={"username": owner_username},
                                   request=request)
        else:
            profile_dict = obj.owner_username
        return profile_dict

    def get_url(self, obj):
        request, _, _, _, _ = collect_request_data(self.context)
        if obj.url is None:
            try:
                return obj.get_url(request)
            except AttributeError:
                return None
        else:
            return obj.url

    def get_href(self, obj):
        request, _, _, _, _ = collect_request_data(self.context)
        if obj.href is None:
            try:
                return obj.get_href(request)
            except AttributeError:
                return None
        else:
            return obj.href

def validate_reader(request, instance):
    if request is None:
        raise serializers.ValidationError("Cannot update without request")
    if instance.reader_username is not None:
        if instance.reader_username != request.user.username:
            raise serializers.ValidationError("Only the reader can edit this")
    return True