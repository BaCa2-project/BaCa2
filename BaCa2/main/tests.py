from django.test import TestCase
from django.contrib.auth.models import Group
from django.utils import timezone

from main.models import (User, Course)


class CourseTest(TestCase):
    """
    Contains tests for the Course model and its manager.
    """

    test_user1 = None
    test_user2 = None

    @classmethod
    def setUpClass(cls):
        cls.test_user1 = User.objects.create_user(
            'user1@gmail.com',
            'user1',
            'password',
            first_name='first_name',
            last_name='last_name'
        )
        cls.test_user2 = User.objects.create_user(
            'user2@gmail.com',
            'user2',
            'password',
            first_name='first_name',
            last_name='last_name'
        )

    @classmethod
    def tearDownClass(cls):
        cls.test_user1.delete()
        cls.test_user2.delete()

    def test_course_default_create_delete(self):
        """
        Tests the default course creation and deletion, checks if the default course roles are
        created and deleted.
        """
        course = Course.objects.create_course(
            name="Test Course",
            short_name="TC_2023"
        )
        self.assertTrue(Course.objects.filter(name="Test Course").exists())
        self.assertTrue(course.role_exists("students"))
        self.assertTrue(course.role_exists("staff"))
        self.assertTrue(course.role_exists("admin"))

        Course.objects.delete_course(course)

        self.assertFalse(Course.objects.filter(name="Test Course").exists())
        self.assertFalse(Group.objects.filter(
            name=Course.create_role_name("students", "tc_2023")
        ).exists())
        self.assertFalse(Group.objects.filter(
            name=Course.create_role_name("staff", "tc_2023")
        ).exists())
        self.assertFalse(Group.objects.filter(
            name=Course.create_role_name("admin", "tc_2023")
        ).exists())

    def test_short_name_generation(self):
        """
        Tests the short name generation for courses, checks if short name is properly generated
        for multiple courses with the same name, and if the short name is properly generated for
        courses with `USOS_code` set.
        """
        course1 = Course.objects.create_course(name="Test Course 1")
        course2 = Course.objects.create_course(name="Test Course 1")
        course3 = Course.objects.create_course(name="Test Course 1")
        course4 = Course.objects.create_course(name="Test Course", usos_code="WMI.II-FIL-OL")
        year = timezone.now().year

        self.assertEqual(course1.short_name, f'tc1_{year}')
        self.assertEqual(course2.short_name, f'tc1_{year}_2')
        self.assertEqual(course3.short_name, f'tc1_{year}_3')
        self.assertEqual(course4.short_name, f'wmi_ii_fil_ol_{year}')

        for course in [course1, course2, course3, course4]:
            Course.objects.delete_course(course)
