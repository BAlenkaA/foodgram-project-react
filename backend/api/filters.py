from django_filters import rest_framework as filters

from .models import Favorite, Recipe, ShoppigCart, Tag


class RecipesFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited']

    def filter_is_favorited(self, queryset, filter_name, value):
        if value and self.request.user.is_authenticated:
            user = self.request.user
            favorited_recipes = Favorite.objects.filter(
                user=user).values_list('recipe', flat=True)
            queryset = queryset.filter(id__in=favorited_recipes)
        return queryset

    def filter_shopping_cart(self, queryset, filter_name, value):
        if value and self.request.user.is_authenticated:
            user = self.request.user
            recipes_in_shopping_cart = ShoppigCart.objects.filter(
                user=user).values_list('recipe', flat=True)
            queryset = queryset.filter(id__in=recipes_in_shopping_cart)
        return queryset
