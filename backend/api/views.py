from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .filters import RecipesFilter
from .models import (CustomUser, Favorite, Ingredient, Recipe, ShoppigCart,
                     Subscription, Tag)
from .permissions import IsOwner
from .serializers import (CustomUserSerializer, IngredientSerializer,
                          PasswordChangeSerializer, RecipeSerializer,
                          RegisterSerializer, ShoppingCartFavoriteSerializer,
                          SubscriptionSerializer, TagSerializer)


class CustomNumberPaginator(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'


class CustomUserViewSet(mixins.ListModelMixin, mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin, mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    """Кастомный Viewset Пользователя."""
    queryset = CustomUser.objects.all()
    pagination_class = CustomNumberPaginator
    serializer_class = CustomUserSerializer

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

    def get_recipes_limit(self, request):
        recipes_limit = request.query_params.get('recipes_limit', None)
        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                raise ValidationError(
                    'recipes_limit должен быть целым числом')
        return recipes_limit

    @action(detail=False, methods=['get'], url_path='subscriptions',
            permission_classes=[IsAuthenticated])
    def get_user_subscriptions(self, request):
        subscriptions = CustomUser.objects.filter(
            pk__in=request.user.subscriber.all().values_list(
                'subscrib_to', flat=True))
        recipes_limit = self.get_recipes_limit(request)
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
            recipes_limit = self.get_recipes_limit(request)
            serializer = SubscriptionSerializer(
                subscrib_to, context={
                    'user': subscriber, 'recipes_limit': recipes_limit})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        subscribe_item = Subscription.objects.filter(
            subscriber=subscriber, subscrib_to=subscrib_to)
        if not subscribe_item.exists():
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
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipesViewSet(viewsets.ModelViewSet):
    """Viewset Рецептов."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwner]
    pagination_class = CustomNumberPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def get_a_list_to_shopping_cart(self, request):
        shopping_list = ShoppigCart.objects.filter(user=request.user)
        ingredient_quantities = shopping_list.values(
            'recipe__ingredientrecipe__ingredient__name',
            'recipe__ingredientrecipe__ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('recipe__ingredientrecipe__amount')
        ).values_list(
            'recipe__ingredientrecipe__ingredient__name',
            'recipe__ingredientrecipe__ingredient__measurement_unit',
            'total_amount'
        )

        data = ''
        for ingredient_info in ingredient_quantities:
            name, measurement_unit, amount = ingredient_info
            data += f'{name.capitalize()} ({measurement_unit}) - {amount}\n'

        response = HttpResponse(data, content_type='text/plain')
        response['Content-Disposition'] = ('attachment; '
                                           'filename="shopping_list.txt"')
        return response

    def add_and_destroy(
            self, request, pk=None, Model=None, message=''):
        user = request.user
        if request.method == 'POST':
            if not Recipe.objects.filter(pk=pk).exists():
                return Response(
                    {'message': 'Нет такого рецепта'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            recipe = self.get_object()
            if Model.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'message': f'Рецепт уже есть в {message}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Model.objects.create(user=user, recipe=recipe)
            serializer = ShoppingCartFavoriteSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            recipe = get_object_or_404(Recipe, id=pk)
            item = Model.objects.filter(user=user, recipe=recipe)
            if not item.exists():
                return Response(
                    {'message': f'Такого рецепта нет в {message}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            item.delete()
            return Response(
                {'message': 'Рецепт успешно удален'},
                status=status.HTTP_204_NO_CONTENT
            )

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def add_and_destroy_to_shopping_cart(self, request, pk=None):
        return self.add_and_destroy(
            request, pk=pk, Model=ShoppigCart, message='списке покупок')

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite',
        permission_classes=[IsAuthenticated]
    )
    def add_and_destroy_to_favorite(self, request, pk=None):
        return self.add_and_destroy(
            request, pk=pk, Model=Favorite, message='избранном')
