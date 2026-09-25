from django.contrib import admin
from .models import Category, Ingredient, Recipe, Favorite


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'category',
        'difficulty',
        'cooking_time',
        'created_at',
    )

    list_filter = ('difficulty', 'category')
    search_fields = ('name',)
    filter_horizontal = ('ingredients',)


admin.site.register(Favorite)