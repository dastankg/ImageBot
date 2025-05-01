#!/bin/sh

while ! nc -z db 5432; do
  sleep 0.2
done

python manage.py makemigrations
python manage.py migrate

gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120