import logging

from django.conf import settings

from core.choices import ResultStatus

logger = logging.getLogger(__name__)

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


def resend_pending_submits():
    """
    This function resends all pending submits to broker
    """
    from broker_api.models import BrokerSubmit
    from main.models import Course

    from .models import Submit
    from .routing import InCourse

    courses = Course.objects.all()
    resent_submits = 0
    for course in courses:
        with InCourse(course):
            submits = Submit.objects.filter(submit_status=ResultStatus.PND)
            for submit in submits:
                if not BrokerSubmit.objects.filter(course=course,
                                                   submit_id=submit.pk,
                                                   ).exists():
                    submit.send()
                    logger.debug(f'Submit {submit.pk} resent to broker')
                    resent_submits += 1

    if resent_submits > 0:
        logger.info(f'Resent {resent_submits} submits to broker')
