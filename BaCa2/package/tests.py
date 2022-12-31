from django.test import TestCase
from .validators import isAny, isNone, isInt, isIntBetween, isFloat, isFloatBetween, isStr, is_, isIn, isShorter, isDict, isPath, isSize, isList, memory_converting, valid_memory_size
from .package_manage import TestF
from BaCa2.settings import BASE_DIR


class ValidationsTests(TestCase):
    def test_isInt(self):
        self.assertTrue(isInt('5'))

    def test_isStr(self):
        self.assertFalse(isStr(5))

    def test_isIntBetween(self):
        self.assertTrue(isIntBetween(5, 2, 10))


class TestFTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test = TestF(BASE_DIR / 'packages' / 'tests_to_testing' / '1.in', {}, {
            'name': '1',
            'memory_limit': '10M',
            'time_limit': 10
        })
    # @classmethod
    # def tearDownClass(cls):
    #     pass
    def test_check_valid(self):
        self.assertTrue(self.test.check_test())
