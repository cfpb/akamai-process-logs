#!/usr/bin/env python

import argparse
import os.path
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from itertools import chain

from akamai.netstorage import Netstorage
from tqdm import tqdm

from storage import DailyCountStorage, RawLogsStorage, generate_dates_between


class DirectoryListing:
    def __init__(self, xml):
        tree = ET.fromstring(xml)

        # <?xml version="1.0" encoding="UTF-8" />
        # <stat directory="/<cpcode>/<domain>">
        #   <file
        #     type="file"
        #     name="cfpb_xxxxxx.xxxxxxx.202001011200-1300-0.gz"
        #     size="1234567"
        #     md5="abcdabcdabcdabcdabcdabcdabcdabcd"
        #     mtime="1577880000"
        #   />
        #   <file ... />
        #   ...
        # </stat>
        self.logs = [LogFile(f.get("name")) for f in tree.findall("file")]

    def get_filenames(self, date):
        return [log.filename for log in self.logs if log.date == date]


class LogFile:
    FILENAME_REGEX = re.compile(
        r"\w+\.\w+\."
        r"(?P<year>\d{4})"
        r"(?P<month>\d{2})"
        r"(?P<day>\d{2})"
        r"(?P<from_hour>\d{2})"
        r"(?P<from_minute>\d{2})"
        r"-"
        r"(?P<to_hour>\d{2})"
        r"(?P<to_minute>\d{2})"
        r"-\d+\.gz"
    )

    def __init__(self, filename):
        self.filename = filename

        match = self.FILENAME_REGEX.match(filename)

        if not match:
            raise ValueError(filename)

        self.date = date(
            int(match.group("year")), int(match.group("month")), int(match.group("day"))
        )


class Downloader:
    def __init__(
        self,
        since_days_ago,
        netstorage_hostname,
        netstorage_key,
        netstorage_keyname,
        netstorage_directory,
        local_storage_directory,
    ):
        self.since_days_ago = since_days_ago
        self.end_date = datetime.utcnow().date() - timedelta(days=1)
        self.start_date = self.end_date - timedelta(days=self.since_days_ago - 1)

        # https://learn.akamai.com/en-us/webhelp/netstorage/netstorage-http-api-developer-guide/
        self.netstorage = Netstorage(
            netstorage_hostname, netstorage_keyname, netstorage_key, ssl=True
        )

        if not netstorage_directory.endswith("/"):
            netstorage_directory += "/"
        self.netstorage_directory = netstorage_directory

        self.local_storage_directory = local_storage_directory

    def download(self):
        netstorage_listing = self._get_netstorage_listing()

        days_to_consider = list(generate_dates_between(self.start_date, self.end_date))
        print(f"Considering {len(days_to_consider)} days")

        raw_logs_storage = RawLogsStorage(self.local_storage_directory)
        daily_count_storage = DailyCountStorage(self.local_storage_directory)

        days_to_download = [
            day for day in days_to_consider if not daily_count_storage.contains_day(day)
        ]
        filenames_to_download = list(
            chain(*(netstorage_listing.get_filenames(day) for day in days_to_download))
        )

        print(
            f"Downloading {len(filenames_to_download)} filenames for {len(days_to_download)} days"
        )
        if filenames_to_download:
            if not raw_logs_storage.exists():
                raw_logs_storage.create()

            for filename in tqdm(filenames_to_download, disable=None):
                self._download(filename, raw_logs_storage.get_directory())

    def _get_netstorage_listing(self):
        return DirectoryListing(
            self._call("dir", self.netstorage_directory, {"encoding": "utf-8"}).text
        )

    def _download(self, filename, destination_directory):
        self._call(
            "download",
            f"{self.netstorage_directory}{filename}",
            os.path.join(destination_directory, filename),
        )

    def _call(self, method, *args):
        fn = getattr(self.netstorage, method)
        _, response = fn(*args)
        response.raise_for_status()
        return response


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--since-days-ago",
        type=int,
        default=120,
        help="Download since this many days ago (default: %(default)s)",
    )
    parser.add_argument(
        "--netstorage-hostname",
        help="NetStorage HTTP API connection hostname",
        required=True,
    )
    parser.add_argument(
        "--netstorage-key", help="NetStorage HTTP API key", required=True
    )
    parser.add_argument(
        "--netstorage-keyname", help="NetStorage HTTP API key name", required=True
    )
    parser.add_argument(
        "--netstorage-directory",
        help="NetStorage log file directory, e.g. /123456/www.example.com",
        required=True,
    )
    parser.add_argument(
        "--local-storage-directory", help="Optional path to local file storage"
    )

    downloader = Downloader(**vars(parser.parse_args()))
    downloader.download()
