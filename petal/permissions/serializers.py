from rest_framework import serializers

from api.serializers import PetalSerializer


class ActionSerializer(PetalSerializer):
    resource = serializers.CharField()
    permission = serializers.CharField()
    # href = serializers.HyperlinkedIdentityField()


class PermissionSerializer(PetalSerializer):
    name = serializers.CharField()
    href = serializers.HyperlinkedIdentityField(view_name="permission-detail",
                                                lookup_field="name")