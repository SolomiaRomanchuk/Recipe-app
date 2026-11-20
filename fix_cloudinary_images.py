
import os
import json
import django
from pathlib import Path

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "recipe_project.settings"
)
django.setup()

import cloudinary.api
from django.conf import settings
from django.db import transaction
from recipes.models import Recipe


# True = тільки перевірка
# False = оновлення PostgreSQL
DRY_RUN = False

BACKUP_FILE = Path("image_paths_backup.json")


# Перевіряємо базу даних
engine = settings.DATABASES["default"]["ENGINE"]

print(f"Database: {engine}")

if engine != "django.db.backends.postgresql":
    raise RuntimeError(
        "PostgreSQL is not connected. "
        "Check DATABASE_URL in .env"
    )


# Отримуємо фотографії з Cloudinary
resources = []
next_cursor = None

while True:
    params = {
        "type": "upload",
        "resource_type": "image",
        "max_results": 500,
    }

    if next_cursor:
        params["next_cursor"] = next_cursor

    response = cloudinary.api.resources(**params)

    resources.extend(response.get("resources", []))

    next_cursor = response.get("next_cursor")

    if not next_cursor:
        break

print(f"Found {len(resources)} Cloudinary images")


# Створюємо резервну копію шляхів
recipes = list(Recipe.objects.all())

if not DRY_RUN:
    if BACKUP_FILE.exists():
        raise RuntimeError(
            f"{BACKUP_FILE} already exists. "
            "Keep the previous backup safe before continuing."
        )

    backup = [
        {
            "id": recipe.pk,
            "name": recipe.name,
            "image": recipe.image.name if recipe.image else ""
        }
        for recipe in recipes
    ]

    with BACKUP_FILE.open("x", encoding="utf-8") as file:
        json.dump(backup, file, indent=2, ensure_ascii=False)

    print(f"Backup saved: {BACKUP_FILE}")


updated = 0
missing = 0
multiple = 0
unchanged = 0

for recipe in recipes:

    if not recipe.image:
        print(f"No image assigned: {recipe.name}")
        missing += 1
        continue

    old_name = recipe.image.name

    # Наприклад: recipes/photo_123.jpeg
    old_id = os.path.splitext(old_name)[0]

    # Cloudinary використовує media/recipes/
    if not old_id.startswith("media/"):
        old_id = "media/" + old_id

    matches = [
        resource
        for resource in resources
        if resource["public_id"] == old_id
        or resource["public_id"].startswith(old_id + "_")
    ]

    if len(matches) == 1:

        resource = matches[0]
        new_id = resource["public_id"]

        # Зберігаємо шлях у форматі Django ImageField
        extension = os.path.splitext(old_name)[1]

        if not extension:
            extension = "." + resource.get("format", "jpg")

        new_name = new_id.removeprefix("media/") + extension

        if new_name == old_name:
            print(f"Already correct: {recipe.name}")
            unchanged += 1
            continue

        print(
            f"{recipe.name}: "
            f"{old_name} -> {new_name}"
        )

        if not DRY_RUN:
            with transaction.atomic():
                recipe.image.name = new_name
                recipe.save(update_fields=["image"])

        updated += 1

    elif len(matches) > 1:

        print(f"Multiple matches for {recipe.name}:")

        for resource in matches:
            print(f"  - {resource['public_id']}")

        multiple += 1

    else:
        print(f"No match for {recipe.name}")
        missing += 1


print("\n========== SUMMARY ==========")
print(f"Total recipes: {len(recipes)}")
print(f"{'Would update' if DRY_RUN else 'Updated'}: {updated}")
print(f"Already correct: {unchanged}")
print(f"Missing images: {missing}")
print(f"Multiple matches: {multiple}")

if DRY_RUN:
    print("\nDRY RUN: No database changes made.")
else:
    print("\nDatabase update completed.")
