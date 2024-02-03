import json
from pathlib import Path
from threading import Lock
from typing import Self

import psycopg2

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
        if defaults is None:
            defaults = {}
        self.db_name = db_name
        self.key_is_name = key_is_name
        self.settings = defaults | kwargs | {'NAME': self.key}
        if key_is_name:
            self.settings['NAME'] = self.db_name

    @classmethod
    def from_json(cls, db_dict: dict) -> Self:
        if 'NAME' not in db_dict:
            raise ValueError('DB name not found in dictionary.')
        db_name = db_dict.pop('NAME')
        return cls(db_name, **db_dict)

    def to_dict(self) -> dict:
        return self.settings.copy()

    @property
    def name(self):
        return self.db_name

    @property
    def key(self):
        if self.key_is_name:
            return self.db_name
        return self.db_name + '_db'


class DBManager:
    """
    A class to manage databases in the system. It allows you to create, delete and migrate
    databases on django runtime.
    """

    #: A list of reserved database names. These databases cannot be created or deleted.
    RESERVED_DB_KEYS = ['postgres', 'template0', 'template1']

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

    def _raw_root_connection(self):
        """
        It creates a raw connection to the database server as the root user

        :return: A connection to the postgres database.
        """

        conn = psycopg2.connect(
            database='postgres',
            user=self.root_user,
            password=self.root_password,
            host=self.db_host
        )
        conn.autocommit = True
        return conn

    def detect_sql_injection(self, db_name: str) -> None:
        """
        It detects if the database name is a SQL injection.

        :param db_name: The name of the database to check.
        :type db_name: str

        :raises self.SQLInjectionError: If the database name is a SQL injection.
        """
        if len(db_name.split()) > 1 or len(db_name) > 63 or db_name in self.RESERVED_DB_KEYS:
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

                drop_if_exist = f' DROP DATABASE IF EXISTS {db.key}; '
                sql = f' CREATE DATABASE {db.key}; '

                cursor.execute(drop_if_exist)
                cursor.execute(sql)

                conn.close()

                self.databases[db.name] = db.to_dict()

                with self.cache_lock:
                    self.save_cache(with_locks=False)

    def migrate_db(self, db_name: str) -> None:
        """
        It migrates the database to the latest version, using django management command
        (``migrate``).

        :param db_name: The name of the database to migrate.
        :type db_name: str
        """
        from django.core.management import call_command

        with self.databases_access_lock:
            if db_name not in self.databases:
                raise ValueError(f'DB {db_name} does not exist or not registered properly.')
        call_command('migrate', database=db_name, interactive=False, skip_checks=True)

    def migrate_all(self):
        """
        It migrates all the databases to the latest version.
        """
        with self.databases_access_lock:
            for db_key in self.databases.keys():
                if db_key != 'default':
                    self.migrate_db(db_key)

    def delete_db(self, db_name: str) -> None:
        """
        It deletes a database from the database server and from the runtime databases.

        :param db_name: The name of the database to delete.
        :type db_name: str
        """
        self.detect_sql_injection(db_name)
        db = DB(db_name, self.default_settings)

        with self.databases_access_lock:
            try:
                self.databases.pop(db.name)
            except KeyError:
                pass

            with self.cache_lock:
                self.save_cache(with_locks=False)

            with self.db_root_access_lock:
                conn = self._raw_root_connection()
                cursor = conn.cursor()
                cursor.execute(CLOSE_ALL_DB_CONNECTIONS % db.key)
                cursor.execute(f' DROP DATABASE IF EXISTS {db.key}; ')
                conn.close()

    def parse_cache(self) -> None:
        """
        It parses the cache file and loads the databases into the runtime databases.
        Best to be called on django app startup to load the databases from the cache file.
        """
        with self.cache_lock:
            if not self.cache_file.exists():
                return
            with open(self.cache_file, 'r') as f:
                try:
                    cache = json.load(f)
                except json.JSONDecodeError:
                    return
                for _db_name, db_settings in cache.items():
                    db = DB.from_json(db_settings)
                    with self.databases_access_lock:
                        self.databases[db.name] = db.to_dict()

    def save_cache(self, with_locks: bool = True) -> None:
        """
        It saves the runtime databases into the cache file.

        :param with_locks: Whether to use locks when accessing the databases.
        :type with_locks: bool
        """
        if with_locks:
            with self.databases_access_lock:
                databases = self.databases.copy()
        else:
            databases = self.databases.copy()

        if 'default' in databases:
            databases.pop('default')
        with open(self.cache_file, 'wt') as f:
            json.dump(databases, f, indent=4)
