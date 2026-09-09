from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    STATUS_CHOICES = [
        ('easy', 'Легко'),
        ('medium', 'Середньо'),
        ('hard', 'Складно'),
    ]

    name = models.CharField(max_length=200)
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
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name