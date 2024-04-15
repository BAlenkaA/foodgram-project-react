from django.urls import include, path, re_path
from rest_framework import routers

from api.views import (CustomUserViewSet, IngredientsViewSet, RecipesViewSet,
                       TagViewSet)

router = routers.SimpleRouter()

router.register(r'recipes', RecipesViewSet, basename='recipes')
router.register(r'users', CustomUserViewSet, basename='users')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientsViewSet, basename='ingredients')

urlpatterns = [
    re_path(r'^auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
