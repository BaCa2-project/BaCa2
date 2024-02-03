LOGIN_URL = '/login/'

LOGIN_REDIRECT_URL = '/main/dashboard'

# Login UJ
# OIDC_RP_CLIENT_ID = os.getenv('OIDC_RP_CLIENT_ID')
# OIDC_RP_CLIENT_SECRET = os.getenv('OIDC_RP_CLIENT_SECRET')
#
# OIDC_OP_AUTHORIZATION_ENDPOINT = ('https://auth.dev.uj.edu.pl/auth/realms/uj/.well-known/openid'
#                                   '-configuration')
# OIDC_OP_TOKEN_ENDPOINT = ('https://auth.dev.uj.edu.pl/auth/realms/uj/.well-known/openid'
#                           '-configuration')
# OIDC_OP_USER_ENDPOINT = ('https://auth.dev.uj.edu.pl/auth/realms/uj/.well-known/openid'
#                          '-configuration')

LOGOUT_REDIRECT_URL = '/login'
