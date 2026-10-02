import json
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from recipes.models import Category, Ingredient, Recipe


class Command(BaseCommand):
    help = "Import initial recipe data into the production database."

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = "recipes_data.json"

        if not os.path.exists(file_path):
            raise CommandError(f"{file_path} was not found.")

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")

        if not username:
            raise CommandError(
                "DJANGO_SUPERUSER_USERNAME is not configured."
            )

        User = get_user_model()

        try:
            admin = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(
                f'Administrator "{username}" does not exist.'
            )

        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        categories = {}
        ingredients = {}

        for item in data:
            model = item["model"]
            fields = item["fields"]

            if model == "recipes.category":
                category, _ = Category.objects.get_or_create(
                    name=fields["name"],
                    defaults={
                        "emoji": fields.get("emoji", "🍽️")
                    },
                )

                categories[item["pk"]] = category

        for item in data:
            model = item["model"]
            fields = item["fields"]

            if model == "recipes.ingredient":
                ingredient, _ = Ingredient.objects.get_or_create(
                    name=fields["name"],
                    defaults={
                        "emoji": fields.get("emoji", "🍽️")
                    },
                )

                ingredients[item["pk"]] = ingredient

        imported_recipes = 0

        for item in data:
            if item["model"] != "recipes.recipe":
                continue

            fields = item["fields"]

            category = categories.get(fields["category"])

            recipe, created = Recipe.objects.get_or_create(
                name=fields["name"],
                owner=admin,
                defaults={
                    "category": category,
                    "cooking_time": fields["cooking_time"],
                    "difficulty": fields["difficulty"],
                    "description": fields.get("description", ""),
                    "image": fields.get("image") or None,
                },
            )

            ingredient_ids = fields.get("ingredients", [])

            recipe.ingredients.set(
                [
                    ingredients[ingredient_id]
                    for ingredient_id in ingredient_ids
                    if ingredient_id in ingredients
                ]
            )

            if created:
                imported_recipes += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import completed. "
                f"{imported_recipes} recipes created."
            )
        )