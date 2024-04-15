from django.contrib.auth.hashers import check_password
from django.core.validators import RegexValidator
from rest_framework import serializers, status
from rest_framework.validators import UniqueValidator

from api.fields import Base64ImageField, Hex2NameColor
from api.models import (CustomUser, Favorite, Ingredient, IngredientRecipe,
                        Recipe, RecipeTag, ShoppigCart, Subscription, Tag)


class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=150,
        validators=[
            UniqueValidator(queryset=CustomUser.objects.all()),
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message='Используются недопустимые символы в username'
            )
        ]
    )

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = CustomUser.objects.create_user(
            **validated_data, password=password)
        return user


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор модели пользователя."""
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            subscriber = request.user
            subscrib_to = obj
            return Subscription.objects.filter(
                subscriber=subscriber, subscrib_to=subscrib_to).exists()
        return False

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )


class PasswordChangeSerializer(serializers.ModelSerializer):
    """Сериализатор смены пароля пользователем."""
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    class Meta:
        model = CustomUser
        fields = ('new_password', 'current_password')

    def validate(self, data):
        user = self.context['request'].user
        current_password = data.get('current_password')
        if not check_password(current_password, user.password):
            raise serializers.ValidationError("Неверный текущий пароль.")
        return data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class RecipeTagsSerializer(serializers.ModelSerializer):
    """Сериализатор промежуточной таблицы рецептов и тегов."""
    id = serializers.IntegerField(source='tag.id')
    name = serializers.CharField(source='tag.name')
    color = Hex2NameColor(source='tag.color')
    slug = serializers.SlugField(source='tag.slug')

    class Meta:
        model = RecipeTag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор модели ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор промежуточной таблицы ингредиентов и рецептов."""
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов."""
    tags = RecipeTagsSerializer(
        source='recipetag_set', many=True, read_only=True)
    ingredients = IngredientRecipeSerializer(
        source='ingredientrecipe_set', many=True, read_only=True)
    author = CustomUserSerializer(
        read_only=True, default=serializers.CurrentUserDefault())
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(required=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def validate_cooking_time(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Время приготовления должно быть положительным числом",
                code=status.HTTP_400_BAD_REQUEST
            )
        return value

    def validate_tags(self, tags_data):
        if not tags_data:
            raise serializers.ValidationError(
                "Поле теги обязательно для заполнения",
                code=status.HTTP_400_BAD_REQUEST
            )

        if len(tags_data) != len(set(tags_data)):
            raise serializers.ValidationError(
                'Повторяющиеся теги в запросе',
                code=status.HTTP_400_BAD_REQUEST
            )

        for tag_id in tags_data:
            try:
                int(tag_id)
            except ValueError:
                raise serializers.ValidationError(
                    {"tags": "Тег должен иметь тип Int"},
                    code=status.HTTP_400_BAD_REQUEST
                )
            try:
                Tag.objects.get(pk=tag_id)
            except Tag.DoesNotExist:
                raise serializers.ValidationError(
                    "Тег с указанным ID не найден",
                    code=status.HTTP_400_BAD_REQUEST
                )
        return tags_data

    def validate_ingredients(self, ingredients_data):
        if not ingredients_data:
            raise serializers.ValidationError(
                'Поле ингредиенты обязательно для заполнения',
                code=status.HTTP_400_BAD_REQUEST
            )
        ingredient_ids = set()
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.get('id', None)
            amount = ingredient_data.get('amount', None)
            if amount is None or int(amount) <= 0:
                raise serializers.ValidationError(
                    'Количество ингридиента должно быть больше 0',
                    code=status.HTTP_400_BAD_REQUEST
                )
            try:
                Ingredient.objects.get(pk=ingredient_id)
            except Ingredient.DoesNotExist:
                raise serializers.ValidationError(
                    'Ингредиент с указанным ID не найден',
                    code=status.HTTP_400_BAD_REQUEST
                )
            if not ingredient_id:
                raise serializers.ValidationError(
                    'Не выбрано ни одного ингридиента',
                    code=status.HTTP_400_BAD_REQUEST
                )
            if ingredient_id in ingredient_ids:
                raise serializers.ValidationError(
                    'Повторяющиеся ингредиенты в запросе',
                    code=status.HTTP_400_BAD_REQUEST
                )
            ingredient_ids.add(ingredient_id)
        return ingredients_data

    def validate(self, data):
        data['tags'] = self.validate_tags(
            self.context['request'].data.get('tags')
        )
        data['ingredients'] = self.validate_ingredients(
            self.context['request'].data.get('ingredients')
        )
        data['author'] = self.context['request'].user
        return data

    def is_object_in_model(self, obj, model):
        user = self.context.get('request').user
        if user.is_authenticated:
            recipe = obj.id
            return model.objects.filter(user=user, recipe=recipe).exists()
        return False

    def get_is_favorited(self, obj):
        return self.is_object_in_model(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        return self.is_object_in_model(obj, ShoppigCart)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def create_or_update_tags_and_ingredients(
            self, recipe, tags_data, ingredients_data):
        recipe_tags_to_create = []
        for tag_data in tags_data:
            if tag_data:
                recipe_tags_to_create.append(RecipeTag(
                    tag_id=tag_data, recipe=recipe))
        RecipeTag.objects.bulk_create(recipe_tags_to_create)
        ingredients_recipe_to_create = []
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.get('id', None)
            amount = ingredient_data.get('amount', 0)
            if ingredient_id:
                ingredients_recipe_to_create.append(IngredientRecipe(
                    recipe=recipe, ingredient_id=ingredient_id, amount=amount))
        IngredientRecipe.objects.bulk_create(ingredients_recipe_to_create)

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.create_or_update_tags_and_ingredients(
            recipe, tags_data, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        instance.tags.clear()
        instance.ingredients.clear()
        self.create_or_update_tags_and_ingredients(
            instance, tags_data, ingredients_data)
        instance = super().update(instance, validated_data)
        return instance


class ShoppingCartFavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор списка покупок и избранного."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписок."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        recipes_limit = self.context.get('recipes_limit')
        recipes_queryset = obj.recipe_set.all()
        if recipes_limit is not None:
            recipes_queryset = recipes_queryset[:recipes_limit]
        return ShoppingCartFavoriteSerializer(recipes_queryset, many=True).data

    def get_is_subscribed(self, obj):
        user = self.context.get('user')
        if user and user.is_authenticated:
            return Subscription.objects.filter(
                subscriber=user, subscrib_to=obj).exists()
        return False

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes_count(self, instance):
        recipes_count = instance.recipe_set.count()
        return recipes_count
