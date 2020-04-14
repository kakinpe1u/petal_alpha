from rest_framework import serializers

from api.utils import generate_job, collect_request_data
from bird.tasks import update_query_object

class NodeSerializer(serializers.Serializer):
    object_uuid = serializers.CharField(read_only=True)
    content = serializers.CharField()
    id = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    created = serializers.DateTimeField(read_only=True)
    url = serializers.SerializerMethodField()
    title = serializers.CharField(required=False,
                                  min_length=15, max_length=120)
    href = serializers.SerializerMethodField()
    summary = serializers.CharField(read_only=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    latitude = serializers.FloatField(required=False, allow_null=True)

    def get_id(self, object):
        try:
            return object.object_uuid
        except AttributeError:
            return None

    def get_type(self, object):
        return object.__class__.__name__.lower()


    def update(self, instance, data):
        task_param = {
            "object_uuid": instance.object_uuid,
            "label": instance.get_child_label().lower()
        }
        generate_job(job_func = update_query_object, job_param = task_param)
        return instance

    def get_url(self, obj):
        """
        url provides a link to the human viewable page that the object appears
        on. This is for user consumption and templates.
        """
        request, _, _, _, _ = collect_request_data(self.context)
        if obj.url is None:
            try:
                return obj.get_url(request)
            except AttributeError:
                return None
        else:
            return obj.url

    def get_href(self, obj):
        """
        href provides a link to the objects API detail endpoint. This is for
        programmatic access.
        """
        request, _, _, _, _ = collect_request_data(self.context)
        if obj.href is None:
            try:
                return obj.get_href(request)
            except AttributeError:
                return None
        else:
            return obj.href
