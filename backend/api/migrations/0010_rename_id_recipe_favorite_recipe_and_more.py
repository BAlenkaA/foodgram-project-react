# Generated by Django 4.2.11 on 2024-04-15 08:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_rename_id_user_favorite_user'),
    ]

    operations = [
        migrations.RenameField(
            model_name='favorite',
            old_name='id_recipe',
            new_name='recipe',
        ),
        migrations.AlterUniqueTogether(
            name='favorite',
            unique_together={('user', 'recipe')},
        ),
    ]
