#!/bin/bash

cd /app/BaCa2

poetry run python BaCa2/manage.py migrate
poetry run python BaCa2/manage.py collectstatic --noinput

gunicorn core.wsgi -c "./gunicorn_config.py"
