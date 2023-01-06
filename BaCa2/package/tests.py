from unittest import TestCase
from django.test import TestCase
from BaCa2.exceptions import NoSetFound, NoTestFound
from .validators import isAny, isNone, isInt, isIntBetween, isFloat, isFloatBetween, isStr, is_, isIn, isShorter, isDict, isPath, isSize, isList, memory_converting, valid_memory_size
from .package_manage import TestF, TSet, Package
from BaCa2.settings import BASE_DIR
from pathlib import Path
from yaml import safe_load

class ValidationsTests(TestCase):
    pass

class TestFTests(TestCase):
    def setUp(self):
        self.test = TestF(Path(__file__).resolve().parent / 'packages' / 'tests_to_testing', {}, {
            'name': '1',
            'memory_limit': '10M',
            'time_limit': 5
        })
    def test_check_valid(self):
        self.assertTrue(self.test.check_test())

    def test_get_settings(self):
        self.assertEqual(self.test['name'], '1')
        self.assertEqual(self.test['memory_limit'], '10M')
        self.assertEqual(self.test['time_limit'], 5)

    def test_set_settings(self):
        self.test['name'] = '2'
        self.assertEqual(self.test['name'], '2')
        self.test['name'] = '1'

class TSetTests(TestCase):
    def setUp(self):
        self.path = Path(__file__).resolve().parent / 'packages\\1\\tests'
        self.set0 = TSet(self.path / 'set0')
        self.set1 = TSet(self.path / 'set1')
        self.set2 = TSet(self.path / 'set2')

    def test_init(self):
        self.assertEqual(self.set0._path, self.path / 'set0')
        self.assertEqual(self.set1._path, self.path / 'set1')
        self.assertEqual(self.set2._path, self.path / 'set2')

    def test_check_valid(self):
        self.assertTrue(self.set0.check_set())
        self.assertEqual(len(self.set0._tests), 2)
        self.assertTrue(self.set1.check_set())
        self.assertTrue(self.set2.check_set())

    def test_func_tests1(self):
        self.assertEqual(self.set0.tests('2'), self.set0._tests[0])
        test = [i for i in self.set1._tests if i['name'] == '2']
        self.assertEqual(self.set1.tests('2'), test[0])
        self.assertEqual(self.set2.tests('3', True), self.set2._tests[3])
        self.set2.delete_test('3')

    def test_func_tests2(self):
        self.assertRaises(NoTestFound, self.set0.tests, '1')
        self.assertRaises(NoTestFound, self.set1.tests, '3')
        self.assertRaises(NoTestFound, self.set2.tests, '2')

    def test_func_delete1(self):
        self.assertEqual(self.set0.tests('4', True), self.set0._tests[2])
        self.set0.delete_test('4')
        names = [i['name'] for i in self.set0._tests]
        self.assertNotIn('4', names)

    def test_func_delete2(self):
        self.assertRaises(NoTestFound, self.set0.tests, '1')
        self.assertRaises(NoTestFound, self.set1.tests, '3')
        self.assertRaises(NoTestFound, self.set2.tests, '2')

    def test_func_move1(self):
        self.set2.move_test('5', self.set1)
        names = [i['name'] for i in self.set1._tests]
        self.assertIn('5', names)
        self.set1.move_test('5', self.set2)

    def test_func_move2(self):
        self.set2.move_test('6', self.set1)
        with open(self.set1._path / 'config.yml', mode="rt", encoding="utf-8") as file:
            settings = safe_load(file)
        value = False
        for i in settings['tests'].values():
            if i['name'] == '6':
                value = True
        self.assertTrue(value)
        self.set1.move_test('6', self.set2)
    def test_func_move2(self):
        self.assertRaises(NoTestFound, self.set0.tests, '1')
        self.assertRaises(NoTestFound, self.set1.tests, '3')
        self.assertRaises(NoTestFound, self.set2.tests, '2')

class PackageTests(TestCase):
    def setUp(self):
        self.path = Path(__file__).resolve().parent.parent / 'package\packages\\1'
        self.package = Package(self.path)

    def test_init(self):
        self.assertEqual(self.package._path, self.path)
        with open(self.path / 'config.yml', mode="rt", encoding="utf-8") as file:
            settings = safe_load(file)
        self.assertEqual(self.package._settings['title'], settings['title'])

    def test_func_sets1(self):
        self.assertEqual(self.package.sets('set0'), self.package._sets[0])

    def test_func_sets2(self):
        self.assertRaises(NoSetFound, self.package.sets, 'set3')

    def test_func_sets3(self):
        self.package.sets('set4', True)
        sets = [i['name'] for i in self.package._sets]
        self.assertIn('set4', sets)
        self.assertTrue(self.package.sets('set4')._path.exists())
        self.package.delete_set('set4')

    def test_func_delete(self):
        self.assertRaises(NoSetFound, self.package.sets, 'set4')

    def test_check_valid(self):
        self.assertTrue(self.package.check_package())



