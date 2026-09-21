from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy
from .models import Recipe, Category, Ingredient
from .forms import SignUpForm

# OLD FUNCTION-BASED VIEWS
# Kept here for comparison according to the homework.
#def recipe_list(request):
   # recipes = Recipe.objects.all()

   # return render(
      #  request,
       # 'recipes/recipe_list.html',
        #{'recipes': recipes}
   # )
#def recipe_detail(request, pk):
    #recipe = get_object_or_404(Recipe, pk=pk)

   # return render(
      #  request,
       # 'recipes/recipe_detail.html',
        #{'recipe': recipe}
    #)
#def category_list(request):
    #categories = Category.objects.all()

    #return render(
       # request,
        #'recipes/category_list.html',
       # {'categories': categories}
    #)
#def ingredient_list(request):
    #ingredients = Ingredient.objects.all()
    #return render(
       # request,
       # 'recipes/ingredient_list.html',
     #   {'ingredients': ingredients }
    #)

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

# LIST VIEW
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

        category_id = self.request.GET.get('category')

        if category_id:
            queryset = queryset.filter(category_id=category_id)

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

        return context

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

        return context

# DETAIL VIEW
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

class CategoryListView(ListView):
    model = Category
    template_name = 'recipes/category_list.html'
    context_object_name = 'categories'
    ordering = ['name']


class IngredientListView(ListView):
    model = Ingredient
    template_name = 'recipes/ingredient_list.html'
    context_object_name = 'ingredients'
    ordering = ['name']

# FILTERED LIST VIEW
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


# CREATE VIEW
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

# UPDATE VIEW
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

# DELETE VIEW
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
