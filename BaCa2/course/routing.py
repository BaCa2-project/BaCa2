from __future__ import annotations
from typing import TYPE_CHECKING

from core.settings import currentDB

if TYPE_CHECKING:
    from main.models import Course


class SimpleCourseRouter:
    """
    Basic usability for all routers in this project.
    """

    @staticmethod
    def _test_course_db(model, **hints):
        if model._meta.app_label == "course":
            return 'test_course'

    def db_for_read(self, model, **hints):
        return self._test_course_db(model, **hints)

    def db_for_write(self, model, **hints):
        return self._test_course_db(model, **hints)

    def allow_relation(self, obj1, obj2, **hints):
        """
        If the two objects are in the same database, or if the second object is in the default database, then allow the
        relationship

        :param obj1: The first object in the relation
        :param obj2: The object that is being created
        :return: The database alias.
        """
        if obj1._state.db == obj2._state.db or obj2._state.db == 'default':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        If the database is 'default' and the app_label is 'course', or if the database
        is not 'default' and the app_label is not 'course', then return True

        :param db: The alias of the database that is being used
        :param app_label: The name of the application that contains the model
        :param model_name: The name of the model to migrate
        :return: True or False
        """
        if (db == 'default') ^ (app_label == 'course'):
            return True
        return False


class ContextCourseRouter(SimpleCourseRouter):
    """
    Router that uses context given by :py:class:`InCourse' context manager.
    """

    @staticmethod
    def _get_context(model, **hints):
        """
        It returns the name of the database to use for a given model. It gets it from context manager.

        :param model: The model class that is being queried
        :return: The name of the database to use.
        """
        if model._meta.app_label != "course":
            return 'default'

        from core.settings import DATABASES
        from core.exceptions import RoutingError

        try:
            db = currentDB.get()
        except LookupError:
            raise RoutingError(
                "No DB chosen. Remember to use 'with InCourse', while accessing course instance.")
        if db not in DATABASES.keys():
            raise RoutingError(f"Can't access course DB {db}. Check the name in 'with InCourse'")

        return db

    def db_for_read(self, model, **hints):
        """
        Returns database for reading operations using :py:func:`ContextCourseRouter._get_context`.

        :param model: Model to be filled with data from specific database.
        :return: Database name
        """
        return self._get_context(model, **hints)

    def db_for_write(self, model, **hints):
        """
        Returns database for writing operations using :py:func:`ContextCourseRouter._get_context`.

        :param model: Model to be saved to specific database.
        :return: Database name
        """
        return self._get_context(model, **hints)


class InCourse:
    """
    It allows you to give the context database. Everything called inside this context manager
    will be performed on database specified on initialization.

    Usage example:

    .. code-block:: python

        from course.routing import InCourse

        using InCourse('course123'):
            Submit.objects.create_submit(...)

    This code will create new submission inside of course ``course123``.
    """

    def __init__(self, course: int | str | Course):
        from util.models_registry import ModelsRegistry
        if isinstance(course, str):
            self.db = course
        else:
            self.db = ModelsRegistry.get_course(course).short_name

    def __enter__(self):
        self.token = currentDB.set(self.db)

    def __exit__(self, *args):
        currentDB.reset(self.token)

    @staticmethod
    def is_defined():
        """
        Checks if there is any context database set.

        :return: True if there is any context database set.
        """
        try:
            currentDB.get()
        except LookupError:
            return False
        return True


class OptionalInCourse(InCourse):
    """
    It allows you to give the context database. Everything called inside this context manager
    will be performed on database specified on initialization. If no database is specified, it will
    be on already set context database.

    Usage example:

    .. code-block:: python

        from course.routing import OptionalInCourse

        using OptionalInCourse('course123'):
            Submit.create_new(...)

    This code will create new submission inside of course ``course123``.

    But this code:

    .. code-block:: python

            from course.routing import OptionalInCourse

            using OptionalInCourse():
                Submit.create_new(...)

    will create new submission inside of course set by :py:class:`InCourse` context manager. If there is no context
    database set, it will raise :py:class:`RoutingError`.
    """

    def __init__(self, course_or_none: int | str | Course | None):

        #: Indicates if database alias was provided
        self.db_provided = course_or_none is not None
        if self.db_provided:
            super().__init__(course_or_none)
        else:
            self.db = None

    def __enter__(self):
        if self.db_provided:
            super().__enter__()

    def __exit__(self, *args):
        if self.db_provided:
            super().__exit__(*args)
