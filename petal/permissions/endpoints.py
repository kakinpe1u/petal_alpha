from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination

from api.permissions import IsAdminOrReadOnly

from .serializers import PermissionSerializer
from .models import Permission


class PrivilegeViewSet(viewsets.ModelViewSet):
    serializer_class = PermissionSerializer
    lookup_field = "name"
    queryset = Permission.nodes.all()
    permission_classes = (IsAuthenticated, IsAdminOrReadOnly)
    pagination_class = LimitOffsetPagination

    def get_object(self):
        return Permission.nodes.get(name=self.kwargs[self.lookup_field])

    def create(self, request, *args, **kwargs):

        return Response({"detail": "TBD"},
                        status=status.HTTP_501_NOT_IMPLEMENTED)

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "TBD"},
                        status=status.HTTP_501_NOT_IMPLEMENTED)