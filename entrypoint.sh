#!/bin/bash

cd /app/BaCa2

poetry run python manage.py migrate

gunicorn core.wsgi -c "./gunicorn_config.py"
