#!/bin/bash

SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL:-"admin@admin.com"}
cd /app/BaCa2/

poetry shell

python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py createsuperuser --email $SUPERUSER_EMAIL --noinput || true
