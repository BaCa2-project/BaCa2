from django.db import transaction
from django.test import TestCase
from django.contrib.auth.models import (Group, Permission)
from django.utils import timezone
from django.core.exceptions import ValidationError

from main.models import (User, Course, Role, RolePreset)
from BaCa2.choices import BasicPermissionType


class CourseTest(TestCase):

    role_preset_1 = None
    role_preset_2 = None
    courses = []

    @classmethod
    def setUpClass(cls) -> None:
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
    def tearDownClass(cls) -> None:
        with transaction.atomic():
            cls.role_preset_1.delete()
            cls.role_preset_2.delete()

            for course in [course for course in cls.courses if course.id is not None]:
                Course.objects.delete_course(course)

    def test_simple_course_creation_deletion(self) -> None:
        """
        Tests the creation and deletion of a course without any members or custom/preset roles.
        Creates two courses with admin role only and deletes them. Checks if courses and roles
        are created and deleted, checks if the admin role has the correct permissions. Asserts that
        the creation of a course with an already existing short_name raises a ValidationError.
        """
        course1 = Course.objects.create_course(
            name='course_1',
            short_name='c1_23',
        )
        self.courses.append(course1)

        course2 = Course.objects.create_course(
            name='course_2',
            short_name='c2_23'
        )
        self.courses.append(course2)

        self.assertTrue(Course.objects.get(short_name='c1_23') == course1)
        self.assertTrue(Course.objects.get(short_name='c2_23') == course2)
        self.assertTrue(Role.objects.filter(name='admin', course=course1).exists())
        self.assertTrue(Role.objects.filter(name='admin', course=course2).exists())
        self.assertTrue(Role.objects.get(name='admin', course=course1) == course1.admin_role)
        self.assertTrue(Role.objects.get(name='admin', course=course2) == course2.admin_role)
        self.assertTrue(Role.objects.get(name='admin', course=course1) == course1.default_role)
        self.assertTrue(Role.objects.get(name='admin', course=course2) == course2.default_role)

        for permission in Course.CourseAction.labels:
            self.assertTrue(course1.admin_role.has_permission(permission))
            self.assertTrue(course2.admin_role.has_permission(permission))

        with self.assertRaises(ValidationError):
            Course.objects.create_course(
                name='course',
                short_name='c1_23'
            )
            Course.objects.create_course(
                name='course',
                short_name='c2_23'
            )

        admin_role_1_id = Role.objects.get(name='admin', course=course1).id
        admin_role_2_id = Role.objects.get(name='admin', course=course2).id

        Course.objects.delete_course(course1)
        Course.objects.delete_course(course2)

        self.assertFalse(Course.objects.filter(short_name='c1_23').exists())
        self.assertFalse(Course.objects.filter(short_name='c2_23').exists())
        self.assertFalse(Role.objects.filter(id=admin_role_1_id).exists())
        self.assertFalse(Role.objects.filter(id=admin_role_2_id).exists())

    def test_course_creation_deletion(self) -> None:
        """
        Tests the creation and deletion of a course with preset roles. Creates two courses with
        different preset roles and deletes them. Checks if courses and roles are created and
        deleted, checks if the roles generated from the presets have the correct permissions.
        """
        course1 = Course.objects.create_course(
            name='course_1',
            short_name='c1_23',
            role_presets=[self.role_preset_1]
        )
        self.courses.append(course1)

        course2 = Course.objects.create_course(
            name='course_2',
            short_name='c2_23',
            role_presets=[self.role_preset_1, self.role_preset_2]
        )
        self.courses.append(course2)

        for role_name in ['admin', self.role_preset_1.name]:
            self.assertTrue(Role.objects.filter(name=role_name, course=course1).exists())

        for role_name in ['admin', self.role_preset_1.name, self.role_preset_2.name]:
            self.assertTrue(Role.objects.filter(name=role_name, course=course2).exists())

        role_1_1 = Role.objects.get(name=self.role_preset_1.name, course=course1)
        role_1_2 = Role.objects.get(name=self.role_preset_1.name, course=course2)
        role_2_2 = Role.objects.get(name=self.role_preset_2.name, course=course2)

        self.assertTrue(Role.objects.get(name='admin', course=course1) == course1.admin_role)
        self.assertTrue(Role.objects.get(name='admin', course=course2) == course2.admin_role)
        self.assertTrue(role_1_1 == course1.default_role)
        self.assertTrue(role_1_2 == course2.default_role)

        for permission in self.role_preset_1.permissions.all():
            self.assertTrue(role_1_1.has_permission(permission))
            self.assertTrue(role_1_2.has_permission(permission))

        for permission in [perm.codename for perm in self.role_preset_2.permissions.all()]:
            self.assertTrue(role_2_2.has_permission(permission))

        role_1_1_id = role_1_1.id
        role_1_2_id = role_1_2.id
        role_2_2_id = role_2_2.id

        Course.objects.delete_course(course1)
        Course.objects.delete_course(course2)

        self.assertFalse(Role.objects.filter(id=role_1_1_id).exists())
        self.assertFalse(Role.objects.filter(id=role_1_2_id).exists())
        self.assertFalse(Role.objects.filter(id=role_2_2_id).exists())

    def test_course_creation_deletion_with_members(self) -> None:
        pass


class UserTest(TestCase):
    pass
