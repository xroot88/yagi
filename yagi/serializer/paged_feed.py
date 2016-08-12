import json
import uuid
import feedgenerator


def clean_content(cdict):
    if cdict.__class__.__name__ == 'dict':
        return dict([i for i in cdict.items() if not i[0].startswith('_')])
    return cdict


class PagedFeed(feedgenerator.Atom1Feed):

    # I hate having to do this, but there is no other way to override
    # the link generation
    def add_item_elements(self, handler, item):
        #glommed wholesale from feed generator to change *one* little thing... (mdragon)
        handler.addQuickElement(u"title", item['title'])
        if item['link'] is not None:
            handler.addQuickElement(u"link", u"", {u"href": item['link'], u"rel": u"alternate"})
        if item['pubdate'] is not None:
            handler.addQuickElement(u"updated", feedgenerator.rfc3339_date(item['pubdate']).decode('utf-8'))

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
            unique_id = "urn:uuid:%s" % uuid.uuid4()
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
                dict(type=u'application/json'))
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


class CufPagedFeed(feedgenerator.Atom1Feed):

    def root_attributes_for_cuf(self, title):
        if title == "Server" or title == "NeutronPubIPv4":
            if self.feed['language'] is not None:
                return {u"xmlns:atom": self.ns, u"xml:lang": self.feed['language']}
            else:
                return {u"xmlns:atom": self.ns}
        if title == "Glance":
            return {u"xmlns:atom": self.ns,
                    u"xmlns": u"http://docs.rackspace.com/core/event",
                    u"xmlns:glance": u"http://docs.rackspace.com/usage/glance"}

    # Get it to care about content elements
    def write_item(self, handler, item, root=False, title="Server"):
        handler.startElement(u"atom:entry",
                             self.root_attributes_for_cuf(title) if root else {})
        for cat in item['categories']:
            handler.addQuickElement(u"atom:category", u"", {u"term": cat})
        handler.addQuickElement(u"atom:title", attrs={u"type": u"text"}, contents=title)
        handler.addQuickElement(u"atom:content",
                                item['contents'],
                                dict(type=u"application/xml"))
        handler.endElement(u"atom:entry")
