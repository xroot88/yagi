import unittest
import httplib2
from yagi import http_util
from tests.unit.test_cufpub import MockMessage, MockResponse
from yagi.handler.atompub_handler import UnauthorizedException, MessageDeliveryFailed
from yagi.handler.cuf_pub_handler import CufPub
from yagi.handler.http_connection import HttpConnection, InvalidContentException
import functools
import stubout
import yagi


class HttpConnectionTests(unittest.TestCase):

    def setUp(self):
        self.stubs = stubout.StubOutForTesting()
        config_dict = {
            'atompub': {
                'url': 'http://127.0.0.1:9000/test/%(event_type)s',
                'user': 'user',
                'key': 'key',
                'interval': 30,
                'max_wait': 600,
                'retries': 1,
                'failures_before_reauth': 5
            },
            'event_feed': {
                'feed_title': 'feed_title',
                'feed_host': 'feed_host',
                'use_https': False,
                'port': 'port'
            },
            'handler_auth': {
                'method': 'no_auth'
            },
            'cufpub': {
                'url': 'http://127.0.0.1:9000/test/%(event_type)s',
                'user': 'user',
                'key': 'key',
                'interval': 30,
                'max_wait': 600,
                'retries': 1,
                'failures_before_reauth': 5
            }
        }

        self.handler = CufPub()

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

        self.stubs.Set(yagi.config, 'config_with', config_with)
        self.stubs.Set(yagi.config, 'get', get)

    def tearDown(self):
        self.stubs.UnsetAll()

    def test_send_notification_successfully(self):
        self.called = False

        def mock_request(*args, **kwargs):
            self.called = True
            return MockResponse(201), None

        handler = CufPub()
        http_conn = HttpConnection(handler)
        endpoint = handler.config_get("url")
        payload_body = {"a":"b"}
        self.stubs.Set(httplib2.Http, 'request', mock_request)
        http_conn.send_notification(endpoint, endpoint, payload_body)

    def test_response_401_raises_unauthorized_exception(self):
        self.called = False

        def mock_request(*args, **kwargs):
            self.called = True
            return MockResponse(401), None

        handler = CufPub()
        http_conn = HttpConnection(handler)
        endpoint = handler.config_get("url")
        payload_body = {"a":"b"}
        self.stubs.Set(httplib2.Http, 'request', mock_request)

        self.assertRaises(UnauthorizedException,http_conn.send_notification,
                          endpoint, endpoint, payload_body)

    def test_response_other_than_201_or_400_raises_exception(self):
        self.called = False

        def mock_request(*args, **kwargs):
            self.called = True
            return MockResponse(405), None

        handler = CufPub()
        http_conn = HttpConnection(handler)
        endpoint = handler.config_get("url")
        payload_body = {"a":"b"}
        self.stubs.Set(httplib2.Http, 'request', mock_request)

        self.assertRaises(MessageDeliveryFailed,http_conn.send_notification,
                          endpoint, endpoint, payload_body)

    def test_response_too_large_error_and_status_not_201_raises_exception(self):
        self.called = False

        def mock_request(*args, **kwargs):
            self.called = True
            raise http_util.ResponseTooLargeError("desc",MockResponse(0),
                                                  "content")

        handler = CufPub()
        http_conn = HttpConnection(handler)
        endpoint = handler.config_get("url")
        payload_body = {"a":"b"}
        self.stubs.Set(httplib2.Http, 'request', mock_request)

        self.assertRaises(MessageDeliveryFailed, http_conn.send_notification,
                          endpoint, endpoint, payload_body)

    def test_response_too_large_error_and_status_is_201_does_not_raise_exception(self):
        self.called = False

        def mock_request(*args, **kwargs):
            self.called = True
            raise http_util.ResponseTooLargeError("desc",MockResponse(201),
                                                  "content")

        handler = CufPub()
        http_conn = HttpConnection(handler)
        endpoint = handler.config_get("url")
        payload_body = {"a":"b"}
        self.stubs.Set(httplib2.Http, 'request', mock_request)

        http_conn.send_notification(endpoint, endpoint, payload_body)

    def test_duplicate_entry_to_atomhopper_response_409(self):
        self.called = False

        def mock_request(*args, **kwargs):
            self.called = True
            return MockResponse(409), None

        handler = CufPub()
        http_conn = HttpConnection(handler)
        endpoint = handler.config_get("url")
        payload_body = {"a":"b"}
        self.stubs.Set(httplib2.Http, 'request', mock_request)

        status = http_conn.send_notification(endpoint, endpoint, payload_body)
        self.assertEqual(status,409)

    def test_response_status_400_raises_invalid_content_exception(self):
        self.called = False

        def mock_request(*args, **kwargs):
            self.called = True
            return MockResponse(400), None
        handler = CufPub()
        http_conn = HttpConnection(handler)
        endpoint = handler.config_get("url")
        payload_body = {"a":"b"}
        self.stubs.Set(httplib2.Http, 'request', mock_request)

        self.assertRaises(InvalidContentException, http_conn.send_notification,
                          endpoint, endpoint, payload_body)



