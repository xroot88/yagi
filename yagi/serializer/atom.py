import feedgenerator

import yagi.config
from yagi.serializer.paged_feed import PagedFeed
import yagi.utils


def _entity_link(entity_id, key):
    return unicode(''.join([_entity_url(), '%s/' % key, str(entity_id)]))


def _entity_url():
    conf = yagi.config.config_with('event_feed')
    feed_host = conf('feed_host')
    use_https = yagi.config.get_bool('event_feed', 'use_https')
    scheme = "%s://" % ('https' if use_https else 'http')
    port = str(conf('port') or '')
    if len(port) > 0:
        port = ':%s' % port

    if not feed_host:
        feed_host = yagi.utils.get_ip_addr()
    return unicode(''.join([scheme, feed_host, port, '/']))


def _categories():
        conf = yagi.config.config_with('event_feed')
        val = 'atom_categories'
        return [c.strip() for c in
                (conf(val).split(',') if conf(val) else [])]


def clean_content(cdict):
    return dict([i for i in cdict.items() if not i[0].startswith('_')])


def _feed_entity(feed, entity, entity_links=True):
    event_type = unicode(entity['event_type'])
    if entity_links:
        elink = _entity_link(entity['id'], entity['event_type'])
    else:
        elink = None
    feed.add_item(title=unicode(entity['event_type']),
                link=elink,
                description=event_type,
                contents=entity['content'],
                unique_id="urn:uuid:%s" % entity['id'],
                categories=[event_type] + _categories())


def dumps(entities, previous_page=None, next_page=None, entity_links=True):
    """Serializes a list of dictionaries as an ATOM feed"""

    title = unicode(yagi.config.get('event_feed', 'feed_title'))
    feed = PagedFeed(
        title=title,
        link=_entity_url(),
        feed_url=_entity_url(),
        description=title,
        language=u'en',
        previous_page_url=("%s?page=%s" % (_entity_url(), previous_page))
                          if previous_page is not None else None,
        next_page_url=("%s?page=%s" % (_entity_url(), next_page))
                          if next_page is not None else None)
    for entity in entities:
        _feed_entity(feed, entity, entity_links)
    return feed.writeString('utf-8')


def dump_item(entity, entity_links=True):
    """Serializes a single dictionary as an ATOM entry"""
    from StringIO import StringIO

    outfile = StringIO()
    handler = feedgenerator.SimplerXMLGenerator(outfile, 'utf-8')
    handler.startDocument()
    title = unicode(yagi.config.get('event_feed', 'feed_title'))
    feed = PagedFeed(
        title=title,
        link=_entity_url(),
        feed_url=_entity_url(),
        description=title,
        language=u'en',
        previous_page_url=None,
        next_page_url=None)

    _feed_entity(feed, entity, entity_links)
    feed.write_item(handler, feed.items[0], root=True)
    return outfile.getvalue()
