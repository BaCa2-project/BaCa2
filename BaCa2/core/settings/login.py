LOGIN_URL = '/login/'

LOGIN_REDIRECT_URL = '/main/dashboard'

# Login UJ
OIDC_RP_CLIENT_ID = os.getenv('OIDC_RP_CLIENT_ID')  # noqa: F821
OIDC_RP_CLIENT_SECRET = os.getenv('OIDC_RP_CLIENT_SECRET')  # noqa: F821

AUTH_DOMAIN = os.getenv('AUTH_DOMAIN')  # noqa: F821

OIDC_OP_AUTHORIZATION_ENDPOINT = (
    f'https://{AUTH_DOMAIN}/auth/realms/uj/protocol/openid-connect/auth')
OIDC_OP_TOKEN_ENDPOINT = (
    f'https://{AUTH_DOMAIN}/auth/realms/uj/protocol/openid-connect/token')
OIDC_OP_USER_ENDPOINT = (
    f'https://{AUTH_DOMAIN}/auth/realms/uj/protocol/openid-connect/userinfo')
OIDC_RP_SIGN_ALGO = 'RS256'
OIDC_OP_JWKS_ENDPOINT = f'https://{AUTH_DOMAIN}/auth/realms/uj/protocol/openid-connect/certs'

OIDC_OP_LOGOUT_URL = f'https://{AUTH_DOMAIN}/auth/realms/uj/protocol/openid-connect/logout'

LOGOUT_REDIRECT_URL = '/login'

ALLOWED_INTERNAL_EMAILS = [
    '@uj.edu.pl',
    '@student.uj.edu.pl',
    '@doctoral.uj.edu.pl',
    '@doktorant.uj.edu.pl',
    '@ii.uj.edu.pl',
]
