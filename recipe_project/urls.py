from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from recipes import views


urlpatterns = [
    path('admin/', admin.site.urls),
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

    # Quick recipes
    path(
        'recipes/quick/',
        views.QuickRecipeListView.as_view(),
        name='quick_recipe_list'
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

    # Recipe detail
    path(
        'recipes/<int:pk>/',
        views.RecipeDetailView.as_view(),
        name='recipe_detail'
    ),

    # Categories
    path(
       'categories/',
        views.CategoryListView.as_view(),
        name='category_list'
    ),

    # Ingredients
    path(
        'ingredients/',
        views.IngredientListView.as_view(),
        name='ingredients_list'
    ),
]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)

