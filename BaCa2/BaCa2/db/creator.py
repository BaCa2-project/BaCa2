import logging
import psycopg2

from BaCa2.db.setup import DEFAULT_DB_SETTINGS
from BaCa2.exceptions import NewDBError

log = logging.getLogger(__name__)


def createDB(db_name, **db_kwargs):
    db_key = db_name
    db_name += '_db'
    from BaCa2.settings import DATABASES, SETTINGS_DIR
    from BaCa2.db.setup import ADMIN_DB_USER, DEFAULT_DB_HOST

    if db_key in DATABASES.keys():
        log.error(f"DB {db_name} already exists.")
        raise NewDBError(f"DB {db_name} already exists.")

    conn = psycopg2.connect(
        database='postgres',
        user=ADMIN_DB_USER['user'],
        password=ADMIN_DB_USER['password'],
        host=DEFAULT_DB_HOST
    )

    conn.autocommit = True
    cursor = conn.cursor()

    sql = f''' CREATE DATABASE {db_name}; '''

    cursor.execute(sql)
    conn.close()
    log.info(f"DB {db_name} created successfully.")

    new_db = DEFAULT_DB_SETTINGS | db_kwargs | {'NAME': db_name}
    DATABASES[db_name] = new_db

    new_db_save = f'''
DATABASES['{db_key}'] = {'{'}
    'ENGINE': '{new_db['ENGINE']}',
    'NAME': '{new_db['NAME']}',
    'USER': '{new_db['USER']}',
    'PASSWORD': '{new_db['PASSWORD']}',
    'HOST': '{new_db['HOST']}',
    'PORT': '{new_db['PORT']}'
{'}'}

'''
    with open(SETTINGS_DIR / 'db/ext_databases.py', 'a') as f:
        f.write(new_db_save)

    log.info(f"DB {db_name} settings saved to ext_databases.")


def migrateDB(db_name):
    from django.core.management import call_command
    call_command('migrate', f'--database={db_name}')
    log.info(f"Migration for DB {db_name} applied.")


def migrateAll():
    from BaCa2.settings import DATABASES
    log.info(f"Migrating all databases.")
    for db in DATABASES.keys():
        migrateDB(db)
    log.info(f"All databases migrated.")
