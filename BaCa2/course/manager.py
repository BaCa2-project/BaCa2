from time import sleep

from BaCa2.db.creator import createDB, migrateDB, deleteDB
import logging


# log = logging.

def create_course(course_name):
    createDB(course_name)
    migrateDB(course_name)


def delete_course(course_name):
    deleteDB(course_name)
