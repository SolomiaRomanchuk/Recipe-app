from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.views.generic import (
    TemplateView,
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from .models import Recipe, Category, Ingredient, Favorite, Profile
from .forms import SignUpForm, RecipeFilterForm, AvatarForm
from django.contrib.auth.views import PasswordChangeView


# OLD FUNCTION-BASED VIEWS
# Kept here for comparison according to the homework.

# def recipe_list(request):
#     recipes = Recipe.objects.all()
#     return render(
#         request,
#         'recipes/recipe_list.html',
#         {'recipes': recipes}
#     )


# def recipe_detail(request, pk):
#     recipe = get_object_or_404(Recipe, pk=pk)
#     return render(
#         request,
#         'recipes/recipe_detail.html',
#         {'recipe': recipe}
#     )


# def category_list(request):
#     categories = Category.objects.all()
#     return render(
#         request,
#         'recipes/category_list.html',
#         {'categories': categories}
#     )


# def ingredient_list(request):
#     ingredients = Ingredient.objects.all()
#     return render(
#         request,
#         'recipes/ingredient_list.html',
#         {'ingredients': ingredients}
#     )


# =========================
# SIGN UP
# =========================

class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('recipe_list')

    def form_valid(self, form):
        response = super().form_valid(form)

        login(self.request, self.object)

        messages.success(
            self.request,
            'Your account has been created successfully!'
        )

        return response


class RecipePasswordChangeView(PasswordChangeView):
    template_name = 'registration/password_change_form.html'
    success_url = reverse_lazy('password_change_done')


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'recipes/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('avatar_form', AvatarForm())
        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'remove_avatar':
            profile = Profile.objects.filter(user=request.user).first()
            if profile:
                profile.avatar.delete(save=True)
            return redirect('profile')

        form = AvatarForm(request.POST, request.FILES)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(avatar_form=form))

        profile, _ = Profile.objects.get_or_create(user=request.user)
        old_name = profile.avatar.name
        storage = profile.avatar.storage
        profile.avatar = form.cleaned_data['avatar']
        profile.save(update_fields=['avatar'])
        if old_name and old_name != profile.avatar.name:
            storage.delete(old_name)
        return redirect('profile')


class SurpriseRecipeView(TemplateView):
    template_name = 'recipes/surprise.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipes = Recipe.objects.select_related('category')
        context['has_recipes'] = recipes.exists()
        if self.request.GET.get('pick') != '1' or not context['has_recipes']:
            return context

        previous = self.request.GET.get('previous', '')
        if previous.isascii() and previous.isdigit() and len(previous) <= 18:
            alternatives = recipes.exclude(pk=int(previous))
            if alternatives.exists():
                recipes = alternatives
        recipe = recipes.order_by('?').first()
        if recipe is None:
            context['has_recipes'] = False
            return context
        context['selected_recipe'] = recipe
        context['recipes'] = [recipe]
        context['favorite_recipe_ids'] = set(
            Favorite.objects.filter(user=self.request.user).values_list('recipe_id', flat=True)
        ) if self.request.user.is_authenticated else set()
        context['shuffle_recipes'] = [
            {'name': item.name, 'image': item.image.url if item.image else ''}
            for item in Recipe.objects.order_by('?')[:12]
        ]
        return context


# =========================
# FAVORITES
# =========================

@login_required
def toggle_favorite(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)

    favorite = Favorite.objects.filter(
        user=request.user,
        recipe=recipe
    ).first()

    if favorite:
        favorite.delete()
    else:
        Favorite.objects.create(
            user=request.user,
            recipe=recipe
        )

    return redirect(
        request.META.get(
            'HTTP_REFERER',
            'recipe_list'
        )
    )


class FavoriteRecipesView(LoginRequiredMixin, ListView):
    model = Recipe
    template_name = 'recipes/recipe_list.html'
    context_object_name = 'recipes'
    paginate_by = 6

    def get_queryset(self):
        return Recipe.objects.filter(
            favorited_by__user=self.request.user
        ).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['page_title'] = 'Favorite Recipes'

        context['favorite_recipe_ids'] = set(
            Favorite.objects.filter(
                user=self.request.user
            ).values_list(
                'recipe_id',
                flat=True
            )
        )

        context['show_recipe_hero'] = False
        context['show_back_to_recipes'] = True

        return context

# =========================
# RECIPE LIST
# =========================

class RecipeListView(ListView):
    model = Recipe
    template_name = 'recipes/recipe_list.html'
    context_object_name = 'recipes'
    ordering = ['name']
    paginate_by = 6
    extra_context = {
        'page_title': 'Latest Recipes'
    }

    def get_queryset(self):
        queryset = Recipe.objects.all()

        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        category_id = self.request.GET.get('category')

        if category_id:
            queryset = queryset.filter(
                category_id=category_id
            )

        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        category_id = self.request.GET.get('category')

        if category_id:
            category = Category.objects.filter(
                id=category_id
            ).first()

            if category:
                context['page_title'] = category.name
                context['selected_category'] = category

        if self.request.user.is_authenticated:
            context['favorite_recipe_ids'] = set(
                Favorite.objects.filter(
                    user=self.request.user
                ).values_list(
                    'recipe_id',
                    flat=True
                )
            )
        else:
            context['favorite_recipe_ids'] = set()

        search_query = self.request.GET.get('search', '').strip()
        context['search_query'] = search_query
        if search_query:
            context['page_title'] = f'Search results for “{search_query}”'
        context['show_recipe_hero'] = not search_query

        return context


# =========================
# RECIPE FILTERS
# =========================

class RecipeFilterView(ListView):
    model = Recipe
    template_name = 'recipes/recipe_filter.html'
    context_object_name = 'recipes'

    def get_queryset(self):
        submitted = any(
            key in self.request.GET for key in ('category', 'difficulty', 'time')
        )
        self.filter_form = RecipeFilterForm(self.request.GET if submitted else None)
        if not self.filter_form.is_valid():
            return Recipe.objects.none()

        filters = self.filter_form.cleaned_data
        queryset = Recipe.objects.select_related('category')
        if filters['category']:
            queryset = queryset.filter(category=filters['category'])
        if filters['difficulty']:
            queryset = queryset.filter(difficulty=filters['difficulty'])
        if filters['time'] == 'over60':
            queryset = queryset.filter(cooking_time__gt=60)
        elif filters['time']:
            queryset = queryset.filter(cooking_time__lte=int(filters['time']))
        return queryset.order_by('name', 'pk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.filter_form
        context['show_results'] = self.filter_form.is_valid()
        context['favorite_recipe_ids'] = set(
            Favorite.objects.filter(user=self.request.user).values_list('recipe_id', flat=True)
        ) if self.request.user.is_authenticated else set()
        return context


# =========================
# MY RECIPES
# =========================

class MyRecipesView(LoginRequiredMixin, ListView):
    model = Recipe
    template_name = 'recipes/recipe_list.html'
    context_object_name = 'recipes'
    paginate_by = 6

    def get_queryset(self):
        return Recipe.objects.filter(
            owner=self.request.user
        ).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['page_title'] = 'My Recipes'

        context['favorite_recipe_ids'] = set(
            Favorite.objects.filter(
                user=self.request.user
            ).values_list(
                'recipe_id',
                flat=True
            )
        )

        context['show_recipe_hero'] = False
        context['show_back_to_recipes'] = True

        return context

# =========================
# DETAIL VIEW
# =========================

class RecipeDetailView(DetailView):
    model = Recipe
    template_name = 'recipes/recipe_detail.html'
    context_object_name = 'recipe'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['related_recipes'] = Recipe.objects.filter(
            category=self.object.category
        ).exclude(
            pk=self.object.pk
        )

        back_from = self.request.GET.get('from')
        category_id = self.request.GET.get('category')

        if back_from == 'category' and category_id:
            category = Category.objects.filter(
                id=category_id
            ).first()

            if category:
                context['back_url'] = (
                    f'/recipes/?category={category.id}'
                )
                context['back_text'] = (
                    f'← Back to {category.name}'
                )

        elif back_from == 'quick':
            context['back_url'] = '/recipes/quick/'
            context['back_text'] = '← Back to Quick Recipes'

        else:
            context['back_url'] = '/recipes/'
            context['back_text'] = '← Back to Recipes'

        return context


# =========================
# CATEGORIES
# =========================

class CategoryListView(ListView):
    model = Category
    template_name = 'recipes/category_list.html'
    context_object_name = 'categories'
    ordering = ['name']
    paginate_by = 6

class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    fields = ['name', 'emoji']
    template_name = 'recipes/category_form.html'
    success_url = reverse_lazy('category_list')

    def form_valid(self, form):
        response = super().form_valid(form)

        messages.success(
            self.request,
            'Category added successfully!'
        )

        return response

class CategoryDeleteView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DeleteView
):
    model = Category
    template_name = 'recipes/category_confirm_delete.html'
    success_url = reverse_lazy('category_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(
            self.request,
            'Category deleted successfully!'
        )

        return super().form_valid(form)

# =========================
# INGREDIENTS
# =========================

class IngredientListView(ListView):
    model = Ingredient
    template_name = 'recipes/ingredient_list.html'
    context_object_name = 'ingredients'
    ordering = ['name']


# =========================
# QUICK RECIPES
# =========================

class QuickRecipeListView(ListView):
    model = Recipe
    template_name = 'recipes/recipe_list.html'
    context_object_name = 'recipes'
    ordering = ['cooking_time']
    extra_context = {
        'page_title': 'Quick Recipes'
    }

    def get_queryset(self):
        return Recipe.objects.filter(
            cooking_time__lte=30
        ).order_by('cooking_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            context['favorite_recipe_ids'] = set(
                Favorite.objects.filter(
                    user=self.request.user
                ).values_list(
                    'recipe_id',
                    flat=True
                )
            )
        else:
            context['favorite_recipe_ids'] = set()

        context['show_recipe_hero'] = False
        context['show_back_to_recipes'] = True

        return context


# =========================
# DIFFICULTY
# =========================

class DifficultyListView(ListView):
    model = Recipe
    template_name = 'recipes/difficulty_list.html'
    context_object_name = 'recipes'


class DifficultyRecipeListView(ListView):
    model = Recipe
    template_name = 'recipes/recipe_list.html'
    context_object_name = 'recipes'
    paginate_by = 6

    def get_queryset(self):
        difficulty = self.kwargs['difficulty']

        return Recipe.objects.filter(
            difficulty=difficulty
        ).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        difficulty = self.kwargs['difficulty']

        difficulty_names = {
            'easy': 'Easy',
            'medium': 'Medium',
            'hard': 'Hard',
        }

        context['page_title'] = (
            f'{difficulty_names.get(difficulty, "Difficulty")} Recipes'
        )

        if self.request.user.is_authenticated:
            context['favorite_recipe_ids'] = set(
                Favorite.objects.filter(
                    user=self.request.user
                ).values_list(
                    'recipe_id',
                    flat=True
                )
            )
        else:
            context['favorite_recipe_ids'] = set()

        context['show_recipe_hero'] = False
        context['selected_difficulty'] = difficulty
        context['show_back_to_difficulty'] = True

        return context



# =========================
# CREATE RECIPE
# =========================

class RecipeCreateView(LoginRequiredMixin, CreateView):
    model = Recipe

    fields = [
        'name',
        'category',
        'ingredients',
        'cooking_time',
        'difficulty',
        'description',
        'image',
    ]

    template_name = 'recipes/recipe_form.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user

        response = super().form_valid(form)

        messages.success(
            self.request,
            'Recipe created successfully!'
        )

        return response


# =========================
# UPDATE RECIPE
# =========================

class RecipeUpdateView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    UpdateView
):
    model = Recipe

    fields = [
        'name',
        'category',
        'ingredients',
        'cooking_time',
        'difficulty',
        'description',
        'image',
    ]

    template_name = 'recipes/recipe_form.html'

    def test_func(self):
        recipe = self.get_object()

        return (
            recipe.owner == self.request.user
            or self.request.user.is_staff
        )

    def form_valid(self, form):
        response = super().form_valid(form)

        messages.success(
            self.request,
            'Recipe updated successfully!'
        )

        return response


# =========================
# DELETE RECIPE
# =========================

class RecipeDeleteView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DeleteView
):
    model = Recipe
    template_name = 'recipes/recipe_confirm_delete.html'
    success_url = reverse_lazy('recipe_list')

    def test_func(self):
        recipe = self.get_object()

        return (
            recipe.owner == self.request.user
            or self.request.user.is_staff
        )

    def form_valid(self, form):
        messages.success(
            self.request,
            'Recipe deleted successfully!'
        )

        return super().form_valid(form)


# =========================
# CREATE INGREDIENT
# =========================

class IngredientCreateView(LoginRequiredMixin, CreateView):
    model = Ingredient
    fields = ['name', 'emoji']
    template_name = 'recipes/ingredient_form.html'
    success_url = reverse_lazy('ingredients_list')

    def form_valid(self, form):
        response = super().form_valid(form)

        messages.success(
            self.request,
            'Ingredient added successfully!'
        )

        return response


# =========================
# DELETE INGREDIENT
# =========================

class IngredientDeleteView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DeleteView
):
    model = Ingredient
    template_name = 'recipes/ingredient_confirm_delete.html'
    success_url = reverse_lazy('ingredients_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(
            self.request,
            'Ingredient deleted successfully!'
        )

        return super().form_valid(form)
