#!/usr/bin/env python
import unittest
from datetime import date

from fetch import LogFile, parse_date


class LogFileTests(unittest.TestCase):
    def test_invalid_filename(self):
        with self.assertRaises(ValueError):
            LogFile('invalid-filename.gz')

    def test_valid_filename(self):
        lf = LogFile('foobar_123456.123456.202001021200-1300-0.gz')
        self.assertEqual(lf.date, date(2020, 1, 2))


class ParseDateTests(unittest.TestCase):
    def test_parse_date(self):
        self.assertEqual(parse_date('2020-02-01'), date(2020, 2, 1))

    def test_parse_date_invalid(self):
        with self.assertRaises(ValueError):
            parse_date('2020-13-01')


if __name__ == '__main__':
    unittest.main()
