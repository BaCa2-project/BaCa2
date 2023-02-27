import logging

import psycopg2
from threading import Lock

from BaCa2.db.setup import DEFAULT_DB_SETTINGS
from BaCa2.exceptions import NewDBError

log = logging.getLogger(__name__)

#: A lock that prevents multiple threads from accessing the database as root at the same time.
_db_root_access = Lock()


def _raw_root_connection():
    """
    It creates a raw connection to the database server as the root user
    :return: A connection to the postgres database.
    """
    from BaCa2.db.setup import ADMIN_DB_USER, DEFAULT_DB_HOST
    conn = psycopg2.connect(
        database='postgres',
        user=ADMIN_DB_USER['user'],
        password=ADMIN_DB_USER['password'],
        host=DEFAULT_DB_HOST
    )
    conn.autocommit = True
    return conn


def createDB(db_name: str, verbose: bool=False, **db_kwargs):
    """
    It creates a new database, adds it to the settings file and to the runtime database connections.

    While runtime :py:data:`_db_root_access` is acquired.

    :param db_name: The name of the database to create
    :type db_name: str
    :param verbose: If True, prints out the progress of the function, defaults to False
    :type verbose: bool (optional)
    """

    db_key = db_name
    db_name += '_db'
    from BaCa2.settings import DATABASES, SETTINGS_DIR

    if db_key in DATABASES.keys():
        log.error(f"DB {db_name} already exists.")
        raise NewDBError(f"DB {db_name} already exists.")

    _db_root_access.acquire()
    if verbose:
        print("Creating connection...")
    conn = _raw_root_connection()
    cursor = conn.cursor()

    drop_if_exist = f'''DROP DATABASE IF EXISTS {db_name};'''
    sql = f''' CREATE DATABASE {db_name}; '''

    cursor.execute(drop_if_exist)
    cursor.execute(sql)
    if verbose:
        print(f"DB {db_name} created.")

    conn.close()
    log.info(f"DB {db_name} created successfully.")

    new_db = DEFAULT_DB_SETTINGS | db_kwargs | {'NAME': db_name}
    DATABASES[db_key] = new_db
    # from django.db import connections
    # connections.configure_settings(None)
    if verbose:
        print("Connection created.")

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
    if verbose:
        print("Settings saved to file.")

    # migrateDB(db_name)

    _db_root_access.release()

    log.info(f"DB {db_name} settings saved to ext_databases.")


def migrateDB(db_name: str):
    """
    It runs the Django command `migrate` on the database specified by `db_name`

    :param db_name: The name of the database to migrate
    :type db_name: str
    """
    from django.core.management import call_command
    # call_command('makemigrations')

    call_command('migrate', database=db_name, interactive=False, skip_checks=True)
    log.info(f"Migration for DB {db_name} applied.")


def migrateAll():
    """
    It loops through all the databases in the settings file and runs the migrateDB function on each one.
    """
    from BaCa2.settings import DATABASES
    log.info(f"Migrating all databases.")
    for db in DATABASES.keys():
        if db != 'default':
            migrateDB(db)
    log.info(f"All databases migrated.")


CLOSE_ALL_DB_CONNECTIONS = '''SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '%s'
  AND pid <> pg_backend_pid();
'''


def deleteDB(db_name: str, verbose: bool=False):
    """
    It deletes a database from the settings.DATABASES dictionary, deletes the database settings from the ext_databases.py
    file, closes all connections to the database, and then drops the database.

    While runtime :py:data:`_db_root_access` is acquired.

    :param db_name: str
    :type db_name: str
    :param verbose: if True, prints out what's happening, defaults to False
    :type verbose: bool (optional)
    """
    from BaCa2.settings import DATABASES, BASE_DIR

    log.info(f'Attempting to delete DB {db_name}')

    _db_root_access.acquire()

    log.info(f"Deleting DB {db_name} from settings.DATABASES.")
    try:
        DATABASES.pop(db_name)
    except KeyError:
        log.info(f"Database {db_name} not found in settings.DATABASES.")
    db_alias = f"{db_name}_db"

    if verbose:
        print(f"Deleted {db_name} from settings.DATABASES.")

    with open(BASE_DIR / "BaCa2/db/ext_databases.py", 'r') as f:
        db_setts = f.read().split('\n\n')

    for i, sett in enumerate(db_setts):
        if sett.find(f"DATABASES['{db_name}']") != -1:
            log.info(f"Deleting DB {db_name} from ext_databases.py")
            db_setts.pop(i)
            break

    with open(BASE_DIR / "BaCa2/db/ext_databases.py", 'w') as f:
        f.write('\n\n'.join(db_setts))

    if verbose:
        print(f"Deleted {db_name} settings from ext_databases.py")

    conn = _raw_root_connection()
    cursor = conn.cursor()

    cursor.execute(CLOSE_ALL_DB_CONNECTIONS % db_alias)
    if verbose:
        print("All DB connections closed")

    sql = f''' DROP DATABASE IF EXISTS {db_alias}; '''
    if verbose:
        print(f"DB {db_alias} dropped.")
    cursor.execute(sql)
    conn.close()
    log.info(f"DB {db_name} successfully deleted.")

    _db_root_access.release()
