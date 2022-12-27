from django.db import models

from BaCa2.settings import currentDB

class SimpleCourseRouter:

    @staticmethod
    def _test_course_db(model, **hints):
        if model._meta.app_label == "course":
            return 'test_course'

    def db_for_read(self, model, **hints):
        return self._test_course_db(model, **hints)

    def db_for_write(self, model, **hints):
        return self._test_course_db(model, **hints)

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._state.db == obj2._state.db or obj2._state.db == 'default':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if (db == 'default') ^ (app_label == 'course'):
            return True
        return False


class ContextCourseRouter(SimpleCourseRouter):
    @staticmethod
    def _get_context(model, **hints):
        if model._meta.app_label != "course":
            return 'default'

        from BaCa2.settings import DATABASES
        from BaCa2.exceptions import RoutingError

        try:
            db = currentDB.get()
        except LookupError:
            raise RoutingError(f"No DB chosen. Remember to use 'with InCourse', while accessing course instance.")
        if db not in DATABASES.keys():
            raise RoutingError(f"Can't access course DB {db}. Check the name in 'with InCourse'")

        return db

    def db_for_read(self, model, **hints):
        return self._get_context(model, **hints)

    def db_for_write(self, model, **hints):
        return self._get_context(model, **hints)


# class DynamicManager(models.Manager):
#     from BaCa2.settings import DATABASES
#     from BaCa2.exceptions import RoutingError
#
#     def get_queryset(self):
#         db = currentDB.get(default=None)
#         if db is None or db not in DynamicManager.DATABASES.keys():
#             raise DynamicManager.RoutingError(f"Can't access DB {db}. Remember to define it using 'InCourse'")
#
#         return self._queryset_class(model=self.model, using=db, hints=self._hints)

class InCourse:
    def __init__(self, db):
        self.db = db

    def __enter__(self):
        self.token = currentDB.set(self.db)

    def __exit__(self, *args):
        currentDB.reset(self.token)
