from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile'
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True)

    @property
    def avatar_url(self):
        try:
            if self.avatar and self.avatar.storage.exists(self.avatar.name):
                return self.avatar.url
        except (OSError, ValueError):
            pass
        return ''


class Category(models.Model):
    name = models.CharField(max_length=100)
    emoji = models.CharField(max_length=10, default='🍽️')

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    emoji = models.CharField(max_length=10, default='🍽️')

    def __str__(self):
        return self.name

class Recipe(models.Model):
    STATUS_CHOICES = [
         ('easy', 'Easy'),
         ('medium', 'Medium'),
         ('hard', 'Hard'),
    ]

    name = models.CharField(max_length=200)

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        null=True,
    )
    
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        blank=True,
        related_name='recipes'
    )
    cooking_time = models.PositiveIntegerField()
    difficulty = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='easy'
    )
    description = models.TextField(blank=True)

    image = models.ImageField(
        upload_to='recipes/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return reverse(
            'recipe_detail',
            kwargs={'pk': self.pk}
        )

    def __str__(self):
        return self.name

class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'

    
