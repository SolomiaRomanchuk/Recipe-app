from django.test import TestCase
from django.urls import reverse

from .models import Category, Ingredient, Recipe


class AuthenticationTests(TestCase):
    password = 'Saffron!River-73-Cook'

    def signup_data(self, **overrides):
        return {
            'username': 'new-cook',
            'password1': self.password,
            'password2': self.password,
            **overrides,
        }

    def test_signup_route_template_and_fields(self):
        from django.urls import resolve
        from .forms import SignUpForm
        from .views import SignUpView

        self.assertIs(resolve('/accounts/signup/').func.view_class, SignUpView)
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/signup.html')
        self.assertIsInstance(response.context['form'], SignUpForm)
        self.assertEqual(list(response.context['form'].fields), ['username', 'password1', 'password2'])
        for name in ['username', 'password1', 'password2']:
            self.assertContains(response, f'name="{name}"')
            self.assertContains(response, f'for="id_{name}"')
        self.assertNotContains(response, 'name="email"')
        for text in ['Username', 'Password', 'Confirm Password', 'Create Account', 'Already have an account?', 'Log In']:
            self.assertContains(response, text)

    def test_invalid_signup_shows_validation_errors(self):
        from django.contrib.auth.models import User
        from django.utils.html import escape

        User.objects.create_user(username='existing-cook', password=self.password)
        for data in [
            {},
            self.signup_data(username='invalid name!'),
            self.signup_data(username='existing-cook'),
            self.signup_data(password2='Different!Password-73'),
            self.signup_data(password1='123', password2='123'),
        ]:
            with self.subTest(data_fields=list(data)):
                response = self.client.post(reverse('signup'), data)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['form'].errors)
                for errors in response.context['form'].errors.values():
                    for error in errors:
                        self.assertContains(response, escape(error))
                self.assertEqual(User.objects.count(), 1)
                self.assertNotIn('_auth_user_id', self.client.session)

    def test_signup_logout_and_login_with_csrf(self):
        from django.contrib.auth.models import User
        from django.test import Client
        from .models import Favorite

        self.client = Client(enforce_csrf_checks=True)
        self.client.get(reverse('signup'))
        response = self.client.post(reverse('signup'), {
            **self.signup_data(),
            'csrfmiddlewaretoken': self.client.cookies['csrftoken'].value,
        })
        self.assertRedirects(response, reverse('recipe_list'))
        user = User.objects.get(username='new-cook')
        self.assertEqual(user.email, '')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertNotEqual(user.password, self.password)
        self.assertTrue(user.check_password(self.password))
        self.assertEqual(self.client.session['_auth_user_id'], str(user.pk))
        self.assertRedirects(
            self.client.get(reverse('admin:index')),
            reverse('admin:login') + '?next=' + reverse('admin:index'),
        )
        for route in ['profile', 'my_recipes', 'favorite_recipes', 'recipe_create', 'password_change']:
            self.assertEqual(self.client.get(reverse(route)).status_code, 200)
        category = Category.objects.create(name='Dinner')
        recipe = Recipe.objects.create(name='Soup', category=category, cooking_time=20, owner=user)
        response = self.client.post(reverse('toggle_favorite', args=[recipe.pk]), {
            'csrfmiddlewaretoken': self.client.cookies['csrftoken'].value,
        })
        self.assertRedirects(response, reverse('recipe_list'))
        self.assertTrue(Favorite.objects.filter(user=user, recipe=recipe).exists())
        self.assertContains(self.client.get(reverse('my_recipes')), 'Soup')
        self.assertEqual(self.client.get(reverse('recipe_update', args=[recipe.pk])).status_code, 200)
        response = self.client.post(reverse('logout'), {
            'csrfmiddlewaretoken': self.client.cookies['csrftoken'].value,
        })
        self.assertRedirects(response, reverse('recipe_list'))
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(self.client.get(reverse('profile')).status_code, 302)
        self.client.get(reverse('login'))
        response = self.client.post(reverse('login'), {
            'username': user.username, 'password': 'wrong-password',
            'csrfmiddlewaretoken': self.client.cookies['csrftoken'].value,
        })
        self.assertContains(response, 'Please enter a correct username and password.')
        self.assertNotIn('_auth_user_id', self.client.session)
        response = self.client.post(reverse('login'), {
            'username': user.username, 'password': self.password,
            'csrfmiddlewaretoken': self.client.cookies['csrftoken'].value,
        })
        self.assertRedirects(response, reverse('recipe_list'))
        self.assertEqual(self.client.session['_auth_user_id'], str(user.pk))


class AdminAuthenticationTests(TestCase):
    def test_superuser_can_log_in_on_site_and_admin(self):
        from django.contrib.auth.models import User
        from secrets import token_urlsafe

        password = token_urlsafe(32)
        user = User.objects.create_superuser(username='admin-test', password=password)
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        response = self.client.post(reverse('login'), {
            'username': user.username, 'password': password,
        })
        self.assertRedirects(response, reverse('recipe_list'))
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 200)
        self.client.logout()
        response = self.client.post(reverse('admin:login'), {
            'username': user.username, 'password': password,
            'next': reverse('admin:index'),
        })
        self.assertRedirects(response, reverse('admin:index'))
        self.assertEqual(self.client.session['_auth_user_id'], str(user.pk))

    def test_normal_user_cannot_log_in_at_admin(self):
        from django.contrib.auth.models import User
        from secrets import token_urlsafe

        password = token_urlsafe(32)
        user = User.objects.create_user(username='normal-test', password=password)
        response = self.client.post(reverse('admin:login'), {
            'username': user.username, 'password': password,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertNotIn('_auth_user_id', self.client.session)


class RecipeSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='Desserts')
        cls.brownie = Recipe.objects.create(
            name='Chocolate Brownie', category=cls.category, cooking_time=30,
        )
        cls.salad = Recipe.objects.create(
            name='Caesar Salad', category=cls.category, cooking_time=15,
            description='Serve with pasta',
        )
        cls.salad.ingredients.add(Ingredient.objects.create(name='Garlic'))

    def search(self, query, **params):
        return self.client.get(reverse('recipe_list'), {'search': query, **params})

    def test_case_insensitive_partial_name_and_preserved_query(self):
        response = self.search('  bRoWn  ')
        self.assertQuerySetEqual(response.context['recipes'], [self.brownie])
        self.assertContains(response, 'value="bRoWn"')
        self.assertContains(response, 'class="recipe-card"')
        self.assertNotContains(response, 'class="hero"')

    def test_other_fields_do_not_match(self):
        for query in ['Garlic', 'Desserts', 'pasta', 'easy', 'nonexistent']:
            with self.subTest(query=query):
                response = self.search(query)
                self.assertQuerySetEqual(response.context['recipes'], [])
                self.assertContains(response, 'No recipes found')
                self.assertContains(response, 'Try searching for another recipe name.')

    def test_blank_search_keeps_regular_list(self):
        response = self.search('   ')
        self.assertEqual(response.context['paginator'].count, 2)
        self.assertTrue(response.context['show_recipe_hero'])

    def test_query_survives_pagination(self):
        for number in range(7):
            Recipe.objects.create(
                name=f'Pasta & Beans {number}', category=self.category, cooking_time=20,
            )
        response = self.search('Pasta & Beans')
        self.assertContains(response, '?page=2&amp;search=Pasta%20%26%20Beans')
        response = self.search('Pasta & Beans', page=2)
        self.assertEqual(len(response.context['recipes']), 1)
        self.assertEqual(response.context['paginator'].count, 7)
        self.assertContains(response, 'value="Pasta &amp; Beans"')

    def test_search_respects_existing_category_filter(self):
        other = Category.objects.create(name='Other')
        response = self.search('brownie', category=other.pk)
        self.assertQuerySetEqual(response.context['recipes'], [])
        response = self.search('brownie', category=self.category.pk)
        self.assertQuerySetEqual(response.context['recipes'], [self.brownie])

    def test_query_is_html_escaped(self):
        response = self.search('\"><script>alert(1)</script>')
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;')


class RecipeFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.desserts = Category.objects.create(name='Desserts')
        cls.mains = Category.objects.create(name='Mains')
        cls.recipes = []
        for name, category, difficulty, minutes in [
            ('Quick Sweet', cls.desserts, 'easy', 15),
            ('Brownie', cls.desserts, 'easy', 30),
            ('Cake', cls.desserts, 'medium', 60),
            ('Pie', cls.desserts, 'hard', 61),
            ('Pasta', cls.mains, 'easy', 16),
            ('Roast', cls.mains, 'hard', 90),
            ('Soup', cls.mains, 'medium', 31),
        ]:
            cls.recipes.append(Recipe.objects.create(
                name=name, category=category, difficulty=difficulty, cooking_time=minutes,
            ))

    def filtered(self, **params):
        return self.client.get(reverse('recipe_filter'), params)

    def names(self, response):
        return {recipe.name for recipe in response.context['recipes']}

    def test_initial_page_and_all_any_submission(self):
        response = self.filtered()
        self.assertContains(response, 'Find Your Perfect Recipe')
        self.assertContains(response, '← Back to Recipes')
        self.assertFalse(response.context['show_results'])
        response = self.filtered(category='', difficulty='', time='')
        self.assertEqual(len(response.context['recipes']), 7)
        self.assertContains(response, 'Recipes That Match Your Preferences')
        self.assertContains(response, 'class="recipe-card"', count=7)

    def test_individual_filters(self):
        self.assertEqual(self.names(self.filtered(difficulty='easy')), {'Quick Sweet', 'Brownie', 'Pasta'})
        self.assertEqual(self.names(self.filtered(category=self.mains.pk)), {'Pasta', 'Roast', 'Soup'})

    def test_combined_filters_and_preserved_values(self):
        response = self.filtered(category=self.desserts.pk, difficulty='easy', time='30')
        self.assertEqual(self.names(response), {'Quick Sweet', 'Brownie'})
        for value in [str(self.desserts.pk), 'easy', '30']:
            self.assertContains(response, f'value="{value}" selected')

    def test_time_boundaries(self):
        for value, expected in [
            ('15', {'Quick Sweet'}),
            ('30', {'Quick Sweet', 'Brownie', 'Pasta'}),
            ('60', {'Quick Sweet', 'Brownie', 'Pasta', 'Cake', 'Soup'}),
            ('over60', {'Pie', 'Roast'}),
        ]:
            with self.subTest(time=value):
                self.assertEqual(self.names(self.filtered(time=value)), expected)

    def test_no_matches_and_reset(self):
        response = self.filtered(category=self.mains.pk, difficulty='hard', time='15')
        self.assertContains(response, 'No matching recipes')
        self.assertContains(response, 'Reset Filters')
        self.assertContains(response, '← Back to Recipes')
        self.assertFalse(self.filtered().context['filter_form'].is_bound)

    def test_invalid_filters_show_errors(self):
        for params in [{'category': 'invalid'}, {'category': '999999'}, {'difficulty': 'invalid'}, {'time': 'invalid'}]:
            with self.subTest(params=params):
                response = self.filtered(**params)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['filter_form'].errors)
                self.assertFalse(response.context['show_results'])

    def test_favorites_and_existing_pages(self):
        from django.contrib.auth.models import User
        from .models import Favorite
        user = User.objects.create_user(username='filter-user', password='test-password')
        self.client.force_login(user)
        Favorite.objects.create(user=user, recipe=self.recipes[0])
        response = self.filtered(difficulty='easy')
        self.assertContains(response, 'favorite-button is-favorite')
        self.assertContains(response, reverse('toggle_favorite', args=[self.recipes[0].pk]))
        for name, args in [
            ('recipe_list', []), ('category_list', []), ('ingredients_list', []),
            ('difficulty_list', []), ('difficulty_recipes', ['easy']),
            ('quick_recipe_list', []), ('favorite_recipes', []), ('my_recipes', []),
        ]:
            with self.subTest(page=name):
                response = self.client.get(reverse(name, args=args))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, reverse('recipe_filter'))

    def test_shared_cards_match_regular_list(self):
        import re
        normal = self.client.get(reverse('recipe_list')).content.decode()
        filtered = self.filtered(category='', difficulty='', time='').content.decode()
        cards = lambda html: re.findall(r'<article class="recipe-card">.*?</article>', html, re.S)
        self.assertEqual(cards(normal), cards(filtered)[:6])


class ProfileTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth.models import User
        cls.user = User.objects.create_user(username='profile-user', password='test-password')
        other = User.objects.create_user(username='other-user')
        category = Category.objects.create(name='Mains')
        for owner in [cls.user, cls.user, other]:
            Recipe.objects.create(name='Soup', owner=owner, category=category, cooking_time=15)

    def test_profile_requires_login(self):
        self.assertRedirects(
            self.client.get(reverse('profile')),
            reverse('login') + '?next=' + reverse('profile'),
        )

    def test_profile_and_menu_navigation(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('profile'))
        self.assertContains(response, 'Hello, profile-user!')
        self.assertContains(response, '2 recipes created')
        html = response.content.decode()
        menu = html.split('<nav class="side-menu-links">')[1].split('</nav>')[0]
        main = html.split('<main class="main-content">')[1].split('</main>')[0]
        for name in ['recipe_list', 'category_list', 'ingredients_list', 'recipe_filter', 'favorite_recipes', 'profile']:
            self.assertIn(f'href="{reverse(name)}"', menu)
        self.assertIn('profile-user', menu)
        self.assertIn('2 recipes', menu)
        for name in ['my_recipes', 'quick_recipe_list', 'difficulty_list', 'password_change', 'logout']:
            self.assertNotIn(reverse(name), menu)
            self.assertIn(reverse(name), main)
        self.assertNotIn(reverse('favorite_recipes'), main)
        for name in ['my_recipes', 'quick_recipe_list', 'difficulty_list', 'password_change']:
            with self.subTest(page=name):
                linked = self.client.get(reverse(name))
                self.assertEqual(linked.status_code, 200)
                if name == 'password_change':
                    self.assertTemplateUsed(linked, 'registration/password_change_form.html')

    def test_guest_menu_keeps_authentication_links(self):
        response = self.client.get(reverse('recipe_list'))
        self.assertContains(response, reverse('login'))
        self.assertContains(response, reverse('signup'))
        self.assertNotContains(response, 'class="menu-user-info menu-profile"')

    def test_logout_requires_post_and_csrf(self):
        import re
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.get(reverse('profile'))
        token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.content.decode()).group(1)
        self.assertEqual(client.get(reverse('logout')).status_code, 405)
        self.assertEqual(client.post(reverse('logout')).status_code, 403)
        self.assertIn('_auth_user_id', client.session)
        response = client.post(reverse('logout'), {'csrfmiddlewaretoken': token})
        self.assertRedirects(response, reverse('recipe_list'))
        self.assertNotIn('_auth_user_id', client.session)


class AvatarTests(TestCase):
    def setUp(self):
        import tempfile
        from django.test import override_settings
        from django.contrib.auth.models import User
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        override = override_settings(MEDIA_ROOT=self.media.name)
        override.enable()
        self.addCleanup(override.disable)
        self.user = User.objects.create_user(username='avatar-user')
        self.client.force_login(self.user)

    def image(self):
        from io import BytesIO
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        data = BytesIO()
        Image.new('RGB', (20, 30), 'orange').save(data, format='PNG')
        return SimpleUploadedFile('photo.png', data.getvalue(), content_type='image/png')

    def test_upload_replace_remove_and_fallback(self):
        from .models import Profile
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'class="profile-avatar-photo"')
        self.assertFalse(Profile.objects.filter(user=self.user).exists())
        self.client.post(reverse('profile'), {'avatar': self.image()})
        profile = Profile.objects.get(user=self.user)
        first_name = profile.avatar.name
        self.assertTrue(profile.avatar.storage.exists(first_name))
        response = self.client.get(reverse('profile'))
        self.assertContains(response, profile.avatar.url, count=2)
        self.assertContains(response, 'avatar-user • 0 recipes')
        self.client.post(reverse('profile'), {'avatar': self.image()})
        profile.refresh_from_db()
        self.assertNotEqual(profile.avatar.name, first_name)
        self.assertFalse(profile.avatar.storage.exists(first_name))
        # A missing file safely restores the default icon in both locations.
        profile.avatar.storage.delete(profile.avatar.name)
        self.assertEqual(profile.avatar_url, '')
        self.assertNotContains(self.client.get(reverse('profile')), 'class="profile-avatar-photo"')
        self.client.post(reverse('profile'), {'action': 'remove_avatar'})
        profile.refresh_from_db()
        self.assertFalse(profile.avatar)
        self.client.post(reverse('profile'), {'avatar': self.image()})
        profile.refresh_from_db()
        name = profile.avatar.name
        self.client.post(reverse('profile'), {'action': 'remove_avatar'})
        self.assertFalse(profile.avatar.storage.exists(name))

    def test_invalid_and_oversized_uploads_preserve_photo(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .models import Profile
        self.client.post(reverse('profile'), {'avatar': self.image()})
        original = Profile.objects.get(user=self.user).avatar.name
        oversized = self.image().read() + b' ' * (5 * 1024 * 1024)
        for upload in [
            SimpleUploadedFile('fake.png', b'not an image', content_type='image/png'),
            SimpleUploadedFile('large.png', oversized, content_type='image/png'),
            SimpleUploadedFile('avatar.svg', b'<svg></svg>', content_type='image/svg+xml'),
        ]:
            response = self.client.post(reverse('profile'), {'avatar': upload})
            self.assertTrue(response.context['avatar_form'].errors)
            self.assertEqual(Profile.objects.get(user=self.user).avatar.name, original)

    def test_avatar_changes_are_authenticated_and_csrf_protected(self):
        from django.test import Client
        from .models import Profile
        self.client.logout()
        response = self.client.post(reverse('profile'), {'avatar': self.image()})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Profile.objects.exists())
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(reverse('profile'), {'avatar': self.image()}).status_code, 403)
        self.assertEqual(client.post(reverse('profile'), {'action': 'remove_avatar'}).status_code, 403)

    def test_upload_only_updates_current_user(self):
        from django.contrib.auth.models import User
        from .models import Profile
        other = User.objects.create_user(username='other-avatar-user')
        self.client.post(reverse('profile'), {'user': other.pk, 'avatar': self.image()})
        self.assertTrue(Profile.objects.filter(user=self.user).exists())
        self.assertFalse(Profile.objects.filter(user=other).exists())


class SurpriseRecipeTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Desserts')

    def recipe(self, name):
        return Recipe.objects.create(name=name, category=self.category, cooking_time=25)

    def test_empty_and_initial_states(self):
        for params in [{}, {'pick': '1'}]:
            response = self.client.get(reverse('surprise_recipe'), params)
            self.assertContains(response, 'No recipes yet')
            self.assertNotContains(response, '← Back to Recipes')
        self.recipe('Brownie')
        response = self.client.get(reverse('surprise_recipe'))
        self.assertContains(response, 'Ready to discover your recipe for today?')
        self.assertNotIn('selected_recipe', response.context)

    def test_real_recipe_detail_and_shared_card(self):
        recipe = self.recipe('Brownie')
        response = self.client.get(reverse('surprise_recipe'), {'pick': '1'})
        self.assertEqual(response.context['selected_recipe'], recipe)
        self.assertContains(response, recipe.get_absolute_url())
        self.assertContains(response, 'Desserts')
        self.assertContains(response, '25 min')
        self.assertTemplateUsed(response, 'recipes/recipe_grid.html')
        self.assertContains(response, 'Surprise Me Again')
        self.assertEqual(response.context['shuffle_recipes'], [{'name': 'Brownie', 'image': ''}])

    def test_repeat_avoids_only_the_previous_recipe(self):
        first = self.recipe('Brownie')
        second = self.recipe('Cake')
        for previous, expected in [(first, second), (second, first)]:
            response = self.client.get(reverse('surprise_recipe'), {'pick': '1', 'previous': previous.pk})
            self.assertEqual(response.context['selected_recipe'], expected)
        second.delete()
        response = self.client.get(reverse('surprise_recipe'), {'pick': '1', 'previous': first.pk})
        self.assertEqual(response.context['selected_recipe'], first)

    def test_invalid_previous_and_safe_animation_data(self):
        recipe = self.recipe('</script><script>alert(1)</script>')
        for previous in ['invalid', '9' * 100, '-1', '9999']:
            response = self.client.get(reverse('surprise_recipe'), {'pick': '1', 'previous': previous})
            self.assertEqual(response.context['selected_recipe'], recipe)
            self.assertNotContains(response, '<script>alert(1)</script>')

    def test_menu_accessible_to_guests_and_members(self):
        self.assertContains(self.client.get(reverse('recipe_list')), reverse('surprise_recipe'))
        from django.contrib.auth.models import User
        from .models import Favorite
        user = User.objects.create_user(username='surprise-user')
        recipe = self.recipe('Brownie')
        Favorite.objects.create(user=user, recipe=recipe)
        self.client.force_login(user)
        response = self.client.get(reverse('surprise_recipe'), {'pick': '1'})
        self.assertContains(response, 'favorite-button is-favorite')
        self.assertContains(response, reverse('surprise_recipe'))
