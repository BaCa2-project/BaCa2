AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = [
    # Login UJ
    'mozilla_django_oidc.auth.OIDCAuthenticationBackend',
    # Custom authentication backend
    'core.auth_backend.BaCa2AuthBackend'
]

AUTH_USER_MODEL = 'main.User'
