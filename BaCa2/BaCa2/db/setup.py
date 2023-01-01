ADMIN_DB_USER = {
    'user': 'root',
    'password': 'BaCa2root'
}

''' creating root db user
CREATE ROLE root WITH
	LOGIN
	SUPERUSER
	CREATEDB
	CREATEROLE
	INHERIT
	REPLICATION
	CONNECTION LIMIT -1
	PASSWORD 'BaCa2root';
GRANT postgres TO root WITH ADMIN OPTION;
COMMENT ON ROLE root IS 'root db user for db managment purposes';
'''

DEFAULT_DB_HOST = 'localhost'

DEFAULT_DB_SETTINGS = {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'USER': 'baca2',
    'PASSWORD': 'zaqwsxcde',
    'HOST': 'localhost',
    'PORT': '',
    'TIME_ZONE': None,
    'CONN_HEALTH_CHECKS': False,
    'CONN_MAX_AGE': 0,
    'AUTOCOMMIT': True,
    'OPTIONS': {},
    'ATOMIC_REQUESTS': False
}
