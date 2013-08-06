import json

import feedgenerator

import yagi.config
import yagi.utils


def _entity_link(entity_id, key):
    return unicode(''.join([_entity_url(), '%s/' % key, str(entity_id)]))


def _entity_url():
    conf = yagi.config.config_with('event_feed')
    feed_host = conf('feed_host')
    use_https = yagi.config.get_bool('event_feed', 'use_https')
    scheme = "%s://" % ('https' if use_https else 'http')
    port = conf('port') or ''
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


class PagedFeed(feedgenerator.Atom1Feed):

    # I hate having to do this, but there is no other way to override
    # the link generation
    def add_item_elements(self, handler, item):
        #glommed wholesale from feed generator to change *one* little thing... (mdragon)
        handler.addQuickElement(u"title", item['title'])
        if item['link'] is not None:
            handler.addQuickElement(u"link", u"", {u"href": item['link'], u"rel": u"alternate"})
        if item['pubdate'] is not None:
            handler.addQuickElement(u"updated", rfc3339_date(item['pubdate']).decode('utf-8'))

        # Author information.
        if item['author_name'] is not None:
            handler.startElement(u"author", {})
            handler.addQuickElement(u"name", item['author_name'])
            if item['author_email'] is not None:
                handler.addQuickElement(u"email", item['author_email'])
            if item['author_link'] is not None:
                handler.addQuickElement(u"uri", item['author_link'])
            handler.endElement(u"author")

        # Unique ID.
        if item['unique_id'] is not None:
            unique_id = item['unique_id']
        else:
            unique_id = get_tag_uri(item['link'], item['pubdate'])
        handler.addQuickElement(u"id", unique_id)

        # Summary.
        if item['description'] is not None:
            handler.addQuickElement(u"summary", item['description'], {u"type": u"html"})

        # Enclosure.
        if item['enclosure'] is not None:
            handler.addQuickElement(u"link", '',
                {u"rel": u"enclosure",
                 u"href": item['enclosure'].url,
                 u"length": item['enclosure'].length,
                 u"type": item['enclosure'].mime_type})

        # Categories.
        for cat in item['categories']:
            handler.addQuickElement(u"category", u"", {u"term": cat})

        # Rights.
        if item['item_copyright'] is not None:
            handler.addQuickElement(u"rights", item['item_copyright'])

    # Get it to care about content elements
    def write_items(self, handler):
        for item in self.items:
            self.write_item(handler, item)

    # Get it to care about content elements
    def write_item(self, handler, item, root=False):
        handler.startElement(u"entry",
                             self.root_attributes() if root else {})
        self.add_item_elements(handler, item)
        handler.addQuickElement(u"content",
                json.dumps(clean_content(item['contents'])),
                dict(type='application/json'))
        handler.endElement(u"entry")

    def add_root_elements(self, handler):
        super(PagedFeed, self).add_root_elements(handler)
        if self.feed.get('next_page_url') is not None:
            handler.addQuickElement(u"link",
                                    "",
                                    {u"rel": u"next",
                                     u"href": self.feed['next_page_url']})
        if self.feed.get('previous_page_url') is not None:
            handler.addQuickElement(u"link",
                                    "",
                                    {u"rel": u"previous",
                                     u"href": self.feed['previous_page_url']})

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
