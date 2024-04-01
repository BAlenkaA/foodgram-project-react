from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, Ingredients, Recipe, Tag, IngredientRecipe, RecipeTags, Favorite

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
    model = RecipeTags
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
        return ", ".join([f'{ingredient.name} ({ingredient.measurement_unit})' for ingredient in obj.ingredients.all()])
    display_ingredients.short_description = 'Ингредиенты'

    def display_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    display_tags.short_description = 'Теги'

    def display_favorites(self, obj):
        return Favorite.objects.filter(id_recipe=obj).count()
    display_favorites.short_description = 'Добавлено в избранное'

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredients, IngredientsAdmin)
admin.site.register(Recipe, RecipeAdmin)

