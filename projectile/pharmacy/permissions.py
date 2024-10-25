from rest_framework import permissions


class IsOwnerAndAdminForStock(permissions.IsAuthenticated):

    def has_permission(self, request, view):
        return request.user.is_staff

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return obj.product.organization == request.user.organization

        return False
