from rest_framework import serializers

from api.utils import generate_job
from bird.jobs import update_search_object

class SBSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    created = serializers.DateTimeField(read_only=True)

    def get_id(self, obj):
        try:
            return obj.object_uuid
        except AttributeError:
            return None

    def get_type(self, obj):
        return obj.__class__.__name__.lower()

    def update(self, instance, validated_data):
        task_param = {
            "object_uuid": instance.object_uuid,
            "label": instance.get_child_label().lower()
        }
        generate_job(job_func=update_search_object, job_param=task_param)
        return instance
