from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """Пользователь может редактировать или удалять только свои рецепты."""

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user
