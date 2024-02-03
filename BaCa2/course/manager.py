from django.conf import settings


def create_course(course_name: str):
    """
    This function creates a new course database and migrates it

    :param course_name: The name of the course you want to create
    :type course_name: str
    """
    settings.DB_MANAGER.create_db(course_name)
    settings.DB_MANAGER.migrate_db(course_name)


def delete_course(course_name: str):
    """
    This function deletes a course from the database

    :param course_name: The name of the course you want to delete
    :type course_name: str
    """
    settings.DB_MANAGER.delete_db(course_name)
