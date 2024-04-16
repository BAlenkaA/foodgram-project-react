from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(
        max_length=254, unique=True, verbose_name='Электронная почта')
    username = models.CharField(
        max_length=150, unique=True, verbose_name='Имя пользовалеля')
    first_name = models.CharField(max_length=150, verbose_name='Имя')
    last_name = models.CharField(max_length=150, verbose_name='Фамилия')
    password = models.CharField(max_length=150, verbose_name='Пароль')

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['id']


class Tag(models.Model):
    name = models.CharField(
        max_length=200, unique=True, verbose_name='Название')
    color = models.CharField(max_length=7, unique=True, verbose_name='Цвет')
    slug = models.SlugField(
        max_length=200, db_index=True, unique=True, verbose_name='Слаг')

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=200, verbose_name='Единицы измерения')

    class Meta:
        ordering = ['name']
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, verbose_name='Автор')
    name = models.CharField(max_length=200, verbose_name='Название')
    image = models.ImageField(
        upload_to='api/images/', verbose_name='Фото готового блюда')
    text = models.TextField(verbose_name='Описание процесса приготовления')
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientRecipe')
    tags = models.ManyToManyField(
        Tag, through='RecipeTag', verbose_name='Тэги')
    cooking_time = models.PositiveIntegerField(
        default=0, verbose_name='Время приготовления')
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата создания')
    modified_at = models.DateTimeField(
        auto_now_add=False, auto_now=True, verbose_name='Дата изменения')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='recipetags',
        verbose_name='Тег'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт')

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Тег'
        constraints = (
            models.UniqueConstraint(
                fields=('tag', 'recipe'),
                name='recipetag_tag_recipe_unique'
            ),
        )

    def __str__(self):
        return 'тэг'


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredientrecipe',
        verbose_name='Ингредиент'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт')
    amount = models.PositiveIntegerField(default=0, verbose_name='Количество')

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиент'
        constraints = (
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='ingredientrecipe_ingredient_recipe_unique'
            ),
        )

    def __str__(self):
        return 'ингредиент'


class ShoppigCart(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт')

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='shoppigcart_user_recipe_unique'
            ),
        )


class Favorite(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='favorite_user',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipe',
        verbose_name='Рецепт'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='favorite_user_recipe_unique'
            ),
        )


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик'
    )
    subscrib_to = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscrib_to',
        verbose_name='Подписка'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('subscriber', 'subscrib_to'),
                name='subscription_subscriber_subscrib_to_unique'
            ),
        )
