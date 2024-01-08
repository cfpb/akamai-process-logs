#!/usr/bin/env python

import argparse
import gzip
import os.path
import re
from collections import Counter

from apachelogs.directives import format2regex

from storage import (
    DailyCountStorage,
    MonthlyCountStorage,
    QuarterlyCountStorage,
    RawLogsStorage,
)


# http://httpd.apache.org/docs/current/mod/mod_log_config.html
APACHE_LOG_FORMAT = '%h %l %u %t "%r" %>s'


class ApacheLogFileRedirectCounter:
    def __init__(self):
        self.count = Counter()
        self.group_defs, self.regex = format2regex(APACHE_LOG_FORMAT)
        self.regex = re.compile(self.regex + " .*")

    def update(self, filename):
        with gzip.open(filename, "rt", errors="ignore") as f:
            self.count.update(filter(None, map(self.parse_line, f)))

    def parse_line(self, line):
        m = self.regex.match(line)

        try:
            path = m.group(5).split(" ")[1]
            status_code = int(m.group(6))
        except (TypeError, ValueError):
            print(f"Warning! Could not parse: {line}")
            return

        if status_code in (301, 302):
            return path, status_code


class RedirectCounter:
    def count(self, overwrite, local_storage_directory):
        raw_logs_storage = RawLogsStorage(local_storage_directory)
        daily_count_storage = DailyCountStorage(local_storage_directory)

        for day in raw_logs_storage.get_days():
            key = daily_count_storage.get_key(day)
            daily_filename = daily_count_storage.get_filename(day)

            if os.path.exists(daily_filename) and not overwrite:
                print(f"{key}: Counts already exist")
                continue

            print(f"{key}: Processing raw log files")
            daily_counts = ApacheLogFileRedirectCounter()
            for filename in raw_logs_storage.get_filenames_for_day(day):
                print(f"{key}: Reading log file {filename}")
                daily_counts.update(filename)

            if not daily_count_storage.exists():
                daily_count_storage.create()

            print(f"{key}: Writing counts to {daily_filename}")
            daily_count_storage.write(daily_counts.count, daily_filename)

        monthly_count_storage = MonthlyCountStorage(local_storage_directory)

        for day in daily_count_storage.get_complete_month_starts():
            key = monthly_count_storage.get_key(day)
            monthly_filename = monthly_count_storage.get_filename(day)

            if os.path.exists(monthly_filename) and not overwrite:
                print(f"{key}: Counts already exist")
                continue

            print(f"{key}: Processing daily count files")
            monthly_counts = Counter()
            for filename in daily_count_storage.get_filenames_for_month(day):
                print(f"{key}: Reading log file {filename}")
                daily_counts = daily_count_storage.read(filename)
                monthly_counts += daily_counts

            if not monthly_count_storage.exists():
                monthly_count_storage.create()

            print(f"{key}: Writing counts to {monthly_filename}")
            monthly_count_storage.write(monthly_counts, monthly_filename)

        quarterly_count_storage = QuarterlyCountStorage(local_storage_directory)

        for day in monthly_count_storage.get_complete_quarter_starts():
            key = quarterly_count_storage.get_key(day)
            quarterly_filename = quarterly_count_storage.get_filename(day)

            if os.path.exists(quarterly_filename) and not overwrite:
                print(f"{key}: Counts already exist")
                continue

            quarterly_counts = Counter()
            for filename in monthly_count_storage.get_filenames_for_quarter(day):
                print(f"{key}: Reading log file {filename}")
                monthly_counts = monthly_count_storage.read(filename)
                quarterly_counts.update(monthly_counts)

            print(f"{key}: Processing monthly count files")
            if not quarterly_count_storage.exists():
                quarterly_count_storage.create()

            print(f"{key}: Writing counts to {quarterly_filename}")
            quarterly_count_storage.write(quarterly_counts, quarterly_filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--local-storage-directory", help="Optional path to local file storage"
    )

    counter = RedirectCounter()
    counter.count(**vars(parser.parse_args()))
