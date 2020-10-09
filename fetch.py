#!/usr/bin/env python

import argparse
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime

from akamai.netstorage import Netstorage
from tqdm import tqdm


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
        self.logs = [LogFile(f.get('name')) for f in tree.findall('file')]

    def get_filenames(self, from_date, to_date=None):
        return [
            log.filename for log in self.logs
            if log.date >= from_date and log.date <= (to_date or from_date)
        ]


class LogFile:
    FILENAME_REGEX = re.compile(
        r'\w+\.\w+\.'
        r'(?P<year>\d{4})'
        r'(?P<month>\d{2})'
        r'(?P<day>\d{2})'
        r'(?P<from_hour>\d{2})'
        r'(?P<from_minute>\d{2})'
        r'-'
        r'(?P<to_hour>\d{2})'
        r'(?P<to_minute>\d{2})'
        r'-\d+\.gz'
    )

    def __init__(self, filename):
        self.filename = filename

        match = self.FILENAME_REGEX.match(filename)

        if not match:
            raise ValueError(filename)

        self.date = date(
            int(match.group('year')),
            int(match.group('month')),
            int(match.group('day'))
        )


class Downloader:
    def __init__(
        self,
        netstorage_hostname,
        netstorage_key,
        netstorage_keyname
    ):
        self.netstorage = Netstorage(
            netstorage_hostname,
            netstorage_keyname,
            netstorage_key,
            ssl=True
        )

    def download(self, netstorage_directory, from_date, to_date=None):
        dir_xml = self._call(
            'dir',
            netstorage_directory,
            {'encoding': 'utf-8'}
        ).text

        dir_listing = DirectoryListing(dir_xml)
        filenames = dir_listing.get_filenames(from_date, to_date)

        if not netstorage_directory.endswith('/'):
            netstorage_directory += '/'

        for filename in tqdm(filenames):
            self._call('download', f'{netstorage_directory}{filename}')

    def _call(self, method, *args):
        fn = getattr(self.netstorage, method)
        _, response = fn(*args)
        response.raise_for_status()
        return response


DESCRIPTION = 'foo'


def parse_date(s):
    return datetime.strptime(s, '%Y-%m-%d').date()


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=DESCRIPTION
    )

    parser.add_argument(
        '--from-date',
        type=parse_date,
        help='Download logs starting from this date, e.g. 2020-01-01',
    )
    parser.add_argument(
        '--to-date',
        type=parse_date,
        help='Download logs starting from this date, e.g. 2020-02-01'
    )

    parser.add_argument(
        '--netstorage-hostname',
        help='NetStorage HTTP API connection hostname',
        required=True
    )
    parser.add_argument(
        '--netstorage-key',
        help='NetStorage HTTP API key',
        required=True
    )
    parser.add_argument(
        '--netstorage-keyname',
        help='NetStorage HTTP API key name',
        required=True
    )
    parser.add_argument(
        '--netstorage-directory',
        help='NetStorage log file directory, e.g. /123456/www.example.com',
        required=True
    )

    args = parser.parse_args()

    # https://learn.akamai.com/en-us/webhelp/netstorage/netstorage-http-api-developer-guide/
    downloader = Downloader(
        args.netstorage_hostname,
        args.netstorage_key,
        args.netstorage_keyname
    )

    downloader.download(
        args.netstorage_directory,
        args.from_date,
        args.to_date
    )


if __name__ == '__main__':
    main()
