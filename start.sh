#!/bin/sh
set -eu
cd "$(dirname "$0")"
echo 'Applying database migrations...'
python manage.py migrate --noinput
echo 'Database migrations completed.'
python manage.py ensure_superuser
exec python -m gunicorn recipe_project.wsgi:application --bind "0.0.0.0:${PORT:-8000}"
