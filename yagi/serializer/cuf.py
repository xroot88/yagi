import feedgenerator

import yagi.config
from yagi.serializer.paged_feed import CufPagedFeed
import yagi.utils


def _entity_link(entity_id, key):
    return unicode(''.join([_entity_url(), '%s/' % key, str(entity_id)]))


def _entity_url():
    conf = yagi.config.config_with('event_feed')
    feed_host = conf('feed_host')
    use_https = yagi.config.get_bool('event_feed', 'use_https')
    scheme = "%s://" % ('https' if use_https else 'http')
    port = conf('port')
    if port:
        port = ':%s' % port
    else:
        port = ''

    if not feed_host:
        feed_host = yagi.utils.get_ip_addr()
    return unicode(''.join([scheme, feed_host, port, '/']))


def _categories():
        conf = yagi.config.config_with('event_feed')
        val = 'atom_categories'
        return [c.strip() for c in
                (conf(val).split(',') if conf(val) else [])]


def dump_item(entity, service_title="Server"):
    """Serializes a single dictionary as an ATOM entry"""
    from StringIO import StringIO

    outfile = StringIO()
    handler = feedgenerator.SimplerXMLGenerator(outfile, 'utf-8')
    handler.startDocument()
    title = unicode(yagi.config.get('event_feed', 'feed_title'))
    feed = CufPagedFeed(
        title=title,
        link=_entity_url(),
        feed_url=_entity_url(),
        description=title,
        language=None,
        previous_page_url=None,
        next_page_url=None)

    event_type = unicode(entity['event_type'])
    original_message_id = unicode("original_message_id:{id}".format(id=
                                  entity['original_message_id']))
    feed.add_item(
        title=unicode(entity['event_type']),
        link=_entity_link(entity['id'], entity['event_type']),
        description=event_type,
        contents=entity['content']['payload'],
        categories=[event_type, original_message_id])
    feed.write_item(handler, feed.items[0], root=True, title=service_title)
    return outfile.getvalue()
