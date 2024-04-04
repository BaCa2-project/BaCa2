Installation guide
==================

.. note::
    This application is prepared to work with some kind of automated checker backend
    (e.g. `KOLEJKA <https://kolejka.matinf.uj.edu.pl/>`_) and broker to translate communication between them.

    Our app provides fully functional broker to work with KOLEJKA backend.

Development installation
------------------------
To install main django web app locally (for development purposes) follow this process:

1. Install prerequisites:

    a. Python 3.11 or newer & pip (`link to Python downloads <https://www.python.org/downloads/>`_)
    b. PostgreSQL 16 (`link to PostgreSQL downloads <https://www.postgresql.org/download/>`_)

2. Install poetry (`about installing poetry <https://python-poetry.org/docs/#installation>`_)

    .. code-block:: console

        pip install poetry

3. Install project dependencies - inside project directory run:

    .. code-block:: console

        python3 -m poetry install

4. Prepare postgres server:

    a. Create new database: ```baca2db```
    b. Create new user ```root```. This db user will be used to managed auto-created databases.

        .. code-block:: postgresql

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
            COMMENT ON ROLE root IS 'root db user for db management purposes';

    c. Create new user ```baca2```. This user will be used for most of app operations.

        .. code-block:: postgresql

            CREATE ROLE baca2
                SUPERUSER
                CREATEDB
                CREATEROLE
                REPLICATION
                PASSWORD 'zaqwsxcde';

            GRANT postgres TO baca2 WITH ADMIN OPTION;

5. *(\*)* Make migration files.

    In current version it is needed to manually make migrations file. In future migrations will be given with project.

    .. code-block:: console

        python3 -m poetry run python3 ./BaCa2/manage.py makemigrations

6. Migrate database

    .. code-block:: console

        python3 -m poetry run python3 ./BaCa2/manage.py migrate

7. Create superuser for django app

    .. code-block:: console

        python3 -m poetry run python3 ./BaCa2/manage.py createsuperuser

    And follow interactive user creation process.

8. All done! Your BaCa2 instance should be working properly.
