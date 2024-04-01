from rest_framework import permissions
from .models import Favorite


class IsOwner(permissions.BasePermission):
    """Пользователь может редактировать или удалять только свои рецепты."""

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user


class IsOwnerOfProfileOrCartOrFavorite(permissions.BasePermission):
    """Пользователь может иметь доступ только к своему списку покупок и избранному"""
    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user


class IsOwnerOfFavorite(permissions.BasePermission):
    """Разрешает доступ только владельцу избранного."""

    def has_permission(self, request, view):
        # Проверяем, что пользователь авторизован
        if not request.user.is_authenticated:
            return False

        # Проверяем, что пользователь отправляет запрос только к своему избранному
        if view.kwargs.get('pk') is not None:  # Предполагается, что идентификатор объекта избранного передается в URL
            favorite = Favorite.objects.filter(pk=view.kwargs['pk']).first()  # Получаем объект избранного
            if favorite is not None:
                return request.user == favorite.id_user  # Проверяем, что текущий пользователь является владельцем избранного
        return True  # Разрешаем доступ для GET-запросов

    def has_object_permission(self, request, view, obj):
        favorite = obj.favorite_set.filter(user=request.user).first()
        return favorite is not None and favorite.user == request.user