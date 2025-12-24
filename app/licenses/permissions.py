from rest_framework import permissions


class IsAuthenticatedBrandSystem(permissions.BasePermission):
    """
    Strictly limits access to authenticated Brand entities.
    Used for sensitive cross-brand lookups.
    """

    def has_permission(self, request, view):
        # request.user is populated as a Brand object by our custom Auth class
        from .models import Brand

        return isinstance(request.user, Brand)
