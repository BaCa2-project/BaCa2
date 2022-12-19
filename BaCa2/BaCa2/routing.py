class SimpleCourseRouter:

    def test_course_db(self, model, **hints):
        if model._meta.app_label == "course":
            return 'test_course'

    def db_for_read(self, model, **hints):
        return self.test_course_db(model, **hints)

    def db_for_write(self, model, **hints):
        return self.test_course_db(model, **hints)

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._state.db == obj2._state.db:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db != 'default' and app_label == 'course':
            return True
        return False
