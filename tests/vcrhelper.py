"""vcrpy integration helpers."""

import os
import unittest

import vcr


CASSETTE_LIB = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'cassettes')
assert os.path.isdir(CASSETTE_LIB), "Cassette library not found."

RECORD_MODE = 'none'


class VCRHelper(unittest.TestCase):

    filter_headers = [
        'user-agent',
        'date',
        'public-key-pins',
    ]

    def do_filter_headers(self, thing):
        for key, value in thing['headers'].items():
            if key.lower() in self.filter_headers:
                redact = '<%s-FILTERED>' % key.upper()
                thing['headers'][key] = redact
        return thing

    def before_record_request(self, request):
        # scrub any request data here
        return request

    def before_record_response(self, response):
        # scrub sensitive response data here
        response = self.do_filter_headers(response)
        return response

    def setUp(self, **vcrkwargs):

        defaults = {
            'filter_headers': self.filter_headers,
            'record_mode': RECORD_MODE,
            'cassette_library_dir': CASSETTE_LIB,
            'before_record_request': self.before_record_request,
            'before_record_response': self.before_record_response,
        }
        defaults.update(vcrkwargs)
        self.vcr = vcr.VCR(
            **defaults
        )
