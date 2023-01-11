from django.test import TestCase
from django.contrib.auth.models import Group, Permission, ContentType
from .models import User, Course, GroupCourse, UserCourse
from course.models import Task
from BaCa2.choices import PermissionTypes


class CoursePermissionsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_user1 = User.objects.create_user(
            'user1@gmail.com',
            'user1',
            'psswd',
            first_name='first_name',
            last_name='last_name'
        )
        cls.test_user2 = User.objects.create_user(
            'user2@gmail.com',
            'user2',
            'psswd',
            first_name='first_name',
            last_name='last_name'
        )

        cls.test_course = Course.objects.create(
            name='test_course',
            short_name='t_course'
        )

        cls.test_group1 = Group.objects.create(
            name='test_group1'
        )
        cls.test_group2 = Group.objects.create(
            name='test_group2'
        )

    @classmethod
    def tearDownClass(cls):
        cls.test_user1.delete()
        cls.test_user2.delete()
        cls.test_course.delete()
        cls.test_group1.delete()
        cls.test_group2.delete()

    def test_access_course(self):
        test_group_course1 = GroupCourse.objects.create(
            course=self.test_course,
            group=self.test_group1
        )
        UserCourse.objects.create(
            course=self.test_course,
            user=self.test_user1,
            group_course=test_group_course1
        )

        self.assertTrue(
            self.test_user1.can_access_course(self.test_course)
        )
        self.assertFalse(
            self.test_user2.can_access_course(self.test_course)
        )

    def test_general_permissions(self):
        self.test_group1.user_set.add(self.test_user1)
        self.test_group1.user_set.add(self.test_user2)
        self.test_group2.user_set.add(self.test_user1)

        self.test_group1.permissions.add(
            Permission.objects.get(codename='view_group')
        )
        self.test_group1.permissions.add(
            Permission.objects.get(codename='change_group')
        )
        self.test_group2.permissions.add(
            Permission.objects.get(codename='add_group')
        )
        self.test_group2.permissions.add(
            Permission.objects.get(codename='delete_group')
        )

        self.assertTrue(
            self.test_user1.check_general_permissions(
                Group,
                PermissionTypes.VIEW
            )
        )
        self.assertTrue(
            self.test_user2.check_general_permissions(
                Group,
                PermissionTypes.VIEW
            )
        )
        self.assertFalse(
            self.test_user2.check_general_permissions(
                Group,
                PermissionTypes.DEL
            )
        )
        self.assertTrue(
            self.test_user1.check_general_permissions(
                Group,
                [PermissionTypes.VIEW, PermissionTypes.EDIT]
            )
        )
        self.assertFalse(
            self.test_user2.check_general_permissions(
                Group,
                [PermissionTypes.VIEW, PermissionTypes.EDIT, PermissionTypes.ADD]
            )
        )
        self.assertTrue(
            self.test_user1.check_general_permissions(
                Group,
                'all'
            )
        )
        self.assertTrue(
            self.test_user1.check_general_permissions(
                Group,
                'all_standard'
            )
        )
        self.assertFalse(
            self.test_user2.check_general_permissions(
                Group,
                'all'
            )
        )
        self.assertTrue(
            self.test_user1.check_general_permissions(
                Group,
                'auth.view_group'
            )
        )
        self.assertFalse(
            self.test_user1.check_general_permissions(
                Group,
                'auth.custom_permission'
            )
        )

    def test_course_permissions(self):
        test_group_course1 = GroupCourse.objects.create(
            course=self.test_course,
            group=self.test_group1
        )
        test_group_course2 = GroupCourse.objects.create(
            course=self.test_course,
            group=self.test_group2
        )

        UserCourse.objects.create(
            course=self.test_course,
            user=self.test_user1,
            group_course=test_group_course1
        )
        UserCourse.objects.create(
            course=self.test_course,
            user=self.test_user2,
            group_course=test_group_course2
        )

        self.test_group2.permissions.add(
            Permission.objects.get(codename='view_task')
        )
        self.test_group2.permissions.add(
            Permission.objects.get(codename='change_task')
        )

        for p in Permission.objects.filter(
                content_type=ContentType.objects.get_for_model(Task).id
        ):
            self.test_group1.permissions.add(p)

        self.assertTrue(
            self.test_user1.check_course_permissions(
                self.test_course,
                Task,
                PermissionTypes.EDIT
            )
        )
        self.assertTrue(
            self.test_user2.check_course_permissions(
                self.test_course,
                Task,
                PermissionTypes.VIEW
            )
        )
        self.assertFalse(
            self.test_user2.check_course_permissions(
                self.test_course,
                Task,
                PermissionTypes.DEL
            )
        )
        self.assertTrue(
            self.test_user1.check_course_permissions(
                self.test_course,
                Task,
                [PermissionTypes.VIEW, PermissionTypes.ADD]
            )
        )
        self.assertFalse(
            self.test_user2.check_course_permissions(
                self.test_course,
                Task,
                [PermissionTypes.VIEW, PermissionTypes.ADD]
            )
        )
        self.assertTrue(
            self.test_user1.check_course_permissions(
                self.test_course,
                Task,
                'all'
            )
        )
        self.assertFalse(
            self.test_user2.check_course_permissions(
                self.test_course,
                Task,
                'all'
            )
        )
