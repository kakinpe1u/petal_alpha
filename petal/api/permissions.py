from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):

    def has_object_permission(self, request, view, object):
        if (object.owner_username == request.user.username or
                request.user.is_staff):
            return True
        else:
            return False


class IsSelfOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, object):
        if request.method in permissions.SAFE_METHODS:
            return True

        return object.username == request.user.username


class IsAnonCreateReadOnlyOrIsAuthenticated(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method == "POST" and not request.user.is_authenticated():
            return True
        elif not request.user.is_authenticated() and request.method != "POST":
            return False
        elif request.method in permissions.SAFE_METHODS:
            return True

        return True

    def has_object_permission(self, request, view, object):
        if not request.user.is_authenticated():
            return False
        if request.method in permissions.SAFE_METHODS:
            return True

        return object.username == request.user.username


class IsUserOrAdmin(permissions.BasePermission):

    def has_object_permission(self, request, view, object):
        if object.user == request.user or request.user.is_staff:
            return True
        else:
            return False


class IsAdminOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.is_staff
