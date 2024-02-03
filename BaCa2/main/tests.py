from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import TestCase
from django.utils import timezone

from course.models import Round, Submit, Task
from course.routing import InCourse
from main.models import Course, Role, RolePreset, User
from package.models import PackageInstance


class CourseTest(TestCase):
    """
    Tests the creation and deletion of courses.
    """

    course_1 = None
    course_2 = None
    role_preset_1 = None
    role_preset_2 = None
    role_1 = None
    role_2 = None
    user_1 = None
    user_2 = None
    user_3 = None
    models = []

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
            cls.models.append(cls.role_preset_1)

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
            cls.models.append(cls.role_preset_2)

            cls.role_1 = Role.objects.create_role(
                name='role_1',
                permissions=[
                    Course.CourseAction.VIEW_ROLE.label,
                    Course.CourseAction.VIEW_MEMBER.label,
                    Course.BasicAction.VIEW.label,
                    Course.BasicAction.EDIT.label
                ]
            )
            cls.models.append(cls.role_1)

            cls.role_2 = Role.objects.create_role(
                name='role_2',
                permissions=[
                    Course.CourseAction.VIEW_ROLE.label,
                    Course.CourseAction.VIEW_MEMBER.label,
                    Course.BasicAction.VIEW.label,
                    Course.BasicAction.EDIT.label,
                    Course.CourseAction.ADD_MEMBER.label,
                    Course.CourseAction.EDIT_ROLE.label
                ]
            )
            cls.models.append(cls.role_2)

            cls.user_1 = User.objects.create_user(
                email='user_1@uj.edu.pl',
                password='password',
                first_name='name_1',
                last_name='surname_1',
            )
            cls.models.append(cls.user_1)

            cls.user_2 = User.objects.create_user(
                email='user_2@uj.edu.pl',
                password='password',
                first_name='name_2',
                last_name='surname_2',
            )
            cls.models.append(cls.user_2)

            cls.user_3 = User.objects.create_user(
                email='user3@uj.edu.pl',
                password='password',
                first_name='name_3',
                last_name='surname_3',
            )
            cls.models.append(cls.user_3)

            cls.course_1 = Course.objects.create_course(
                name='Design Patterns',
                usos_course_code='WMI.II-WP-S',
                usos_term_code='23/24Z',
                role_presets=[cls.role_preset_1, cls.role_preset_2]
            )
            cls.models.append(cls.course_1)

            cls.course_2 = Course.objects.create_course(
                name='Software Testing',
                usos_course_code='WMI.II-TO-S',
                usos_term_code='23/24Z',
                role_presets=[cls.role_preset_2]
            )
            cls.models.append(cls.course_2)

    @classmethod
    def tearDownClass(cls) -> None:
        with transaction.atomic():
            for model in [model for model in cls.models if model.id is not None]:
                model.delete()

    @classmethod
    def reset_roles(cls) -> None:
        cls.role_1.course = None
        cls.role_1.save()
        cls.role_2.course = None
        cls.role_2.save()

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
        self.models.append(course1)

        course2 = Course.objects.create_course(
            name='course_2',
            short_name='c2_23'
        )
        self.models.append(course2)

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
            name='course_3',
            short_name='c3_23',
            role_presets=[self.role_preset_1]
        )
        self.models.append(course1)

        course2 = Course.objects.create_course(
            name='course_4',
            short_name='c4_23',
            role_presets=[self.role_preset_1, self.role_preset_2]
        )
        self.models.append(course2)

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

        course1.delete()
        course2.delete()

        self.assertFalse(Role.objects.filter(id=role_1_1_id).exists())
        self.assertFalse(Role.objects.filter(id=role_1_2_id).exists())
        self.assertFalse(Role.objects.filter(id=role_2_2_id).exists())

    def test_course_creation_deletion_with_members(self) -> None:
        """
        Tests the creation and deletion of a course with preset roles and members. Creates a course
        with two preset roles and adds three members to it. Checks if the course is deleted
        correctly and makes sure that the members are not deleted with the course.
        """
        course1 = Course.objects.create_course(
            name='course_5',
            short_name='c5_23',
            role_presets=[self.role_preset_1, self.role_preset_2]
        )
        self.models.append(course1)

        course1.add_member(self.user_1.email, self.role_preset_1.name)
        course1.add_member(self.user_2, self.role_preset_2.name)
        course1.add_member(self.user_3.id, self.role_preset_2.name)

        self.assertTrue(course1.user_is_member(self.user_1))
        self.assertTrue(course1.user_is_member(self.user_2.id))
        self.assertTrue(course1.user_is_member(self.user_3.email))

        user_1_id = self.user_1.id
        user_2_id = self.user_2.id
        user_3_id = self.user_3.id

        course1.delete()

        self.assertFalse(Course.objects.filter(short_name='c5_23').exists())
        self.assertTrue(User.objects.filter(id=user_1_id).exists())
        self.assertTrue(User.objects.filter(id=user_2_id).exists())
        self.assertTrue(User.objects.filter(id=user_3_id).exists())

    def test_course_short_name_generation(self) -> None:
        """
        Tests the generation of a course short_name. Creates three courses, one with and two without
        USOS codes. Checks if the short_name is generated correctly for all three. Asserts that
        ValidationError is raised when trying to create a course with USOS codes that are already
        in use or when one of the codes was provided without the other.
        """
        curr_year = timezone.now().year

        course1 = Course.objects.create_course(
            name='Advanced Design Patterns',
        )
        self.models.append(course1)

        course2 = Course.objects.create_course(
            name='Advanced Design Patterns'
        )
        self.models.append(course2)

        course3 = Course.objects.create_course(
            name='Advanced Design Patterns',
            usos_course_code='WMI.II.ZWPiA-S',
            usos_term_code='23/24Z'
        )
        self.models.append(course3)

        self.assertTrue(Course.objects.get(short_name=f'adp_{curr_year}') == course1)
        self.assertTrue(Course.objects.get(short_name=f'adp_{curr_year}_2') == course2)
        self.assertTrue(Course.objects.get(short_name='wmi_ii_zwpia_s__23_24z') == course3)

        with self.assertRaises(ValidationError):
            Course.objects.create_course(
                name='Advanced Design Patterns',
                usos_course_code='WMI.II.ZWPiA-S',
            )

        with self.assertRaises(ValidationError):
            Course.objects.create_course(
                name='Advanced Design Patterns',
                usos_term_code='23/24Z',
            )

        with self.assertRaises(ValidationError):
            Course.objects.create_course(
                name='Advanced Design & Architectural Patterns',
                usos_course_code='WMI.II.ZWPiA-S',
                usos_term_code='23/24Z',
            )

        for course in [course1, course2, course3]:
            Course.objects.delete_course(course)

    def test_course_add_role(self) -> None:
        """
        Tests the addition of a new roles to a course. Adds a new role to the course in three
        different ways and checks if the role was added correctly. Checks if appropriate exceptions
        are raised when attempting to add roles already existing in the course, roles with duplicate
        names, or roles assigned to other courses.
        """
        self.reset_roles()

        role_preset_3 = RolePreset.objects.create_role_preset(
            name='role_preset_3',
            permissions=[Course.CourseAction.VIEW_MEMBER.label,
                         Course.BasicAction.VIEW.label]
        )
        self.models.append(role_preset_3)

        new_role_1 = Role.objects.create_role(
            name='new_role_1',
            permissions=[Course.CourseAction.VIEW_MEMBER.label,
                         Course.BasicAction.VIEW.label,
                         Course.BasicAction.EDIT.label]
        )
        self.models.append(new_role_1)

        self.course_1.create_role_from_preset(role_preset_3)
        self.course_1.add_role(new_role_1)
        self.course_1.create_role('new_role_2', [Course.BasicAction.EDIT.label])

        self.assertTrue(self.course_1.role_exists(role_preset_3.name))
        self.assertTrue(self.course_1.role_exists(new_role_1.name))
        self.assertTrue(self.course_1.role_exists('new_role_2'))

        with self.assertRaises(Course.CourseRoleError):
            self.course_1.create_role_from_preset(role_preset_3)

        with self.assertRaises(Course.CourseRoleError):
            self.course_1.add_role(new_role_1)

        with self.assertRaises(Course.CourseRoleError):
            self.course_1.create_role('new_role_2', [Course.BasicAction.VIEW.label])

        new_role_3 = Role.objects.create_role(
            name='new_role_3',
            permissions=[Course.CourseAction.VIEW_MEMBER.label, Course.BasicAction.VIEW.label]
        )
        self.models.append(new_role_3)

        self.course_2.add_role(new_role_3)

        with self.assertRaises(Course.CourseRoleError):
            self.course_1.add_role(new_role_3)

    def test_course_remove_role(self) -> None:
        """
        Tests the removal of roles from a course. Checks if roles are correctly removed and if
        appropriate exceptions are raised when attempting to remove the admin or default role,
        a role not assigned to the course or a role with users assigned to it.
        """
        self.reset_roles()

        self.course_1.add_role(self.role_1)
        self.course_1.add_role(self.role_2)
        self.course_1.add_member(self.user_1, self.role_2)
        self.course_1.add_member(self.user_2, self.role_2)
        self.course_1.add_member(self.user_3, self.role_2)

        role_1_id = self.role_1.id
        role_2_id = self.role_2.id
        admin_role_id = self.course_1.admin_role.id
        default_role_id = self.course_1.default_role.id

        self.course_1.remove_role(self.role_1)

        self.assertFalse(self.course_1.role_exists(role_1_id))
        self.assertFalse(Role.objects.filter(id=role_1_id).exists())

        with self.assertRaises(Course.CourseRoleError):
            self.course_1.remove_role(admin_role_id)

        with self.assertRaises(Course.CourseRoleError):
            self.course_1.remove_role(default_role_id)

        with self.assertRaises(Course.CourseRoleError):
            self.course_1.remove_role(role_2_id)

        self.course_1.remove_member(self.user_1.email)
        self.course_1.change_member_role(self.user_2.id, self.course_1.default_role.name)
        self.course_1.make_member_admin(self.user_3)

        self.course_1.remove_role(role_2_id)

        self.assertFalse(self.course_1.role_exists(role_2_id))
        self.assertFalse(Role.objects.filter(id=role_2_id).exists())

    def test_course_add_role_permissions(self) -> None:
        """
        Tests the addition of permissions to roles. Checks if permissions are correctly added and
        if appropriate exceptions are raised when attempting to add permissions to roles which are
        not assigned to the course or when attempting to add permissions already assigned to the
        given role.
        """
        self.reset_roles()

        permissions = [Course.CourseAction.ADD_MEMBER.label,
                       Course.CourseAction.EDIT_ROLE.label,
                       Course.CourseAction.DEL_ROLE.label]

        self.course_1.add_role(self.role_1)
        self.course_1.add_role_permissions(self.role_1.id, permissions)

        for perm in permissions:
            self.assertTrue(self.course_1.role_has_permission(self.role_1.name, perm))

        with self.assertRaises(Course.CourseRoleError):
            self.course_1.add_role_permissions(self.role_2.id, [Course.CourseAction.DEL_ROLE.label])

        with self.assertRaises(Role.RolePermissionError):
            self.course_1.add_role_permissions(self.role_1, [Course.CourseAction.EDIT_ROLE.label])

    def test_course_remove_role_permissions(self) -> None:
        """
        Tests removal of permission from a role. Checks if permissions are correctly removed and if
        appropriate exceptions are raised when attempting to remove permissions from roles which
        are not assigned to the course, from roles which do not have the given permissions or from
        admin roles.
        """
        self.reset_roles()

        permissions = [Course.CourseAction.ADD_MEMBER.label,
                       Course.CourseAction.EDIT_ROLE.label]

        self.course_2.add_role(self.role_2)

        self.assertTrue(self.course_2.role_has_permission(
            'role_preset_2',
            Course.CourseAction.ADD_MEMBER.label
        ))

        for perm in permissions:
            self.assertTrue(self.course_2.role_has_permission(self.role_2.id, perm))

        self.course_2.remove_role_permissions(
            'role_preset_2',
            [Course.CourseAction.ADD_MEMBER.label]
        )
        self.course_2.remove_role_permissions(
            self.role_2,
            permissions
        )

        self.assertFalse(self.course_2.role_has_permission(
            'role_preset_2',
            Course.CourseAction.ADD_MEMBER.label
        ))

        for perm in permissions:
            self.assertFalse(self.course_2.role_has_permission(self.role_2, perm))

        with self.assertRaises(Course.CourseRoleError):
            self.course_2.remove_role_permissions(self.role_1, [Course.BasicAction.VIEW.label])

        with self.assertRaises(Role.RolePermissionError):
            self.course_2.remove_role_permissions(self.role_2, permissions)

        with self.assertRaises(Course.CourseRoleError):
            self.course_2.remove_role_permissions(self.course_2.admin_role.name, permissions)

    def test_course_change_role_permissions(self) -> None:
        """
        Tests changing permissions of a role. Checks if permissions are correctly changed and if
        appropriate exceptions are raised when attempting to change permissions of roles which are
        not assigned to the course or admin roles.
        """
        self.reset_roles()

        role_1_permissions = [Course.CourseAction.VIEW_ROLE.label,
                              Course.CourseAction.VIEW_MEMBER.label,
                              Course.BasicAction.VIEW.label]

        role_1_new_permissions = [Course.CourseAction.ADD_MEMBER.label,
                                  Course.CourseAction.EDIT_ROLE.label,
                                  Course.BasicAction.VIEW.label]

        self.course_1.add_role(self.role_1)

        for perm in role_1_permissions:
            self.assertTrue(self.course_1.role_has_permission(self.role_1, perm))

        for perm in list(set(role_1_new_permissions) - set(role_1_permissions)):
            self.assertFalse(self.course_1.role_has_permission(self.role_1, perm))

        self.course_1.change_role_permissions(self.role_1.name, role_1_new_permissions)

        for perm in role_1_new_permissions:
            self.assertTrue(self.course_1.role_has_permission(self.role_1.id, perm))

        for perm in list(set(role_1_permissions) - set(role_1_new_permissions)):
            self.assertFalse(self.course_1.role_has_permission(self.role_1, perm))

        with self.assertRaises(Course.CourseRoleError):
            self.course_1.change_role_permissions(self.role_2, role_1_permissions)

        with self.assertRaises(Course.CourseRoleError):
            self.course_1.change_role_permissions(self.course_1.admin_role.id, role_1_permissions)

    # def test_course_add_remove_member(self) -> None:
    #     """
    #     Tests addition and removal of members to a course. Checks if members are correctly added
    #     and removed from the course and if appropriate exceptions are raised when attempting to
    #     add members which are already assigned to the course, when attempting to add members with
    #     roles which are not assigned to the course, when attempting to add members to admin roles
    #     or when attempting to remove members who are not assigned to the course.
    #     """
    #     self.reset_roles()
    #
    #     course_a = Course.objects.create_course(name='course_1')
    #     self.models.append(course_a)
    #     course_b = Course.objects.create_course(name='course_2')
    #     self.models.append(course_b)
    #
    #     course_a.add_role(self.role_1)
    #     course_a.add_role(self.role_2)
    #     course_b.create_role_from_preset(self.role_preset_1)
    #     course_b.create_role_from_preset(self.role_preset_2)
    #
    #     for user in [self.user_1, self.user_2, self.user_3]:
    #         self.assertFalse(course_a.user_is_member(user.id))
    #         self.assertFalse(course_b.user_is_member(user.email))
    #
    #     course_a.add_member(self.user_1, self.role_1.name)
    #     course_a.add_members([self.user_2.id, self.user_3.id], self.role_2)
    #     course_b.add_member(self.user_1, self.role_preset_1.name)
    #     course_b.add_member(self.user_2, self.role_preset_2.name)
    #
    #     for user in [self.user_1, self.user_2, self.user_3]:
    #         self.assertTrue(course_a.user_is_member(user.id))
    #
    #     for user in [self.user_1, self.user_2]:
    #         self.assertTrue(course_b.user_is_member(user))
    #
    #     self.assertTrue(course_a.user_has_role(self.user_1.id, self.role_1.name))
    #     self.assertTrue(course_a.user_has_role(self.user_2.email, self.role_2.id))
    #     self.assertTrue(course_a.user_has_role(self.user_3, self.role_2))
    #     self.assertTrue(course_b.user_has_role(self.user_1, self.role_preset_1.name))
    #     self.assertTrue(course_b.user_has_role(self.user_2, self.role_preset_2.name))
    #
    #     for perm in self.role_1.permissions.all():
    #         self.assertTrue(self.user_1.has_course_permission(perm, course_a.short_name))
    #
    #     for perm in self.role_preset_1.permissions.all():
    #         self.assertTrue(self.user_1.has_course_permission(perm.codename, course_b))
    #
    #     with self.assertRaises(Course.CourseMemberError):
    #         course_a.add_member(self.user_1, self.role_1)
    #
    #     with self.assertRaises(Course.CourseMemberError):
    #         course_a.add_member(self.user_1, self.role_2.name)
    #
    #     with self.assertRaises(Course.CourseRoleError):
    #         course_b.add_member(self.user_3, self.role_1.id)
    #
    #     with self.assertRaises(Course.CourseRoleError):
    #         course_b.add_member(self.user_3, self.course_2.admin_role)
    #
    #     for user in [self.user_1, self.user_2, self.user_3]:
    #         course_a.remove_member(user)
    #     course_b.remove_members([self.user_1.id, self.user_2.id])
    #
    #     for user in [self.user_1, self.user_2, self.user_3]:
    #         self.assertFalse(course_a.user_is_member(user))
    #         self.assertFalse(course_b.user_is_member(user))
    #
    #     with self.assertRaises(Course.CourseMemberError):
    #         course_a.remove_member(self.user_1)
    #
    #     with self.assertRaises(Course.CourseMemberError):
    #         self.user_1.has_course_permission(self.role_1.permissions.all()[0], course_a)

    def test_add_remove_admin(self) -> None:
        """
        Tests addition and removal of admins to a course. Checks if admins are correctly added
        and removed from the course and if appropriate exceptions are raised when attempting to
        add admins which are already assigned to the course or when attempting to remove admins
        using the remove_member method.
        """
        self.reset_roles()

        course_a = Course.objects.create_course(name='course_1')
        self.models.append(course_a)

        for user in [self.user_1, self.user_2]:
            self.assertFalse(course_a.user_is_member(user))
            self.assertFalse(course_a.user_is_admin(user))

        course_a.add_role(self.role_1)
        course_a.add_member(self.user_1.id, self.role_1.name)
        course_a.add_admin(self.user_2.id)

        for user in [self.user_1, self.user_2]:
            self.assertTrue(course_a.user_is_member(user))

        self.assertTrue(course_a.user_is_admin(self.user_2))
        self.assertFalse(course_a.user_is_admin(self.user_1))

        with self.assertRaises(Course.CourseMemberError):
            course_a.remove_member(self.user_2)

        with self.assertRaises(Course.CourseMemberError):
            course_a.remove_admin(self.user_1)

        course_a.remove_admin(self.user_2)
        course_a.remove_member(self.user_1)

        for user in [self.user_1, self.user_2]:
            self.assertFalse(course_a.user_is_member(user))
            self.assertFalse(course_a.user_is_admin(user))

    # def test_change_member_role(self) -> None:
    #     """
    #     Tests changing the role of a member. Checks if the role is correctly changed and if
    #     appropriate exceptions are raised when attempting to change the role of members which are
    #     not assigned to the course, when attempting to change the role of members to roles which
    #     are not assigned to the course, when attempting to change the role of members to the admin
    #     role or when attempting to change the role of an admin.
    #     """
    #     self.reset_roles()
    #
    #     course_a = Course.objects.create_course(name='course_1')
    #     self.models.append(course_a)
    #     course_a.add_role(self.role_1)
    #     course_a.add_role(self.role_2)
    #     course_a.add_members([self.user_1.id, self.user_2.id, self.user_3.id], self.role_1)
    #
    #     for user in [self.user_1, self.user_2, self.user_3]:
    #         self.assertTrue(course_a.user_is_member(user))
    #         self.assertTrue(course_a.user_has_role(user, self.role_1))
    #         self.assertFalse(course_a.user_is_admin(user))
    #
    #     course_a.change_member_role(self.user_1, self.role_2)
    #     course_a.change_members_role([self.user_2.id, self.user_3.id], self.role_2)
    #
    #     for user in [self.user_1, self.user_2, self.user_3]:
    #         self.assertTrue(course_a.user_is_member(user))
    #         self.assertTrue(course_a.user_has_role(user, self.role_2))
    #         self.assertFalse(course_a.user_is_admin(user))
    #
    #     course_a.remove_member(self.user_1)
    #
    #     with self.assertRaises(Course.CourseMemberError):
    #         course_a.change_member_role(self.user_1, self.role_1)
    #
    #     course_a.remove_role(self.role_1)
    #
    #     with self.assertRaises(Course.CourseRoleError):
    #         course_a.change_member_role(self.user_2, self.role_1)
    #
    #     with self.assertRaises(Course.CourseRoleError):
    #         course_a.change_member_role(self.user_2, self.course_1.admin_role)
    #
    #     course_a.add_admin(self.user_1)
    #
    #     with self.assertRaises(Course.CourseRoleError):
    #         course_a.change_member_role(self.user_1, self.role_2)


class TestCourseActions(TestCase):
    course_1 = None
    user_1 = None

    @classmethod
    def setUpTestData(cls):
        cls.course_1 = Course.objects.create_course(
            name='Design Patterns 2',
        )
        cls.user_1 = User.objects.create_user(
            email='test@test.com',
            password='test'
        )

    @classmethod
    def tearDownClass(cls):
        cls.course_1.delete()
        cls.user_1.delete()

    def tearDown(self):
        with InCourse(self.course_1):
            Round.objects.all().delete()
            Task.objects.all().delete()
            Submit.objects.all().delete()

    def new_round(self, name=None):
        round_ = self.course_1.create_round(
            start_date=timezone.now() - timezone.timedelta(days=1),
            deadline_date=timezone.now() + timezone.timedelta(days=1),
            name=name
        )
        return round_

    @staticmethod
    def get_pkg(name='dosko'):
        pkgs = PackageInstance.objects.filter(package_source__name=name).all()
        if len(pkgs) == 0:
            return PackageInstance.objects.create_source_and_instance(name, '1')
        else:
            return pkgs[0]

    def new_task(self, round_, name='Liczby Doskonałe'):
        pkg = self.get_pkg()
        task = self.course_1.create_task(
            package_instance=pkg,
            round_=round_,
            task_name=name,
            points=10,
        )
        return task

    def new_submit(self, task, user):
        submit = self.course_1.create_submit(
            task=task,
            user=user,
            source_code='1234.cpp',
            auto_send=False
        )
        return submit

    def test_01_create_round(self):
        self.new_round('round_1')
        self.assertEqual(len(self.course_1.rounds()), 1)
        self.assertEqual(self.course_1.rounds()[0].name, 'round_1')

    def test_02_delete_round(self):
        r = self.new_round()
        with InCourse(self.course_1):
            self.assertEqual(len(Round.objects.all()), 1)
        self.course_1.delete_round(r.pk)
        with InCourse(self.course_1):
            self.assertEqual(len(Round.objects.all()), 0)

    def test_03_get_round(self):
        r1 = self.new_round('test 1')
        r2 = self.new_round('test 2')
        self.assertEqual(self.course_1.get_round(r1.pk), r1)
        self.assertEqual(self.course_1.get_round(r2.pk), r2)

    def test_04_create_task(self):
        self.new_task(self.new_round())
        r = self.course_1.rounds()[0]
        self.assertEqual(len(r.tasks), 1)
        t = r.tasks[0]
        self.assertEqual(t.task_name, 'Liczby Doskonałe')
        self.assertEqual(len(t.sets), 4)

    def test_05_get_task(self):
        t = self.new_task(self.new_round())
        self.assertEqual(self.course_1.get_task(t.pk), t)
        self.assertEqual(self.course_1.get_task(t), t)

    def test_06_delete_task(self):
        t = self.new_task(self.new_round())
        r = self.course_1.rounds()[0]
        self.assertEqual(len(r.tasks), 1)
        self.course_1.delete_task(t.pk)
        self.assertEqual(len(r.tasks), 0)

    def test_07_create_submit(self):
        t = self.new_task(self.new_round())
        self.new_submit(t, self.user_1)
        self.assertEqual(len(t.submits()), 1)
        s = t.submits()[0]
        self.assertEqual(s.user, self.user_1)

    def test_08_delete_submit(self):
        t = self.new_task(self.new_round())
        s = self.new_submit(t, self.user_1)
        self.assertEqual(len(t.submits()), 1)
        self.course_1.delete_submit(s.pk)
        self.assertEqual(len(t.submits()), 0)


class UserTest(TestCase):
    pass
