#!/bin/bash

cd /app/BaCa2

gunicorn core.wsgi -c "./gunicorn_config.py"
