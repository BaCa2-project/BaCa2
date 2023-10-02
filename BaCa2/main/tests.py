from django.test import TestCase
from django.contrib.auth.models import Group
from django.utils import timezone

from main.models import (User, Course)


class CourseManagerTest(TestCase):
    """
    Contains tests for the Course manager. Tests relate to the creation and deletion of courses,
    their roles and databases.
    """

    @staticmethod
    def course_exists(name) -> bool:
        """
        Simple helper function to check if a course with a given name exists.

        :param name: name of the course to check
        :type name: str

        :return: `True` if the course exists, `False` otherwise
        :rtype: bool
        """
        return Course.objects.filter(name=name).exists()

    @staticmethod
    def role_exists(role_verbose_name, course_short_name) -> bool:
        """
        Simple helper function to check if a role with given verbose name and given course short
        name exists. Does not check if the role is assigned to the course with the given short
        name, only if the role exists.

        :param role_verbose_name: verbose name of the role to check
        :type role_verbose_name: str
        :param course_short_name: short name of the course
        :type course_short_name: str

        :return: `True` if the role exists, `False` otherwise
        :rtype: bool
        """
        return Group.objects.filter(
            name=Course.create_role_name(role_verbose_name, course_short_name)
        ).exists()

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_course_default_create_delete(self):
        """
        Tests the default course creation and deletion, checks if the default course roles are
        created and deleted.
        """
        name = "Test Course"
        short_name = "tc_2023"

        course = Course.objects.create_course(
            name=name,
            short_name=short_name
        )

        self.assertTrue(self.course_exists(name))
        for role in ["students", "staff", "admin"]:
            self.assertTrue(course.role_exists(role))

        Course.objects.delete_course(course)

        self.assertFalse(self.course_exists(name))
        for role in ["students", "staff", "admin"]:
            self.assertFalse(self.role_exists(role, short_name))

    def test_course_create_delete(self):
        """
        Tests custom course creation and deletion, checks if the custom course roles are assigned
        to the course and deleted properly.
        """
        name1 = "Test Course 1"
        short_name2 = "tc1_2023"
        name2 = "Test Course 2"
        short_name1 = "tc2_2023"

        role1_1 = Group.objects.create(
            name=Course.create_role_name("role1", short_name1)
        )
        role1_2 = Group.objects.create(
            name=Course.create_role_name("role2", short_name1)
        )
        role2_1 = Group.objects.create(
            name=Course.create_role_name("role1", short_name2)
        )
        role2_2 = Group.objects.create(
            name=Course.create_role_name("role2", short_name2)
        )

        course1 = Course.objects.create_course(
            name=name1,
            short_name=short_name1,
            roles=[role1_1, role1_2],
            default_role=role1_2,
            create_basic_roles=False
        )
        course2 = Course.objects.create_course(
            name=name2,
            short_name=short_name2,
            roles=[role2_1, role2_2],
            default_role="role2",
            create_basic_roles=True
        )

        self.assertTrue(self.course_exists(name1))
        for role in ["role1", "role2", "admin"]:
            self.assertTrue(course1.role_exists(role))
        self.assertTrue(len(course1.roles()) == 3)

        self.assertTrue(self.course_exists(name2))
        for role in ["role1", "role2", "admin", "staff", "students"]:
            self.assertTrue(course2.role_exists(role))
        self.assertTrue(len(course2.roles()) == 5)

        Course.objects.delete_course(course1)
        Course.objects.delete_course(course2)

        self.assertFalse(self.course_exists(name1))
        for role in ["role1", "role2", "admin"]:
            self.assertFalse(self.role_exists(role, short_name1))

        self.assertFalse(self.course_exists(name2))
        for role in ["role1", "role2", "admin", "staff", "students"]:
            self.assertFalse(self.role_exists(role, short_name2))

    def test_short_name_generation(self):
        """
        Tests the short name generation for courses, checks if short name is properly generated
        for multiple courses with the same name, and if the short name is properly generated for
        courses with `USOS_code` set.
        """
        course1 = Course.objects.create_course(name="Test Course 3")
        course2 = Course.objects.create_course(name="Test Course 3")
        course3 = Course.objects.create_course(name="Test Course 3")
        course4 = Course.objects.create_course(name="Test Course",
                                               usos_course_code="WMI.II-FIL-OL",
                                               usos_term_code="23/24Z")
        year = timezone.now().year

        self.assertEqual(course1.short_name, f'tc3_{year}')
        self.assertEqual(course2.short_name, f'tc3_{year}_2')
        self.assertEqual(course3.short_name, f'tc3_{year}_3')
        self.assertEqual(course4.short_name, f'wmi_ii_fil_ol_23_24z')

        for course in [course1, course2, course3, course4]:
            Course.objects.delete_course(course)
