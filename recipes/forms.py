from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Category, Recipe
from django.core.files.base import ContentFile
from io import BytesIO
from uuid import uuid4
from PIL import Image, ImageOps


class AvatarForm(forms.Form):
    avatar = forms.ImageField(widget=forms.FileInput(attrs={
        'accept': 'image/jpeg,image/png,image/webp,image/gif',
        'class': 'avatar-file-input',
    }))

    def clean_avatar(self):
        avatar = self.cleaned_data['avatar']
        if avatar.size > 5 * 1024 * 1024:
            raise forms.ValidationError('Please choose an image smaller than 5 MB.')
        if avatar.image.format not in {'JPEG', 'PNG', 'WEBP', 'GIF'}:
            raise forms.ValidationError('Please choose a JPEG, PNG, WebP, or GIF image.')
        try:
            avatar.seek(0)
            with Image.open(avatar) as image:
                image = ImageOps.exif_transpose(image)
                image.thumbnail((1024, 1024))
                output = BytesIO()
                image.convert('RGBA').save(output, format='PNG')
        except (OSError, ValueError, Image.DecompressionBombError):
            raise forms.ValidationError('This image could not be read. Please choose another photo.')
        return ContentFile(output.getvalue(), name=f'{uuid4().hex}.png')


class RecipeFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=Category.objects.order_by('name'),
        required=False,
        empty_label='Any Category',
    )
    difficulty = forms.ChoiceField(
        choices=[('', 'Any Difficulty'), *Recipe.STATUS_CHOICES],
        required=False,
    )
    time = forms.ChoiceField(
        label='Cooking Time',
        choices=[
            ('', 'Any Time'),
            ('15', 'Up to 15 minutes'),
            ('30', 'Up to 30 minutes'),
            ('60', 'Up to 60 minutes'),
            ('over60', 'More than 60 minutes'),
        ],
        required=False,
    )


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username',
            'email',
            'password1',
            'password2',
        )
