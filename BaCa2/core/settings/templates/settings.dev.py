DEBUG = True

# Disable SSL redirect
SECURE_SSL_REDIRECT = False

# Disable broker connection
MOCK_BROKER = True

# Disable oidc authentication
try:
    AUTHENTICATION_BACKENDS.remove(  # noqa: F821
        'mozilla_django_oidc.auth.OIDCAuthenticationBackend')
except ValueError:
    pass

# Disable OIDC middleware
try:
    MIDDLEWARE.remove('mozilla_django_oidc.middleware.SessionRefresh')  # noqa: F821
except ValueError:
    pass
