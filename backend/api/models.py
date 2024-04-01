from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(max_length=254, unique=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    password = models.CharField(max_length=150)

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'


class Tag(models.Model):
    name = models.CharField(max_length=200, unique=True)
    color = models.CharField(max_length=7, unique=True)
    slug = models.SlugField(max_length=200, db_index=True, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'


class Ingredients(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    measurement_unit = models.CharField(max_length=200, verbose_name='Единицы измерения')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'


class Recipe(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Автор')
    name = models.CharField(max_length=200, verbose_name='Название')
    image = models.ImageField(upload_to='api/images/')
    text = models.TextField()
    ingredients = models.ManyToManyField(Ingredients, through='IngredientRecipe')
    tags = models.ManyToManyField(Tag, through='RecipeTags')
    cooking_time = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'


class RecipeTags(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='recipetags', verbose_name='Тег')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(Ingredients, on_delete=models.CASCADE, related_name='ingredientrecipe', verbose_name='Ингредиент')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(default=0, verbose_name='Количество')


class ShoppigCart(models.Model):
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    recipe_id = models.ForeignKey(Recipe, on_delete=models.CASCADE)


class Favorite(models.Model):
    id_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    id_recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)


class Subscription(models.Model):
    subscriber = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='subscriber')
    subscrib_to = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='subscrib_to')
