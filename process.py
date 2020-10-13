#!/usr/bin/env python

from collections import defaultdict

import apachelogs
from mrjob.job import MRJob


# http://httpd.apache.org/docs/current/mod/mod_log_config.html
APACHE_LOG_FORMAT = (
    "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\" \"%{Cookie}i\""
)


class RedirectFrequencyCount(MRJob):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = apachelogs.LogParser(APACHE_LOG_FORMAT)

    def mapper(self, _, line):
        try:
            entry = self.parser.parse(line)
        except apachelogs.InvalidEntryError:
            return

        path = entry.request_line.split(' ')[1]
        status_code = entry.final_status

        yield path, {status_code: 1}

    def reducer(self, key, values):
        codes = defaultdict(int)

        for value in values:
            for code, count in value.items():
                codes[code] += count

        yield key, codes


if __name__ == '__main__':
    RedirectFrequencyCount.run()
