import os
from collections import defaultdict

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .filters import RecipesFilter
from .models import (CustomUser, Favorite, Ingredients, Recipe, ShoppigCart,
                     Subscription, Tag)
from .permissions import IsOwner
from .serializers import (CustomUserSerializer, IngredientRecipe,
                          IngredientSerializer, PasswordChangeSerializer,
                          RecipeSerializer, RegisterSerializer,
                          ShoppingCartFavoriteSerializer,
                          SubscriptionSerializer, TagSerializer)


class CustomNumberPaginator(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'


class CustomUserViewSet(mixins.ListModelMixin, mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin, mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    queryset = CustomUser.objects.all()
    pagination_class = CustomNumberPaginator
    serializer_class = CustomUserSerializer
    """Кастомный Viewset Пользователя."""

    def get_serializer_class(self):
        if self.action == 'create':
            return RegisterSerializer
        return CustomUserSerializer

    @action(detail=False, methods=['get'], url_path='me',
            permission_classes=[IsOwner])
    def get_your_profile(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='set_password',
            permission_classes=[IsOwner])
    def set_your_password(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['new_password']
        user = request.user
        user.set_password(password)
        user.save()
        return Response(
            {"detail": "Пароль успешно изменен"},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['get'], url_path='subscriptions',
            permission_classes=[IsAuthenticated])
    def get_user_subscriptions(self, request):
        subscriptions = CustomUser.objects.filter(
            pk__in=request.user.subscriber.all().values_list(
                'subscrib_to', flat=True))
        recipes_limit = request.query_params.get('recipes_limit', None)
        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                return Response(
                    {'message': 'recipes_limit должен быть целым числом'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        context = {
            'request': request,
            'user': request.user,
            'recipes_limit': recipes_limit
        }
        paginator = CustomNumberPaginator()
        paginated_queryset = paginator.paginate_queryset(
            subscriptions, request)
        serializer = SubscriptionSerializer(
            paginated_queryset, many=True, read_only=True, context=context)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe',
            permission_classes=[IsAuthenticated])
    def add_and_destroy_subscribe(self, request, pk=None):
        subscriber = request.user
        subscrib_to = get_object_or_404(CustomUser, id=pk)
        if request.method == 'POST':
            if subscriber == subscrib_to:
                return Response(
                    {'message': 'Вы не можете подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Subscription.objects.filter(
                    subscriber=subscriber, subscrib_to=subscrib_to).exists():
                return Response(
                    {'message': 'Вы уже подписаны на данного пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(
                subscriber=subscriber, subscrib_to=subscrib_to)
            recipes_limit = request.query_params.get('recipes_limit', None)
            if recipes_limit is not None:
                try:
                    recipes_limit = int(recipes_limit)
                except ValueError:
                    return Response(
                        {'message': 'recipes_limit должен быть целым числом'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            serializer = SubscriptionSerializer(
                subscrib_to, context={
                    'user': subscriber, 'recipes_limit': recipes_limit})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            subscribe_item = Subscription.objects.filter(
                subscriber=subscriber, subscrib_to=subscrib_to)
            if not subscribe_item:
                return Response(
                    {'message': 'Вы не подписаны на данного пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscribe_item.delete()
            return Response(
                {'message': 'Вы успешно отписались от пользователя'},
                status=status.HTTP_204_NO_CONTENT
            )


class TagViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    """Кастомный Viewset Тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientsViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                         viewsets.GenericViewSet):
    """Кастомный Viewset Ингридиентов."""
    queryset = Ingredients.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipesViewSet(viewsets.ModelViewSet):
    """Viewset Рецептов."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomNumberPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not IsOwner().has_object_permission(request, self, instance):
            return Response(
                {"detail": "Вы не являетесь автором этого рецепта."},
                status=status.HTTP_403_FORBIDDEN
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def get_a_list_to_shopping_cart(self, request):
        shopping_list = ShoppigCart.objects.filter(user_id=request.user)
        ingredient_quantities = defaultdict(int)
        for item in shopping_list:
            recipe = item.recipe_id
            ingredients_info = IngredientRecipe.objects.filter(
                recipe=recipe).values_list(
                'ingredient__name', 'ingredient__measurement_unit',
                'amount')
            for ingredient_info in ingredients_info:
                name, measurement_unit, amount = ingredient_info
                print(name, measurement_unit, amount)
                ingredient_quantities[(name, measurement_unit)] += amount
        data = ''
        for ingredient, quantity in ingredient_quantities.items():
            data += (f'{ingredient[0].capitalize()}'
                     f' ({ingredient[1]}) - {quantity}\n')
            response = HttpResponse(data, content_type='text/plain')
            response['Content-Disposition'] = ('attachment; '
                                               'filename="shopping_list.txt"')
        return response

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def add_and_destroy_to_shopping_cart(self, request, pk=None):
        user = request.user
        if request.method == 'POST':
            if not Recipe.objects.filter(pk=pk).exists():
                return Response(
                    {'message': 'Нет такого рецепта'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            recipe = self.get_object()
            if ShoppigCart.objects.filter(
                    user_id=user, recipe_id=recipe).exists():
                return Response(
                    {'message': 'Рецепт уже есть в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item = ShoppigCart.objects.create(
                user_id=user, recipe_id=recipe)
            serializer = ShoppingCartFavoriteSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            if not Recipe.objects.filter(pk=pk).exists():
                return Response(
                    {'message': 'Нет такого рецепта'},
                    status=status.HTTP_404_NOT_FOUND
                )
            recipe = self.get_object()
            cart_item = ShoppigCart.objects.filter(
                user_id=user, recipe_id=recipe)
            if not cart_item:
                return Response(
                    {'message': 'Такого рецепта нет в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item.delete()
            return Response(
                {'message': 'Рецепт успешно удален из списка покупок'},
                status=status.HTTP_204_NO_CONTENT
            )

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def add_and_destroy_to_favorite(self, request, pk=None):
        user = request.user
        if request.method == 'POST':
            if not Recipe.objects.filter(pk=pk).exists():
                return Response(
                    {'message': 'Нет такого рецепта'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            recipe = self.get_object()
            if Favorite.objects.filter(
                    id_user=user, id_recipe=recipe).exists():
                return Response(
                    {'message': 'Рецепт уже есть в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite_item = Favorite.objects.create(
                id_user=user, id_recipe=recipe)
            serializer = ShoppingCartFavoriteSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            if not Recipe.objects.filter(pk=pk).exists():
                return Response(
                    {'message': 'Нет такого рецепта'},
                    status=status.HTTP_404_NOT_FOUND
                )
            recipe = self.get_object()
            favorite_item = Favorite.objects.filter(
                id_user=user, id_recipe=recipe)
            if not favorite_item:
                return Response(
                    {'message': 'Такого рецепта нет в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite_item.delete()
            return Response(
                {'message': 'Рецепт успешно удален из избранного'},
                status=status.HTTP_204_NO_CONTENT
            )
