DEBUG = True

# Disable SSL redirect
SECURE_SSL_REDIRECT = False

# Disable oidc authentication
try:
    AUTHENTICATION_BACKENDS.remove(  # noqa: F821
        'mozilla_django_oidc.auth.OIDCAuthenticationBackend')
except ValueError:
    pass
