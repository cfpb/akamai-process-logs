import unittest
from datetime import date

from storage import generate_dates_between, get_last_day_of_month


class GenerateDatesBetweenTests(unittest.TestCase):
    def test_single_day(self):
        day = date(2023, 9, 28)
        self.assertEqual(list(generate_dates_between(day, day)), [day])

    def test_date_range(self):
        self.assertEqual(
            list(generate_dates_between(date(2023, 2, 27), date(2023, 3, 2))),
            [date(2023, 2, 27), date(2023, 2, 28), date(2023, 3, 1), date(2023, 3, 2)],
        )


class GetLastDayOfMonthTests(unittest.TestCase):
    def test_get_last_day(self):
        self.assertEqual(get_last_day_of_month(2023, 1), date(2023, 1, 31))
        self.assertEqual(get_last_day_of_month(2024, 2), date(2024, 2, 29))
