import unittest
import httplib2

import stubout

from yagi import auth
from yagi import config


class MockResponse(object):
    def __init__(self, status_code=200):
        self.status = status_code


class TestAuth(unittest.TestCase):

    def setUp(self):
        self.stubs = stubout.StubOutForTesting()
        config_dict = {
            'handler_auth': {
                'method': 'rax_auth_v2',
                'user': 'a_user',
                'key': 'seekret_key',
                'validate_ssl': 'False',
                'auth_server': 'http://127.0.0.1:12345/test',
            },
        }

        self.auth_json = '{"access": {"token": {"id": "%s"}}}'

        def get(*args, **kwargs):
            val = None
            for arg in args:
                if val:
                    val = val.get(arg)
                else:
                    val = config_dict.get(arg)
                    if not val:
                        return None or kwargs.get('default')
            return val

        def config_with(*args):
            return functools.partial(get, args)

        self.stubs.Set(config, 'config_with', config_with)
        self.stubs.Set(config, 'get', get)

    def tearDown(self):
        self.stubs.UnsetAll()

    def test_rax_auth_caches_token(self):
        self.calls = 0

        def mock_request(*args, **kwargs):
            self.calls += 1
            body = self.auth_json % ("token_%s" % self.calls)
            return MockResponse(200), body
        self.stubs.Set(httplib2.Http, 'request', mock_request)
        headers = dict()
        auth.rax_auth_v2("bogus_unused_conn", headers, force=False)
        self.assertEquals(self.calls, 1)
        self.assertEquals(headers['X-Auth-Token'], 'token_1')
        #round 2
        headers = dict()
        auth.rax_auth_v2("bogus_unused_conn", headers, force=False)
        self.assertEquals(self.calls, 1)
        self.assertEquals(headers['X-Auth-Token'], 'token_1')
        #round 3
        headers = dict()
        auth.rax_auth_v2("bogus_unused_conn", headers, force=True)
        self.assertEquals(self.calls, 2)
        self.assertEquals(headers['X-Auth-Token'], 'token_2')

