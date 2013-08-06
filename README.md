# Yagi

A modular OpenStack notification event processor/broadcaster written in Python.

Yagi is designed to efficiently gather amqp messages in the json format used by OpenStack projects
notification busses, from a large and configurable number of queues, and proccess them through an extensible
set of simple handlers.

Handlers are simple to write, and can be chained in a WSGI-like architecture.
Yagi handles fetching messages, a batch at a time, and passes fetched messages to each handler,
handling AMQP message semantics so the handlers can concentrate on the task at hand.

In addition, a feed daemon is included that can generate a paged Atom feed of notification events that have been persisted in a datastore.

## Available Handlers

* AtomPub: Formats notifications in Atom format, and pushes them to a
           feed server using the AtomPub protocol. Useful with feed servers such as AtomHopper
           (http://atomhopper.org/)
* Redis:   Persists notifications to a Redis database. Can be used with
           Yagi\'s feed daemon.
* PubSubHubub: Pings a pubsubhubub hub when notifications arrive.
               Together with a hub, and yagi\'s feed daemon, this can enable publish/subscribe subscriptions
               to notification events.
* StackTackPing: Works with the StackTach openstack monitoring tool to
                 monitor event feeds. If you are using Yagi to provide feeds of openstack notifications,
                 this will ping stacktach when those feeds are updated, informing it of the success or failure
                 of the updates, letting you catch if the feed server is down, or some system is dropping events.

## Installation and running

The current version of Yagi can be fetched from the code repository at: https://github.com/rackerlabs/yagi
cd to the yagi directory and run:

    sudo python setup.py install

The launch the yagi process:

    yagi-event

An altername config file may be passed to yagi like this:

    yagi-event -c /path/to/config/file

Yagi does not daemonize. use your favorite daemon manager to do that.


## Configuration

A sample yagi.conf can be found in the etc directory.

Sections to note:
* rabbit_broker: Your rabbit connection info goes here.
* event_feed: If using the feed daemon, remember to set the feed_host to
              the name of the host it is running on. This allows yagi to correctly construct links in the feed.
* persistence: If using the redis handler, put your reddisc connection
               info here.
* consumers: the 'queues' config variable lists the queues yagi should
             listen on.
* consumer:$queue_name: For each queue Yagi is listening on there should
                       be a consumer section in the config file (for example if you have a queue named
                       some.queue listed in the [consumers] section, there should be a [consumer:some.queue]
                       section with configuration for that specific queue.) This should list properties
                       for the queue, such as if itshould be durable. Important variables here are 'apps',
                       which is a comma separated list of handlers that messages from that queues should be
                       passed to, and 'max_messages' which is the maximum number of messages that
                       Yagi will pull from that queue at one time. (it will then go to the next queue,
                       eventually coming back around, if there are still messages waiting)

Handlers may also have their own, additional configuration.
This is usually found in a section named after the handler (all lowercase, one word)

## Scaling

Yagi is designed to scale by running multiple processes. Simply launch as many yagi-event processes as
you need to handle your load. (yagi-event is fairly lightweight)

## Dependencies:

* anyjson
* argparse
* feedgenerator
* httplib2
* requests (eventually httplib2 will be replaced with requests)
* redis (if using redis handler)
* webob
* eventlet
* python-dateutil
* daemon
* pubsubhubbub_publish (if using pubsubhubub handler) (available under the publisher_clients folder
         after checking out the project from [Google Code]
         (http://code.google.com/p/pubsubhubbub/source/checkout)
         NOTE: the plan is to replace this dependency later with our implementation
* carrot (if using Rabbit)
* routes

## Running the feed daemon

Simply run:
    yagi-feed

## Setting up a hub (if using PubSubHubub)

Download the Google App Engine SDK for Linux and add it to your path

    http://code.google.com/appengine/downloads.html

Then checkout the reference hub.

    svn checkout http://pubsubhubbub.googlecode.com/svn/trunk/ pubsubhubbub-read-only

Install pubsubhubbub_publisher for python

    cd pubsubhubbub-read-only/publisher_clients/python
    sudo python setup.py install

Start the hub

    cd pubsubhubbub-read-only
    dev_appserver.py hub/ -p<port number specified in yagi.conf>

## Testing subscriptions for PubSubHubub.

    cd yagi

    # You'll want to run this in multiple screen windows or terminal sessions, as the callback process
    # won't daemonize

    python subscriber/callback.py <sub_port>
    python subscriber/sub.py <topic> <callback> <hub>

    # I usually load other/push_rabbit.py in an iPython session
    cd other
    ipython
    import push_rabbit

    # the cast below is assuming you setting up yagi to listen on a queue named 'notifications.warn'
    push_rabbit.cast(dict(a=3), 'instance', 'notifications', 'warn')

You should see XML content being pushed to your window running callback.py, above.
