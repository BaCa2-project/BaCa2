from core.db.creator import createDB, migrateDB, deleteDB


# log = logging.

def create_course(course_name: str):
    """
    This function creates a new course database and migrates it

    :param course_name: The name of the course you want to create
    :type course_name: str
    """
    createDB(course_name)
    migrateDB(course_name)


def delete_course(course_name: str):
    """
    This function deletes a course from the database

    :param course_name: The name of the course you want to delete
    :type course_name: str
    """
    deleteDB(course_name)
