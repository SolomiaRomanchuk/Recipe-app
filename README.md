# Recipe Book

Recipe Book is a Django web application for discovering, creating, and managing recipes.
Users can browse recipes, organize them by categories and difficulty, save favorites, filter recipes, and discover random meal ideas.

## Features

- User registration and authentication
- Create, edit, and delete recipes
- Recipe categories
- Ingredients
- Recipe difficulty levels
- Quick Recipes
- Recipe filtering
- Recipe search
- Favorites
- My Recipes
- User profile with avatar
- Change password
- Surprise Me random recipe feature
- Responsive design
- Recipe images

## Technologies

- Python
- Django
- HTML
- CSS
- JavaScript
- SQLite for local development
- WhiteNoise for static files
- Gunicorn
- django-environ

## How to Run Locally

```bash
git clone <your-repository-url>
cd recipe-book

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env

## Fill .env with your local values:

SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
Then run:

python3 manage.py migrate
python3 manage.py runserver

## Open the application in your browser.
```

## Live Demo

Live demo will be added after deployment.

## Screenshot
![Recipe Book Screenshot](screenshot.png)
