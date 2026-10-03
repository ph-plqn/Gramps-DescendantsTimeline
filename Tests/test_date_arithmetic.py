import unittest
from datetime import date

from descendants_timeline.inference.date_arithmetic import add_years


class TestAddYears(unittest.TestCase):

    def test_add_positive_years(self):
        result = add_years(
            date(1800, 6, 15),
            12,
        )

        self.assertEqual(
            result,
            date(1812, 6, 15),
        )

    def test_subtract_years(self):
        result = add_years(
            date(1870, 6, 15),
            -125,
        )

        self.assertEqual(
            result,
            date(1745, 6, 15),
        )

    def test_february_29_to_leap_year(self):
        result = add_years(
            date(1804, 2, 29),
            12,
        )

        self.assertEqual(
            result,
            date(1816, 2, 29),
        )

    def test_february_29_to_non_leap_year(self):
        result = add_years(
            date(1804, 2, 29),
            125,
        )

        self.assertEqual(
            result,
            date(1929, 3, 1),
        )

    def test_february_29_backward_to_non_leap_year(self):
        result = add_years(
            date(1880, 2, 29),
            -125,
        )

        self.assertEqual(
            result,
            date(1755, 3, 1),
        )
    def test_zero_years_returns_same_date(self):
        value = date(1850, 7, 10)

        result = add_years(value, 0)

        self.assertEqual(result, value)

    def test_rejects_non_date_value(self):
        with self.assertRaises(TypeError):
            add_years("1800-01-01", 12)

    def test_rejects_non_integer_years(self):
        with self.assertRaises(TypeError):
            add_years(date(1800, 1, 1), 12.5)