import calendar
import csv
import os
import re
import os.path
from collections import Counter
from datetime import date, datetime, timedelta
from functools import cached_property


def generate_dates_between(start_date, end_date):
    start_dt = datetime(start_date.year, start_date.month, start_date.day)
    end_dt = datetime(end_date.year, end_date.month, end_date.day)
    dt = start_dt
    while dt <= end_dt:
        yield dt.date()
        dt += timedelta(days=1)


def get_last_day_of_month(year, month):
    _, days_in_month = calendar.monthrange(year, month)
    return date(year, month, days_in_month)


class Storage:
    def __init__(self, root_directory=None):
        self.root_directory = root_directory or "."

    def exists(self):
        return os.path.exists(self.get_directory()) and os.path.isdir(
            self.get_directory()
        )

    def create(self):
        return os.mkdir(self.get_directory())

    def get_directory(self):
        return os.path.join(self.root_directory, self.get_directory_name())

    def get_directory_name(self):
        raise NotImplementedError("Implemented in subclasses")

    def get_filename_pattern(self):
        raise NotImplementedError("Implemented in subclasses")

    @cached_property
    def filename_re(self):
        return re.compile(self.get_filename_pattern())

    def get_filenames(self):
        if not self.exists():
            return []

        return [
            os.path.join(self.get_directory(), filename)
            for filename in sorted(os.listdir(self.get_directory()))
            if self.filename_re.match(filename)
        ]

    def get_keys(self):
        keys = []
        for filename in self.get_filenames():
            if match := self.filename_re.match(filename):
                keys.append(match.group("key"))
        return sorted(set(keys))

    def get_day(self, key):
        return datetime.strptime(key, "%Y%m%d").date()

    def get_key(self, day):
        return day.strftime("%Y%m%d")

    def get_days(self):
        return list(map(self.get_day, self.get_keys()))


class RawLogsStorage(Storage):
    def get_directory_name(self):
        return "raw_logs"

    def get_filename_pattern(self):
        return r"^.*\.((?P<key>\d{8}))\d{4}-\d{4}-\d+\.gz$"

    def get_filenames_for_day(self, day):
        filename_day_pattern = self.get_filename_pattern().replace(
            "(?P<key>\d{8})", self.get_key(day)
        )
        filename_day_re = re.compile(filename_day_pattern)
        return [
            filename
            for filename in self.get_filenames()
            if filename_day_re.match(filename)
        ]


class CountStorage(Storage):
    def get_filename(self, day):
        return os.path.join(self.get_directory(), self.get_key(day) + ".csv")

    def contains_day(self, day):
        return day in self.get_days()

    def write(self, counts, filename):
        with open(filename, "w") as f:
            writer = csv.writer(f)
            for (url, status_code), count in counts.most_common():
                writer.writerow([count, url, status_code])

    def read(self, filename):
        with open(filename) as f:
            return Counter(
                {
                    (url, int(status_code)): int(count)
                    for count, url, status_code in csv.reader(f)
                }
            )


class DailyCountStorage(CountStorage):
    def get_directory_name(self):
        return "daily"

    def get_filename_pattern(self):
        return r"^(.*/)?(?P<key>\d{8})\.csv$"

    def get_filenames_for_month(self, day):
        last_day_of_month = get_last_day_of_month(day.year, day.month)

        days_in_month = [
            date(day.year, day.month, day_number)
            for day_number in range(1, last_day_of_month.day + 1)
        ]

        return list(map(self.get_filename, days_in_month))

    def get_complete_month_starts(self):
        existing_days = self.get_days()
        month_starts = sorted(
            date(year, month, 1)
            for year, month in set((day.year, day.month) for day in existing_days)
        )

        existing_filenames = set(self.get_filenames())
        return [
            month_start
            for month_start in month_starts
            if set(self.get_filenames_for_month(month_start)).issubset(
                existing_filenames
            )
        ]


class MonthlyCountStorage(CountStorage):
    def get_directory_name(self):
        return "monthly"

    def get_day(self, key):
        return datetime.strptime(key, "%Y%m").date()

    def get_key(self, day):
        return day.strftime("%Y%m")

    def get_filename_pattern(self):
        return r"^(.*/)?(?P<key>\d{6})\.csv$"

    def get_filenames_for_quarter(self, day):
        first_day_of_quarter = date(day.year, day.month // 3 * 3 + 1, 1)

        month_starts_in_quarter = [
            first_day_of_quarter,
            date(day.year, first_day_of_quarter.month + 1, 1),
            date(day.year, first_day_of_quarter.month + 2, 1),
        ]

        return list(map(self.get_filename, month_starts_in_quarter))

    def get_complete_quarter_starts(self):
        existing_days = self.get_days()
        quarter_starts = sorted(
            date(year, month, 1)
            for year, month in set((day.year, day.month) for day in existing_days)
            if month % 3 == 1
        )

        existing_filenames = set(self.get_filenames())
        return [
            quarter_start
            for quarter_start in quarter_starts
            if set(self.get_filenames_for_quarter(quarter_start)).issubset(
                existing_filenames
            )
        ]


class QuarterlyCountStorage(CountStorage):
    def get_directory_name(self):
        return "quarterly"

    def get_day(self, key):
        match = re.match("(?P<year>\d{4})Q(?P<month>\d{2})", key)
        return date(match.group("year"), match.group("month"), 1)

    def get_key(self, day):
        return f"{day.strftime('%Y')}Q{(day.month // 3) + 1}"

    def get_filename_pattern(self):
        return r"^(.*/)?(?P<key>\d{4}Q\d)\.csv$"
