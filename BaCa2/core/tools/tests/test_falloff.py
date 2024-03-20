from datetime import datetime

from django.test import TestCase

from BaCa2.core.tools.falloff import *

from parameterized import parameterized


class TestFallOff(TestCase):

    def setUp(self):
        self.start = datetime(2022, 1, 1)
        self.deadline = datetime(2022, 1, 10)
        self.end = datetime(2022, 1, 5)

    def test_no_fall_off_within_deadline(self):
        fall_off = FallOff[FallOffPolicy.NONE](self.start, self.deadline, self.end)
        when = datetime(2022, 1, 7)
        factor = fall_off.get_factor(when)
        self.assertEqual(factor, 1.0)

    def test_linear_fall_off_within_end(self):
        fall_off = FallOff[FallOffPolicy.LINEAR](self.start, self.deadline, self.end)
        when = datetime(2022, 1, 3)
        factor = fall_off.get_factor(when)
        self.assertEqual(factor, 1.0)

    def test_no_fall_off_outside_deadline(self):
        fall_off = FallOff[FallOffPolicy.NONE](self.start, self.deadline, self.end)
        when = datetime(2022, 1, 15)
        factor = fall_off.get_factor(when)
        self.assertEqual(factor, 0.0)

    def test_linear_fall_off_outside_end_and_deadline(self):
        fall_off = FallOff[FallOffPolicy.LINEAR](self.start, self.deadline, self.end)
        when = datetime(2022, 1, 15)
        factor = fall_off.get_factor(when)
        self.assertEqual(factor, 0.0)

    def test_square_fall_off_within_end_date(self):
        square_fall_off = FallOff[FallOffPolicy.SQUARE](self.start, self.deadline, self.end)
        when = datetime(2022, 1, 4)
        factor = square_fall_off.get_factor(when)
        self.assertEqual(factor, 1.0)

    def test_unrecognized_fall_off_policy(self):
        with self.assertRaises(ValueError):
            # noinspection PyTypeChecker
            _ = FallOff['UNKNOWN']

    def test_linear_fall_off_get_factor_between_end_and_deadline(self):
        fall_off = FallOff[FallOffPolicy.LINEAR](self.start, self.deadline, self.end)
        when = datetime(2022, 1, 7)
        factor = fall_off.get_factor(when)
        self.assertGreaterEqual(factor, 0.0)
        self.assertLessEqual(factor, 1.0)

    def test_square_fall_off_get_factor_between_end_and_deadline(self):
        square_fall_off = FallOff[FallOffPolicy.SQUARE](self.start, self.deadline, self.end)
        when = datetime(2022, 1, 7)
        factor = square_fall_off.get_factor(when)
        self.assertGreaterEqual(factor, 0.0)
        self.assertLessEqual(factor, 1.0)


class TestNoFallOff(TestCase):

    def setUp(self):
        self.start = datetime(2022, 1, 1)
        self.deadline = datetime(2022, 1, 10)

    def test_within_deadline(self):
        no_fall_off = NoFallOff(self.start, self.deadline)
        within_deadline = datetime(2022, 1, 5)
        self.assertEqual(no_fall_off.get_factor(within_deadline), 1.0)

    def test_outside_deadline(self):
        no_fall_off = NoFallOff(self.start, self.deadline)
        outside_deadline = datetime(2022, 1, 15)
        self.assertEqual(no_fall_off.get_factor(outside_deadline), 0.0)

    def test_equal_start_time(self):
        no_fall_off = NoFallOff(self.start, self.deadline)
        self.assertEqual(no_fall_off.get_factor(self.start), 1.0)

    def test_equal_deadline(self):
        no_fall_off = NoFallOff(self.start, self.deadline)
        self.assertEqual(no_fall_off.get_factor(self.deadline), 1.0)

    def test_returns_zero_when_time_before_start(self):
        no_fall_off = NoFallOff(self.start, self.deadline)
        time_before_start = datetime(2021, 12, 31)
        factor = no_fall_off.get_factor(time_before_start)
        self.assertEqual(factor, 0.0)


class TestLinearFallOff(TestCase):

    def setUp(self):
        self.start = datetime(2022, 1, 1)
        self.deadline = datetime(2022, 1, 10)
        self.end = datetime(2022, 1, 5)

    def test_returns_1_if_within_end(self):
        fall_off = LinearFallOff(self.start, self.deadline, self.end)
        when = datetime(2022, 1, 4)
        factor = fall_off.get_factor(when)
        self.assertEqual(factor, 1.0)

    def test_returns_0_if_outside_start_and_end(self):
        fall_off = LinearFallOff(self.start, self.deadline, self.end)
        when = datetime(2022, 1, 11)
        factor = fall_off.get_factor(when)
        self.assertEqual(factor, 0.0)

    def test_returns_1_if_same_as_start_time(self):
        fall_off = LinearFallOff(self.start, self.deadline, self.end)
        when = datetime(2022, 1, 1)
        factor = fall_off.get_factor(when)
        self.assertEqual(factor, 1.0)

    def test_returns_0_if_same_as_deadline(self):
        fall_off = LinearFallOff(self.start, self.deadline, self.end)
        when = datetime(2022, 1, 10)
        factor = fall_off.get_factor(when)
        self.assertEqual(factor, 0.0)

    @parameterized.expand([
        (datetime(2022, 1, 8), 0.0, 0.5),
        (datetime(2022, 1, 6), 0.5, 1.0),
    ])
    def test_linear_fall_off_behaviour(self, when, lower_bound, upper_bound):
        fall_off = LinearFallOff(self.start, self.deadline, self.end)
        factor = fall_off.get_factor(when)
        self.assertGreaterEqual(factor, lower_bound)
        self.assertLessEqual(factor, upper_bound)


class TestSquareFallOff(TestCase):

    def setUp(self):
        self.start = datetime(2022, 1, 1)
        self.deadline = datetime(2022, 1, 10)
        self.end = datetime(2022, 1, 5)

    def test_returns_1_if_within_end_time(self):
        square_fall_off = SquareFallOff(self.start, self.deadline, self.end)
        when = datetime(2022, 1, 3)
        factor = square_fall_off.get_factor(when)
        self.assertEqual(factor, 1.0)

    def test_returns_0_if_outside_deadline_and_end_time(self):
        square_fall_off = SquareFallOff(self.start, self.deadline, self.end)
        when = datetime(2022, 1, 15)
        factor = square_fall_off.get_factor(when)
        self.assertEqual(factor, 0.0)

    def test_returns_1_if_equal_to_start_time(self):
        square_fall_off = SquareFallOff(self.start, self.deadline, self.end)
        when = datetime(2022, 1, 1)
        factor = square_fall_off.get_factor(when)
        self.assertEqual(factor, 1.0)

    def test_returns_0_if_equal_to_deadline_time(self):
        square_fall_off = SquareFallOff(self.start, self.deadline, self.end)
        when = datetime(2022, 1, 10)
        factor = square_fall_off.get_factor(when)
        self.assertAlmostEqual(factor, 0.0, 5)

    def test_behaviour_between_end_and_deadline(self):
        square_fall_off = SquareFallOff(self.start, self.deadline, self.end)
        halfway_point = self.end + (self.deadline - self.end) / 2
        factor = square_fall_off.get_factor(halfway_point)
        self.assertGreaterEqual(factor, 0.6)
        self.assertLessEqual(factor, 1.0)
