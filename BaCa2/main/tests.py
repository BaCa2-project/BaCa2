from django.db import transaction
from django.test import TestCase
from django.contrib.auth.models import (Group, Permission)
from django.utils import timezone

from main.models import (User, Course, Role, RolePreset)
from BaCa2.choices import BasicPermissionType


class CourseTest(TestCase):

    role_preset_1 = None
    role_preset_2 = None
    courses = []

    @classmethod
    def setUpClass(cls):
        with transaction.atomic():
            cls.role_preset_1 = RolePreset.objects.create_role_preset(
                name='role_preset_1',
                permissions=[
                    Course.CourseAction.VIEW_ROLE.label,
                    Course.CourseAction.VIEW_MEMBER.label,
                    Course.BasicAction.VIEW.label
                ]
            )
            cls.role_preset_2 = RolePreset.objects.create_role_preset(
                name='role_preset_2',
                permissions=[
                    Course.CourseAction.VIEW_ROLE.label,
                    Course.CourseAction.VIEW_MEMBER.label,
                    Course.BasicAction.VIEW.label,
                    Course.CourseAction.ADD_MEMBER.label,
                    Course.CourseAction.EDIT_ROLE.label
                ]
            )

    @classmethod
    def tearDownClass(cls):
        with transaction.atomic():
            cls.role_preset_1.delete()
            cls.role_preset_2.delete()

            for course in cls.courses:
                Course.objects.delete_course(course)

    def test_simple_course_creation(self):
        course = Course.objects.create_course(
            name='course_1',
            short_name='c1_23',
        )
        self.courses.append(course)
        self.assertTrue(Course.objects.get(short_name='c1_23') == course)
        self.assertTrue(Role.objects.filter(name='admin', course=course).exists())
        self.assertTrue(Role.objects.get(name='admin', course=course) == course.admin_role)

        for permission in Course.CourseAction.labels:
            self.assertTrue(course.admin_role.has_permission(permission))

        self.courses.remove(course)
        Course.objects.delete_course(course)


class UserTest(TestCase):
    pass
