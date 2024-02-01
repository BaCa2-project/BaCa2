import os

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG')

HOST_NAME = os.getenv('HOST_NAME')
HOST_IP = os.getenv('HOST_IP')

ALLOWED_HOSTS = [
    '0.0.0.0',
    '127.0.0.1',
    'localhost',
    HOST_NAME,
    HOST_IP,
]

# mark signal redirected via proxy as https
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

CSRF_TRUSTED_ORIGINS = [
    f'https://{HOST_NAME}',
    'https://127.0.0.1'
]
