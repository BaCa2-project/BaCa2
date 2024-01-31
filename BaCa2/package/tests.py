import shutil

from django.test import TestCase

from .models import *
from main.models import User
from course.routing import InCourse
from core.settings import PACKAGES, PACKAGES_DIR
from parameterized import parameterized


class TestPackage(TestCase):
    user = None
    user2 = None

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('test@test.com', 'test')
        cls.user2 = User.objects.create_user('test2@test.com', 'test')
        cls.zip_file = PACKAGES_DIR / 'test_pkg.zip'

    def tearDown(self):
        PackageInstance.objects.all().delete()
        PackageSource.objects.all().delete()
        PackageInstanceUser.objects.all().delete()

    @parameterized.expand([(True,), (None,)])
    def test_01_create_package_instance(self, usr):
        if usr:
            usr = self.user
        pkg = PackageInstance.objects.create_source_and_instance('dosko', '1', creator=usr)
        self.assertIsInstance(pkg.package, Package)
        self.assertIn(pkg.key, PACKAGES.keys())
        self.assertEqual(pkg.package['title'], 'Liczby Doskonałe')

        if usr:
            self.assertEqual(len(pkg.permitted_users), 1)
            self.assertEqual(pkg.permitted_users[0], usr)

    @parameterized.expand([('none',), ('creator',), ('permission_pass',)])
    def test_02_create_new_commit(self, usr_mode):
        usr = None
        if usr_mode in ('creator', 'permission_pass'):
            usr = self.user
        pkg = PackageInstance.objects.create_source_and_instance('dosko', '1', creator=usr)
        if usr_mode == 'permission_pass':
            pkg.add_permitted_user(self.user2)
            self.assertEqual(len(pkg.permitted_users), 2)
        new_pkg = None
        try:
            if usr_mode == 'permission_pass':
                new_pkg = PackageInstance.objects.make_package_instance_commit(pkg)
            elif usr_mode == 'creator':
                new_pkg = PackageInstance.objects.make_package_instance_commit(
                    pkg,
                    copy_permissions=False,
                    creator=self.user2,
                )
            else:
                new_pkg = PackageInstance.objects.make_package_instance_commit(
                    pkg,
                    copy_permissions=False,
                )
            self.assertIsInstance(new_pkg.package, Package)
            self.assertIn(new_pkg.key, PACKAGES.keys())
            self.assertEqual(new_pkg.package['title'], 'Liczby Doskonałe')
            self.assertNotEqual(new_pkg.key, pkg.key)
            self.assertNotEqual(new_pkg.path, pkg.path)

            if usr_mode == 'permission_pass':
                self.assertEqual(len(new_pkg.permitted_users), 2)
                self.assertIn(self.user, new_pkg.permitted_users)
                self.assertIn(self.user2, new_pkg.permitted_users)
            elif usr_mode == 'creator':
                self.assertEqual(len(new_pkg.permitted_users), 1)
                self.assertIn(self.user2, new_pkg.permitted_users)
            else:
                self.assertEqual(len(new_pkg.permitted_users), 0)

            shutil.rmtree(new_pkg.path)
            new_pkg.delete()
        except Exception as e:
            shutil.rmtree(new_pkg.path)
            new_pkg.delete()
            raise e

    @parameterized.expand([(False,), (True,)])
    def test_03_delete_package_instance(self, users):
        pkg = PackageInstance.objects.create_source_and_instance('dosko', '1')
        new_pkg = None
        try:
            new_pkg = PackageInstance.objects.make_package_instance_commit(pkg)
            if users:
                new_pkg.add_permitted_user(self.user)
                new_pkg.add_permitted_user(self.user2)
            path = new_pkg.path
            pk = new_pkg.pk
            PackageInstance.objects.delete_package_instance(new_pkg, delete_files=True)
            self.assertFalse(path.exists())
            with self.assertRaises(PackageInstance.DoesNotExist):
                deleted = PackageInstance.objects.get(pk=pk)
            if users:
                users_assigned = PackageInstanceUser.objects.filter(package_instance_id=pk).count()
                self.assertEqual(users_assigned, 0)
        except Exception as e:
            shutil.rmtree(new_pkg.path)
            new_pkg.delete()
            raise e

    @parameterized.expand([
        ('without users', False, False, ),
        ('with creator', True, False, ),
        ('with instance permissions', False, True),
        ('with creator and instance permissions', True, True)])
    def test_04_create_from_zip(self, name, usr, from_instance):
        pkg_src = PackageSource.objects.create_package_source('dosko')
        pkg = None
        if usr:
            usr = self.user
        else:
            usr = None
        if from_instance:
            pkg = PackageInstance.objects.create_package_instance(pkg_src, commit='1', creator=usr)
            pkg.add_permitted_user(self.user2)
        try:
            pkg = PackageInstance.objects.create_package_instance_from_zip(
                pkg_src,
                self.zip_file,
                permissions_from_instance=pkg,
                creator=usr
            )
            self.assertIsInstance(pkg.package, Package)
            self.assertIn(pkg.key, PACKAGES.keys())
            self.assertEqual(pkg.package['title'], 'zip test pkg')
            self.assertEqual(pkg.package['points'], 123)
            if usr and from_instance:
                self.assertEqual(len(pkg.permitted_users), 2)
                self.assertIn(self.user, pkg.permitted_users)
                self.assertIn(self.user2, pkg.permitted_users)
            elif usr:
                self.assertEqual(len(pkg.permitted_users), 1)
                self.assertIn(self.user, pkg.permitted_users)
            elif from_instance:
                self.assertEqual(len(pkg.permitted_users), 1)
                self.assertIn(self.user2, pkg.permitted_users)
            else:
                self.assertEqual(len(pkg.permitted_users), 0)

            shutil.rmtree(pkg.path)
            pkg.delete()
        except Exception as e:
            if pkg is not None:
                shutil.rmtree(pkg.path)
                pkg.delete()
            raise e

    @parameterized.expand([(False,), (True,)])
    def test_05_create_source_from_zip(self, usr):
        pkg_src = None
        if usr:
            usr = self.user
        else:
            usr = None
        try:
            pkg_src = PackageSource.objects.create_package_source_from_zip(
                'test',
                self.zip_file,
                creator=usr
            )
            self.assertIsInstance(pkg_src, PackageSource)
            pkg = pkg_src.instances.first()
            self.assertIn(pkg.key, PACKAGES.keys())
            self.assertEqual(pkg.package['title'], 'zip test pkg')
            self.assertEqual(pkg.package['points'], 123)
            if usr:
                self.assertEqual(len(pkg.permitted_users), 1)
                self.assertIn(self.user, pkg.permitted_users)
            else:
                self.assertEqual(len(pkg.permitted_users), 0)
            shutil.rmtree(pkg_src.path)
            pkg_src.delete()
        except Exception as e:
            if pkg_src is not None:
                shutil.rmtree(pkg_src.path)
                pkg_src.delete()
            raise e
