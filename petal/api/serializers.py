from rest_framework import serializers

from api.utils import generate_job
from bird.tasks import update_query_object

class NodeSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    created = serializers.DateTimeField(read_only=True)

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

