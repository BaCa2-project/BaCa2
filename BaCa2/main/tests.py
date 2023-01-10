from django.test import TestCase


class CoursePermissionsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        from .models import User, Course
        from django.contrib.auth.models import Group

        cls.test_user = User.objects.create_user(
            'user@gmail.com',
            'user',
            'psswd',
            first_name='first_name',
            last_name='last_name'
        )

        cls.test_course = Course.objects.create(
            name='test_course',
            short_name='t_course'
        )

        cls.test_group = Group.objects.create(
            name='test_group'
        )

    @classmethod
    def tearDownClass(cls):
        cls.test_user.delete()
        cls.test_course.delete()
        cls.test_group.delete()

    def test_course_permission(self):
        from .models import GroupCourse, UserCourse
        from course.models import Task
        from django.contrib.auth.models import Permission
        from BaCa2.choices import PermissionTypes

        test_group_course = GroupCourse.objects.create(
            course=self.test_course,
            group=self.test_group
        )

        test_user_course = UserCourse.objects.create(
            course=self.test_course,
            user=self.test_user,
            group_course=test_group_course
        )

        self.test_group.permissions.add(Permission.objects.get(codename='view_task'))

        self.assertTrue(
            self.test_user.check_course_permissions(
                self.test_course,
                Task,
                PermissionTypes.VIEW
            )
        )

    def test_general_permission(self):
        from django.contrib.auth.models import Permission, Group, ContentType
        from course.models import Task
        from BaCa2.choices import PermissionTypes

        self.test_group.user_set.add(self.test_user)
        permissions_list = Permission.objects.filter(
            content_type__model=Task
        )
        for perm in permissions_list:
            self.test_group.permissions.add(perm)

        self.assertTrue(
            self.test_user.check_general_permissions(
                Task,
                PermissionTypes.DEL
            )
        )
