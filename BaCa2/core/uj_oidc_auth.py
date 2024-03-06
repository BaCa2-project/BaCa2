import logging

from core.choices import UserJob
from main.models import User
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

logger = logging.getLogger(__name__)


class BaCa2UJAuth(OIDCAuthenticationBackend):

    def filter_users_by_claims(self, claims):
        email = claims.get('email')
        if not email:
            return User.objects.none()

        return User.objects.filter(email=email)

    def create_user(self, claims):
        email = claims.get('email')
        first_name = claims.get('given_name', '')
        last_name = claims.get('family_name', '')

        # UJ specific
        usos_id = claims.get('ujUsosID')
        is_student = claims.get('ujIsStudent', False)
        is_employee = claims.get('ujIsEmployee', False)
        is_doctoral = claims.get('ujIsDoctoral', False)

        user_job = User.get_user_job(is_student, is_employee, is_doctoral)

        if not email:
            return None

        user = User.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            usos_id=usos_id,
            user_job=user_job,
        )
        logger.info(
            f'Created new user: {user} ({user.first_name} {user.last_name}) [{user.user_job}]')

        return user

    def update_user(self, user, claims):
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')

        # UJ specific
        usos_id = claims.get('ujUsosID')
        if usos_id:
            user.usos_id = usos_id
        user_job = User.get_user_job(
            is_student=claims.get('ujIsStudent', False),
            is_employee=claims.get('ujIsEmployee', False),
            is_doctoral=claims.get('ujIsDoctoral', False)
        )
        # prevent accidental degradation to student
        if not (user.user_job != UserJob.ST.value and user_job == UserJob.ST.value):
            user.user_job = user_job
        user.save()

        return user
