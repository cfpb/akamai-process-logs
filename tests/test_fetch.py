import unittest
from datetime import date

from fetch import LogFile


class LogFileTests(unittest.TestCase):
    def test_invalid_filename(self):
        with self.assertRaises(ValueError):
            LogFile("invalid-filename.gz")

    def test_valid_filename(self):
        lf = LogFile("foobar_123456.123456.202001021200-1300-0.gz")
        self.assertEqual(lf.date, date(2020, 1, 2))
