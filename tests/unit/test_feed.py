import unittest
import feedgenerator
import stubout
import webob

import yagi.feed.feed
from StringIO import StringIO
from yagi.serializer.paged_feed import CufPagedFeed


class FeedTests(unittest.TestCase):
    """Some lame tests to hold everything together until I can write a better
    router in"""

    def setUp(self):
        self.stubs = stubout.StubOutForTesting()

        def mock_fun(*args):
            pass
        self.stubs.Set(yagi.feed.feed.EventFeed, '__init__', mock_fun)
        self.stubs.Set(yagi.feed.feed.EventFeed, 'respond', mock_fun)

    def tearDown(self):
        self.stubs.UnsetAll()

    def test_get_one(self):
        self.called = False

        def mock_get_one(*args):
            self.called = True
        self.stubs.Set(yagi.feed.feed.EventFeed, 'get_one', mock_get_one)
        feed = yagi.feed.feed.EventFeed()
        req = webob.Request.blank('/dummy/0')
        req.get_response(feed.route_request)
        self.assertEqual(self.called, True)

    def test_get_all(self):
        self.called = False

        def mock_get_all(*args):
            self.called = True
        self.stubs.Set(yagi.feed.feed.EventFeed, 'get_all', mock_get_all)
        feed = yagi.feed.feed.EventFeed()
        req = webob.Request.blank('/')
        req.get_response(feed.route_request)
        self.assertEqual(self.called, True)

    def test_get_all_of_resource(self):
        self.called = False

        def mock_get_all(*args):
            pass

        def mock_get(*args):
            self.called = True

        self.stubs.Set(yagi.feed.feed.EventFeed, 'get_all', mock_get_all)
        self.stubs.Set(yagi.feed.feed.EventFeed, 'get_all_of_resource',
                mock_get)
        feed = yagi.feed.feed.EventFeed()
        req = webob.Request.blank('/instance')
        req.get_response(feed.route_request)
        self.assertEqual(self.called, True)

    def test_get_all_of_resource_2(self):
        self.called = False

        def mock_get_all(*args):
            pass

        def mock_get(*args):
            self.called = True

        self.stubs.Set(yagi.feed.feed.EventFeed, 'get_all', mock_get_all)
        self.stubs.Set(yagi.feed.feed.EventFeed, 'get_all_of_resource',
                mock_get)
        feed = yagi.feed.feed.EventFeed()
        # Trailing slash
        req = webob.Request.blank('/instance/')
        req.get_response(feed.route_request)
        self.assertEqual(self.called, True)


class TestCufFeed(unittest.TestCase):

    def test_write_item_in_cuf_feed(self):
        outfile = StringIO()
        handler = feedgenerator.SimplerXMLGenerator(outfile, 'utf-8')
        handler.startDocument()
        contents = '<event xmlns="http://docs.rackspace.com/core/event" ' \
                   'xmlns:nova="http://docs.rackspace.com/event/nova" ' \
                   'version="1" tenantId="2882"/></event>'
        item = {u'description': u'test', u'pubdate': None,
                u'author_link': None, u'author_name': None,
                u'link': 'http://127.0.0.1/test/some_uuid',
                u'ttl': None, u'enclosure': None, u'categories': [u'test'],
                u'item_copyright': None, u'title': u'test',
                u'author_email': None, u'comments': None,
                'contents': contents,
                u'unique_id': None}
        cuf_paged_feed = CufPagedFeed(title='test',
                                      link='http://127.0.0.1/test/some_uuid',
                                      feed_url='http://127.0.0.1/test/some_uuid',
                                      description='test',
                                      language=None,
                                      previous_page_url=None,
                                      next_page_url=None)
        cuf_paged_feed.write_item(handler,item)
        expected_result = '<?xml version="1.0" encoding="utf-8"?>\n'\
        '<?atom feed="glance/events"?><atom:entry><atom:title type="text">'\
        'Server</atom:title><atom:content type="application/xml">&lt;event '\
        'xmlns="http://docs.rackspace.com/core/event" xmlns:nova="http://'\
        'docs.rackspace.com/event/nova" version="1" ' \
        'tenantId="2882"/&gt;&lt;/event&gt;</atom:content></atom:entry></atom>'
        self.assertEqual(outfile.getvalue(),expected_result)
