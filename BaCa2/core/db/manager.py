import copy
import json
import logging
from pathlib import Path
from threading import Lock

import psycopg2
from libinjection import is_sql_injection

logger = logging.getLogger(__name__)


#: Postgres query to close all connections to a database
CLOSE_ALL_DB_CONNECTIONS = """SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '%s'
  AND pid <> pg_backend_pid();
"""


class DB:
    """
    A class to represent a database.
    """

    def __init__(self,
                 db_name: str,
                 defaults: dict = None,
                 key_is_name: bool = False,
                 **kwargs):
        """
        It initializes the DB object.

        :param db_name: The name of the database.
        :type db_name: str
        :param defaults: The default settings for the database.
        :type defaults: dict
        :param key_is_name: Whether the key of the database is the name of the database.
        :type key_is_name: bool
        :param kwargs: The settings for the database.
        """
        if defaults is None:
            defaults = {}
        if not db_name:
            raise ValueError('db_name must be a non-empty string.')
        self.db_name = db_name
        self.key_is_name = key_is_name
        self.key = self.db_name if key_is_name else self.db_name + '_db'
        self.settings = defaults | kwargs | {'NAME': self.key}
        if key_is_name:
            self.settings['NAME'] = self.db_name

    @classmethod
    def from_json(cls, db_dict: dict, db_name: str = None) -> 'DB':
        """
        It creates a DB object from a dictionary. If the db_name is not provided, it is taken from
        the dictionary, but without the '_db' suffix.

        :param db_dict: The dictionary with the database settings.
        :type db_dict: dict
        :param db_name: The name of the database.
        :type db_name: str

        :return: The DB object.
        :rtype: DB
        """
        if 'NAME' not in db_dict:
            raise ValueError('DB name not found in dictionary.')
        if db_name is None:
            db_name = db_dict.pop('NAME')
        else:
            db_dict.pop('NAME')
        if db_name.endswith('_db'):
            db_name = db_name[:-3]
            logger.warning(f'Database name {db_name} has been stripped of the "_db" suffix.')
        return cls(db_name, **db_dict)

    def to_dict(self) -> dict:
        """
        It returns a deep copy of the database settings as a dictionary.
        """
        return copy.deepcopy(self.settings)

    @property
    def name(self):
        """
        It returns the name of the database.
        """
        return self.db_name


class DBManager:
    """
    A class to manage databases in the system. It allows you to create, delete and migrate
    databases on django runtime.
    """

    #: Maximum length of a database name. Used to detect SQL injection.
    MAX_DB_NAME_LENGTH = 63

    class SQLInjectionError(Exception):
        """
        An exception raised when SQL injection is detected.
        """
        pass

    def __init__(self,
                 cache_file: Path,
                 default_settings: dict,
                 root_user: str,
                 root_password: str,
                 db_host: str = 'localhost',
                 databases: dict = None,
                 default_db_key: str = 'default',
                 add_default: bool = True, ):
        """
        It initializes the DBManager object.

        :param cache_file: The file where the database settings are stored.
        :type cache_file: Path
        :param default_settings: The default settings for new databases.
        :type default_settings: dict
        :param root_user: The root username of the database server.
        :type root_user: str
        :param root_password: The root password of the database server.
        :type root_password: str
        :param db_host: The host of the database server.
        :type db_host: str
        :param databases: The databases that are already created - reference to django DATABASES
            setting.
        :type databases: dict
        :param default_db_key: The default key for the default database.
        :type default_db_key: str
        :param add_default: Whether to add the default database to the runtime databases.
        :type add_default: bool
        """
        self.cache_file = cache_file
        self.default_settings = default_settings
        self.root_user = root_user
        self.root_password = root_password
        self.db_host = db_host
        self.databases = databases
        if self.databases is None:
            self.databases = {}
        self.default_db_key = default_db_key
        self.databases_access_lock = Lock()
        self.db_root_access_lock = Lock()
        self.cache_lock = Lock()

        if add_default:
            default = DB(self.default_db_key, self.default_settings, key_is_name=True)
            self.databases['default'] = default.to_dict()

        logger.info('DBManager initialized.')

    def _raw_root_connection(self):
        """
        It creates a raw connection to the database server as the root user

        :return: A connection to the postgres database.
        """
        try:
            conn = psycopg2.connect(
                database='postgres',
                user=self.root_user,
                password=self.root_password,
                host=self.db_host
            )
            conn.autocommit = True
            return conn
        except psycopg2.OperationalError as e:
            raise psycopg2.OperationalError(f'Error connecting to the database: {str(e)}')

    def detect_sql_injection(self, db_name: str) -> None:
        """
        It detects if the database name is a SQL injection.

        :param db_name: The name of the database to check.
        :type db_name: str

        :raises self.SQLInjectionError: If the database name is a SQL injection.
        """
        db_name = db_name.strip()
        if not db_name:
            raise self.SQLInjectionError('Empty database name.')

        if ' ' in db_name:
            raise self.SQLInjectionError(
                'Spaces detected in database name. Potential SQL injection.')

        if len(db_name) > self.MAX_DB_NAME_LENGTH:
            raise self.SQLInjectionError(
                'Database name exceeds maximum length. Potential SQL injection.')

        if db_name.lower() in self.RESERVED_DB_KEYS:
            raise self.SQLInjectionError(
                'Reserved database name detected. Potential SQL injection.')

        if is_sql_injection(db_name)['is_sqli']:
            raise self.SQLInjectionError('SQL injection detected.')

    def create_db(self, db_name: str, **kwargs) -> None:
        """
        It creates a new database, adds it to the settings file and to the runtime database
        connections.

        :param db_name: The name of the database to create
        :type db_name: str
        """
        self.detect_sql_injection(db_name)
        db = DB(db_name, self.default_settings, **kwargs)

        with self.databases_access_lock:
            if db.key in self.databases:
                raise ValueError(f'DB {db_name} already exists.')

            with self.db_root_access_lock:
                conn = self._raw_root_connection()
                cursor = conn.cursor()

                drop_if_exist = ' DROP DATABASE IF EXISTS %s; '
                sql = ' CREATE DATABASE %s; '

                try:
                    cursor.execute(drop_if_exist, (db.key,))
                    cursor.execute(sql, (db.key,))
                except Exception as e:
                    logger.error(f'Error executing SQL commands: {str(e)}')

                finally:
                    conn.close()

                self.databases.setdefault(db.name, db.to_dict())

                with self.cache_lock:
                    self.save_cache(with_locks=False)
        logger.info(f'Database {db_name} created.')

    def migrate_db(self, db_name: str, migrate_all: bool = False) -> None:
        """
        It migrates the database to the latest version, using django management command
        (``migrate``).

        :param db_name: The name of the database to migrate.
        :type db_name: str
        :param migrate_all: Should be set to True if method is called from ``migrate_all`` method.
        :type migrate_all: bool
        """
        from django.core.management import call_command

        if migrate_all:
            if db_name not in self.databases:
                raise ValueError(f'DB {db_name} does not exist or not registered properly.')
        else:
            with self.databases_access_lock:
                if db_name not in self.databases:
                    raise ValueError(f'DB {db_name} does not exist or not registered properly.')
        call_command('migrate',
                     database=db_name,
                     interactive=False,
                     skip_checks=True,
                     verbosity=0)
        logger.info(f'Database {db_name} migrated.')

    def migrate_all(self):
        """
        It migrates all the databases to the latest version.
        """
        with self.databases_access_lock:
            for db_key in self.databases.keys():
                if db_key != 'default':
                    self.migrate_db(db_key, migrate_all=True)

    def delete_db(self, db_name: str) -> None:
        """
        It deletes a database from the database server and from the runtime databases.

        :param db_name: The name of the database to delete.
        :type db_name: str
        """
        self.detect_sql_injection(db_name)
        db = DB(db_name, self.default_settings)

        with self.databases_access_lock:
            if db.name not in self.databases:
                raise ValueError(f'DB {db_name} does not exist.')

            self.databases.pop(db.name, None)

            with self.cache_lock:
                self.save_cache(with_locks=False)

            with self.db_root_access_lock:
                conn = self._raw_root_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute(CLOSE_ALL_DB_CONNECTIONS, (db.key,))
                    cursor.execute(' DROP DATABASE IF EXISTS %s; ', (db.key,))
                except Exception as e:
                    logger.error(f'Error deleting database: {str(e)}')
                finally:
                    conn.close()
        logger.info(f'Database {db_name} deleted.')

    def parse_cache(self) -> None:
        """
        It parses the cache file and loads the databases into the runtime databases.
        Best to be called on django app startup to load the databases from the cache file.
        """
        with self.cache_lock:
            try:
                with self.cache_file.open('r') as f:
                    cache = json.load(f)
            except FileNotFoundError:
                logger.error('Cache file not found. Continuing with empty cache.')
                cache = {}
            except json.JSONDecodeError:
                logger.error('Error loading JSON file. Continuing with empty cache.')
                cache = {}

            with self.databases_access_lock:
                for db_name, db_settings in cache.items():
                    db = DB.from_json(db_settings, db_name=db_name)
                    self.databases.setdefault(db.name, db.to_dict())

        logger.info('Databases loaded from cache.')

        # Check if there were changes to the databases
        if self.databases != {}:
            self.save_cache()

    def save_cache(self, with_locks: bool = True) -> None:
        """
        It saves the runtime databases into the cache file.

        :param with_locks: Whether to use locks when accessing the databases.
        :type with_locks: bool
        """
        if with_locks:
            with self.databases_access_lock:
                databases = copy.deepcopy(self.databases)
        else:
            databases = copy.deepcopy(self.databases)

        databases.pop('default', None)
        try:
            self.cache_file.write_text(json.dumps(databases, indent=4))
            logger.info('Databases saved to cache.')
        except Exception as e:
            logger.error(f'Error saving databases to cache: {str(e)}')
