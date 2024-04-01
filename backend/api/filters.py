import django_filters

from .models import Recipe, Tag, Favorite


class RecipesFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(field_name='tags__slug', to_field_name='slug', queryset=Tag.objects.all())
    is_favorited = django_filters.BooleanFilter(method='filter_is_favorited')
    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited']

    def filter_is_favorited(self, queryset, filter_name, value):
        print('ok')
        if value and self.request.user.is_authenticated:
            user = self.request.user
            favorited_recipes_ids = Favorite.objects.filter(id_user=user).values_list('id_recipe', flat=True)
            queryset = queryset.filter(id__in=favorited_recipes_ids)
        return queryset