# Generated by Django 4.2.10 on 2024-05-24 09:09

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_ingredient_recipe_ingredients"),
    ]

    operations = [
        migrations.AddField(
            model_name="recipe",
            name="image",
            field=models.ImageField(null=True, upload_to="uploads/recipe"),
        ),
    ]