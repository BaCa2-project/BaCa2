from django.test import TestCase
from django.contrib.auth.models import Group
from django.utils import timezone

from main.models import (User, Course)


class CourseTest(TestCase):
    """
    Contains tests for the Course manager and the Course model related to course creation, deletion
    and management.
    """
    user1 = None
    teacher1 = None
    teacher2 = None
    teacher3 = None
    student1 = None
    student2 = None
    users = None

    course1 = None
    courses = None

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
        cls.user1 = User.objects.create_user(email="user1@mail.com",
                                             password="user1",
                                             first_name="Jan",
                                             last_name="Kowalski")
        cls.teacher1 = User.objects.create_user(email="teacher1@uj.edu.pl",
                                                password="teacher1",
                                                first_name="Arkadiusz",
                                                last_name="Sokołowski")
        cls.teacher2 = User.objects.create_user(email="teacher2@uj.edu.pl",
                                                password="teacher2",
                                                first_name="Michał",
                                                last_name="Mnich")
        cls.teacher3 = User.objects.create_user(email="teacher3@uj.edu.pl",
                                                password="teacher3",
                                                first_name="Jarosław",
                                                last_name="Hryszka")
        cls.student1 = User.objects.create_user(email="student1@student.uj.edu.pl",
                                                password="student1",
                                                first_name="Bartosz",
                                                last_name="Deptuła")
        cls.student2 = User.objects.create_user(email="student2@student.uj.edu.pl",
                                                password="student2",
                                                first_name="Mateusz",
                                                last_name="Kadula")
        cls.users = [cls.user1, cls.teacher1, cls.teacher2, cls.teacher3, cls.student1,
                     cls.student2]

        cls.course1 = Course.objects.create_course(name="Course 1")
        cls.courses = [cls.course1]

    @classmethod
    def tearDownClass(cls):
        for user in cls.users:
            User.objects.delete_user(user)
        for course in cls.courses:
            Course.objects.delete_course(course)

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

    def test_course_create_delete_advanced(self):
        """
        Tests if course creation and deletion works properly with custom role creation and
        course member assignment.
        """
        roles = {'lab_teachers': ['view_round', 'change_round', 'view_task', 'change_task',
                                  'view_testset', 'change_testset', 'view_test', 'change_test',
                                  'view_submit', 'add_submit', 'view_result']}
        course_members = {'staff': [self.teacher1.id],
                          'lab_teachers': [self.teacher2.id, self.teacher3.id],
                          'students': [self.student1.id, self.student2.id]}

        course1 = Course.objects.create_course(name="Java Programming",
                                               usos_course_code="WMI.II-PwJ-S",
                                               usos_term_code="23/24Z",
                                               roles=roles,
                                               default_role="students",
                                               create_basic_roles=True,
                                               course_members=course_members)

        self.assertTrue(self.course_exists("Java Programming"))
        self.assertTrue(len(course1.roles()) == 4)
        self.assertEqual(course1.default_role_name, "students")
        self.assertEqual(course1.short_name, "wmi_ii_pwj_s_23_24z")

        for role in ["lab_teachers", "students", "staff", "admin"]:
            self.assertTrue(course1.role_exists(role))

        for user in [self.teacher1, self.teacher2, self.teacher3, self.student1, self.student2]:
            self.assertTrue(course1.user_is_member(user))

        for user in [self.teacher2, self.teacher3]:
            self.assertTrue(course1.user_has_role(user, "lab_teachers"))
        for user in [self.student1, self.student2]:
            self.assertTrue(course1.user_has_role(user, "students"))
        self.assertTrue(course1.user_has_role(self.teacher1, "staff"))

        for perm in course1.get_role_permissions("lab_teachers"):
            self.assertTrue(perm.codename in roles["lab_teachers"])

        for user in [self.teacher2, self.teacher3]:
            self.assertTrue(user in course1.get_users_with_permission('change_task'))

        Course.objects.delete_course(course1)

        self.assertFalse(self.course_exists("Java Programming"))
        for role in ["lab_teachers", "students", "staff", "admin"]:
            self.assertFalse(self.role_exists(role, "wmi_ii_pwj_s_23_24z"))

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

    def test_course_add_remove_user(self):
        """
        Test whether adding and removing users from a course works properly. Checks if users are
        assigned with proper roles and if exceptions are raised when attempting to add already
        added users or remove non-member users from a course.
        """
        self.course1.add_user(self.teacher1, "staff")
        self.course1.add_user(self.student1, "students")

        self.assertTrue(self.course1.user_is_member(self.teacher1))
        self.assertTrue(self.course1.user_is_member(self.student1))
        self.assertTrue(self.course1.user_has_role(self.teacher1, "staff"))
        self.assertTrue(self.course1.user_has_role(self.student1, "students"))

        with self.assertRaises(Course.CourseMemberError):
            self.course1.add_user(self.teacher1, "staff")
        with self.assertRaises(Course.CourseMemberError):
            self.course1.add_user(self.student1, "students")

        self.course1.remove_user(self.teacher1)
        self.course1.remove_user(self.student1)

        self.assertFalse(self.course1.user_is_member(self.teacher1))
        self.assertFalse(self.course1.user_is_member(self.student1))

        with self.assertRaises(Course.CourseMemberError):
            self.course1.remove_user(self.teacher1)
        with self.assertRaises(Course.CourseMemberError):
            self.course1.remove_user(self.student1)

    def test_change_role(self):
        """
        Test whether changing user's role in a course works properly. Checks if exceptions are
        raised when attempting to change role of a non-member user.
        """
        self.course1.add_user(self.teacher1, "staff")
        self.course1.change_user_role(self.teacher1, "admin")

        self.assertTrue(self.course1.user_has_role(self.teacher1, "admin"))
        self.assertFalse(self.course1.user_has_role(self.teacher1, "staff"))

        self.course1.remove_user(self.teacher1)

        with self.assertRaises(Course.CourseMemberError):
            self.course1.change_user_role(self.teacher1, "staff")

    def test_add_remove_role(self):
        """
        Test whether adding and removing roles from a course works properly. Checks if exceptions
        are raised when attempting to add already added roles or remove non-existing or protected
        roles.
        """
        pass