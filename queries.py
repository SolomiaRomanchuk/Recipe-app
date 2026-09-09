import os
import django

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'recipe_project.settings'
)

django.setup()

from recipes.models import Category, Ingredient, Recipe
from django.db.models import Count, Avg, Min, Max, Sum


# 1. Усі рецепти
print('1:', Recipe.objects.all())


# 2. Рецепти з часом приготування більше 30 хвилин
print('2:', Recipe.objects.filter(cooking_time__gt=30))


# 3. Рецепти певної категорії
print('3:', Recipe.objects.filter(category__name='Сніданки'))


# 4. Рецепти певної складності
print('4:', Recipe.objects.filter(difficulty='easy'))


# 5. Топ-3 рецепти за найменшим часом приготування
print(
    '5:',
    Recipe.objects.order_by('cooking_time')[:3]
)


# 6. Кількість рецептів у кожній категорії
print(
    '6:',
    Category.objects.annotate(
        recipe_count=Count('recipes')
    )
)


# 7. Рецепти та їх SQL
query = Recipe.objects.filter(
    ingredients__name='Яйце'
)

print('7:', query)
print(query.query)