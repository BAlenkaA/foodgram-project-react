# Generated by Django 4.2.11 on 2024-04-11 19:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_alter_customuser_options_alter_recipe_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ingredientrecipe',
            options={'verbose_name': 'ингредиент', 'verbose_name_plural': 'Ингредиент'},
        ),
        migrations.AlterModelOptions(
            name='recipetags',
            options={'verbose_name': 'тег', 'verbose_name_plural': 'Тег'},
        ),
        migrations.AlterField(
            model_name='recipe',
            name='cooking_time',
            field=models.PositiveIntegerField(default=0, verbose_name='Время приготовления'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='image',
            field=models.ImageField(upload_to='api/images/', verbose_name='Фото готового блюда'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='text',
            field=models.TextField(verbose_name='Описание процесса приготовления'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='color',
            field=models.CharField(max_length=7, unique=True, verbose_name='Цвет'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(max_length=200, unique=True, verbose_name='Название'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='slug',
            field=models.SlugField(max_length=200, unique=True, verbose_name='Слаг'),
        ),
        migrations.AlterUniqueTogether(
            name='recipetags',
            unique_together={('tag', 'recipe')},
        ),
    ]
