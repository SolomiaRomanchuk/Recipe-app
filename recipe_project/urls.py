from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from recipes import views


urlpatterns = [
    path('admin/', admin.site.urls),

    path('profile/', views.ProfileView.as_view(), name='profile'),


    path(
        'accounts/password_change/',
         views.RecipePasswordChangeView.as_view(),
         name='password_change'
    ),

    path(
        'accounts/',
        include('django.contrib.auth.urls')
    ),

    path(
        'accounts/signup/',
        views.SignUpView.as_view(),
        name='signup'
    ),

    # Recipe list
    path(
        'recipes/',
        views.RecipeListView.as_view(),
        name='recipe_list'
    ),

    path(
        'recipes/filter/',
        views.RecipeFilterView.as_view(),
        name='recipe_filter'
    ),

    # Surprise Me
    path('recipes/surprise/', views.SurpriseRecipeView.as_view(), name='surprise_recipe'),

    # Quick recipes
    path(
        'recipes/quick/',
        views.QuickRecipeListView.as_view(),
        name='quick_recipe_list'
    ),

    # Difficulty
    path(
         'recipes/difficulty/',
         views.DifficultyListView.as_view(),
         name='difficulty_list'
     ),

    path(
         'recipes/difficulty/<str:difficulty>/',
         views.DifficultyRecipeListView.as_view(),
         name='difficulty_recipes'
    ),

    # Create recipe
    path(
        'recipes/new/',
        views.RecipeCreateView.as_view(),
        name='recipe_create'
    ),

    # Update recipe
    path(
        'recipes/<int:pk>/edit/',
        views.RecipeUpdateView.as_view(),
        name='recipe_update'
    ),

    # Delete recipe
    path(
        'recipes/<int:pk>/delete/',
        views.RecipeDeleteView.as_view(),
        name='recipe_delete'
    ),

    path(
       'recipes/my/',
        views.MyRecipesView.as_view(),
        name='my_recipes'
     ),

    path(
        'recipes/favorites/',
        views.FavoriteRecipesView.as_view(),
        name='favorite_recipes'
    ),

    # Recipe detail
    path(
        'recipes/<int:pk>/',
        views.RecipeDetailView.as_view(),
        name='recipe_detail'
    ),

    path(
       'recipes/<int:pk>/favorite/',
        views.toggle_favorite,
        name='toggle_favorite'
    ),

    # Categories
    path(
       'categories/',
        views.CategoryListView.as_view(),
        name='category_list'
    ),

    path(
       'categories/new/',
        views.CategoryCreateView.as_view(),
        name='category_create'
    ),

    path(
       'categories/<int:pk>/delete/',
        views.CategoryDeleteView.as_view(),
         name='category_delete'
   ),

    # Ingredients
    path(
        'ingredients/',
        views.IngredientListView.as_view(),
        name='ingredients_list'
    ),

    # Add ingredient
    path(
        'ingredients/new/',
         views.IngredientCreateView.as_view(),
         name='ingredient_create'
    ),

    # Delete ingredient
    path(
        'ingredients/<int:pk>/delete/',
        views.IngredientDeleteView.as_view(),
        name='ingredient_delete'
    ),

]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)
