from django.db import models


class SimpleCourseRouter:

    @staticmethod
    def test_course_db(model, **hints):
        if model._meta.app_label == "course":
            return 'test_course'

    @staticmethod
    def hinted_db(model, **hints):
        from BaCa2.settings import DATABASES
        db = hints.get('actualDB', None)
        if model._meta.app_label == "course" and db is not None and db in DATABASES.keys():
            return hints['actualDB']

    def db_for_read(self, model, **hints):
        return self.test_course_db(model, **hints)

    def db_for_write(self, model, **hints):
        return self.test_course_db(model, **hints)

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._state.db == obj2._state.db:
            return True
        if obj2._state.db == 'default':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if (db == 'default') ^ (app_label == 'course'):
            return True
        return False


# class DynamicManager(models.Manager):
#     from BaCa2.settings import DATABASES
#     from BaCa2.exceptions import RoutingError
#     def __init__(self):
#         super().__init__()
#         self._hints['actualDB'] = None
#
#     def get_queryset(self):
#         db = self._hints['actualDB']
#         if db is None or db not in DynamicManager.DATABASES.keys():
#             raise DynamicManager.RoutingError(f"Can't access DB {db}. Remember to define it using 'InCourse'")
#
#         return self._queryset_class(model=self.model, using=self._db, hints=self._hints)

