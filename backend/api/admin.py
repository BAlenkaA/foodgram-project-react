from django.contrib import admin

from .models import (CustomUser, Favorite, Ingredient, IngredientRecipe,
                     Recipe, RecipeTag, Tag)

admin.site.empty_value_display = 'Не задано'


class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'email',
        'username',
        'first_name',
        'last_name',
    )
    list_filter = (
        'email',
        'username'
    )


class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'color',
        'slug'
    )


class IngredientsAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit'
    )
    list_filter = (
        'name',
    )


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    extra = 1


class RecipeTagsInline(admin.TabularInline):
    model = RecipeTag
    extra = 1


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'display_ingredients',
        'display_tags',
        'display_favorites'
    )
    list_filter = (
        'author',
        'name',
        'tags'
    )
    filter_horizontal = ('tags', 'ingredients')
    inlines = (IngredientRecipeInline, RecipeTagsInline)

    def display_ingredients(self, obj):
        ingredients = obj.ingredients.all().values_list(
            'name', 'measurement_unit')
        return ", ".join([f'{name} ({unit})' for name, unit in ingredients])
    display_ingredients.short_description = 'Ингредиенты'

    def display_tags(self, obj):
        tags = obj.tags.all().values_list('name', flat=True)
        return ", ".join([f'{name}' for name in tags])
    display_tags.short_description = 'Теги'

    def display_favorites(self, obj):
        return Favorite.objects.filter(recipe=obj).count()
    display_favorites.short_description = 'Добавлено в избранное'


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientsAdmin)
admin.site.register(Recipe, RecipeAdmin)
