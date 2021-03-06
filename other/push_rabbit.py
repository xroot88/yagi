import datetime
import sys
import uuid

from carrot.connection import BrokerConnection
from carrot.messaging import Publisher

sys.path.insert(0, '../')

import yagi.config
import yagi.log


def cast(msg, event_type, topic, priority):
    yagi.config.setup(config_path='/etc/yagi.conf')
    conf = yagi.config.config_with('rabbit_broker')
    host = conf('host')
    port = conf('port')
    user = conf('user')
    exchange = conf('exchange')
    password = conf('password')
    vhost = conf('vhost')

    message_dict = {
        'message_id': str(uuid.uuid4()),
        'event_type': event_type,
        'publisher_id': 'some_publisher',
        'priority': priority,
        'timestamp': str(datetime.datetime.utcnow()),
        'payload': msg
        }
    conn = BrokerConnection(hostname=host, port=port, userid=user,
             password=password, virtual_host=vhost)
    publisher = Publisher(connection=conn, exchange=exchange,
            routing_key="%s.%s" % (topic, priority), durable=False,
            exchange_type='topic')
    publisher.send(message_dict)
    publisher.close()


def make_amqp_conn():
    """Sends a message on a topic without waiting for a response"""
    yagi.config.setup(config_path='/etc/yagi.conf')
    conf = yagi.config.config_with('rabbit_broker')
    host = conf('host')
    port = conf('port')
    user = conf('user')
    password = conf('password')
    vhost = conf('vhost')

    params = dict(hostname=host,
                  port=int(port),
                  userid=user,
                  password=password,
                  virtual_host=vhost)
    from carrot.connection import AMQPConnection
    conn = AMQPConnection(**params)
    return conn


def delete_queue(queue):
    conn = make_amqp_conn()
    x = conn.get_channel()
    x.queue_delete(queue)


def delete_exchange(exch):
    conn = make_amqp_conn()
    x = conn.get_channel()
    x.exchange_delete(exch)
