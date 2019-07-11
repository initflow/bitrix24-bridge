import asyncio
from abc import ABC, abstractmethod, ABCMeta

import aio_pika
import typing
import ujson
from aio_pika import ExchangeType

from bridge.conf import settings


class MessageProducer(ABC):

    @abstractmethod
    async def connect(self):
        raise NotImplemented

    @abstractmethod
    async def close(self):
        raise NotImplemented

    @abstractmethod
    async def send(self, message):
        raise NotImplemented

    class Meta:
        abstract = True


class RabbitMQProducer(MessageProducer):

    def __init__(self, connection_url=None, *,
                 host=None, port=None, user=None, password=None, routing_key=None,
                 exchange=None, exchange_durable=None, exchange_type=None,
                 virtual_host=None, loop=None):
        """
        Realisation of Message Producer for RabbitMQ
        Required connection_url or params
        :param connection_url: str - amqp://user:password@host:port/virtual_host
        :param host: str
        :param port: str
        :param user: str
        :param password: str
        :param routing_key: str
        :param exchange: str
        :param exchange_durable: bool
        :param exchange_type: ExchangeType
        :param virtual_host: str
        :param loop: event loop
        """
        self.connection_url = connection_url or settings.RABBITMQ_URL

        self.host = host or settings.RABBITMQ_HOST
        self.port = port or settings.RABBITMQ_PORT
        self.routing_key = routing_key or settings.RABBITMQ_ROUTING_KEY
        self.user = user or settings.RABBITMQ_USER
        self.password = password or settings.RABBITMQ_PASS
        self.exchange_name = exchange or settings.RABBITMQ_EXCHANGE
        self.virtual_host = virtual_host or settings.RABBITMQ_VIRTUAL_HOST
        self.exchange_durable = exchange_durable or settings.RABBITMQ_EXCHANGE_DURABLE
        self.exchange_type = exchange_type or ExchangeType.__members__.get(
            settings.RABBITMQ_EXCHANGE_TYPE.upper(), ExchangeType.TOPIC
        )
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self.connection = None
        self.channel = None
        self.exchange = None

    async def connect(self):
        if self.connection is None or self.connection.is_closed:
            if self.connection_url:
                self.connection = await aio_pika.connect_robust(self.connection_url)
            else:
                self.connection = await aio_pika.connect_robust(
                    host=self.host, port=self.port,
                    login=self.user, password=self.password,
                    virtualhost=self.virtual_host,
                    loop=self.loop,
                )
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                self.exchange_name, auto_delete=False, type=self.exchange_type,
                durable=self.exchange_durable
            )
        return self.connection

    async def close(self):
        if self.connection and self.connection.is_open:
            await self.connection.close()
            await self.channel.close()
            self.connection = None
            self.channel = None
            self.exchange = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def send(self, message: dict):
        if self.connection is None or self.exchange is None:
            await self.connect()

        body = ujson.dumps(message).encode()

        response = await self.exchange.publish(
            aio_pika.Message(body=body, content_type='application/json'),
            routing_key=self.routing_key
        )
        return response


class MessageConsumer(ABC):

    @abstractmethod
    def connect(self):
        raise NotImplemented

    @abstractmethod
    def close(self):
        raise NotImplemented

    @abstractmethod
    def receive(self, message):
        raise NotImplemented

    class Meta:
        abstract = True


class RabbitMQConsumer(MessageConsumer):

    def __init__(self, connection_url=None, *,
                 host=None, port=None, user=None, password=None, queue=None, queue_durable=None,
                 exchange=None, virtual_host=None, loop=None):
        """
        Realisation of Message Producer for RabbitMQ
        Required connection_url or params
        :param connection_url: str - amqp://user:password@host:port/virtual_host
        :param host: str
        :param port: str
        :param user: str
        :param password: str
        :param queue: str
        :param queue_durable: str
        :param exchange: str
        :param virtual_host: str
        :param loop: event loop
        """
        self.connection_url = connection_url or settings.RABBITMQ_URL
        self.virtual_host = virtual_host or settings.RABBITMQ_VIRTUAL_HOST
        self.host = host or settings.RABBITMQ_HOST
        self.port = port or settings.RABBITMQ_PORT
        self.queue = queue or settings.RABBITMQ_MESSAGE_QUEUE
        self.user = user or settings.RABBITMQ_USER
        self.password = password or settings.RABBITMQ_PASS
        self.exchange_name = exchange or settings.RABBITMQ_EXCHANGE
        self.queue_durable = queue_durable or settings.RABBITMQ_QUEUE_DURABLE
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self.connection = None
        self.channel = None
        self.exchange = None

    async def connect(self):
        if self.connection is None or self.connection.is_closed:
            if self.connection_url:
                self.connection = await aio_pika.connect_robust(self.connection_url)
            else:
                self.connection = await aio_pika.connect_robust(
                    host=self.host, port=self.port,
                    login=self.user, password=self.password,
                    virtualhost=self.virtual_host,
                    loop=self.loop,
                )
        return self.connection

    async def close(self):
        if self.connection and self.connection.is_open:
            self.connection.close()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def receive(self, callback):
        connection = await self.connect()

        channel = await connection.channel()

        queue = await channel.declare_queue(
            self.queue, auto_delete=False, durable=self.queue_durable
        )
        await queue.consume(callback)


class MessageClient(MessageProducer, MessageConsumer, ABC):
    class Meta:
        abstract = True


class RabbitMQClient(MessageClient):

    def __init__(self, connection_url=None, *,
                 host=None, port=None, user=None, password=None, queue=None, queue_durable=None,
                 routing_key=None,
                 exchange=None, exchange_type=None, exchange_durable=None, virtual_host=None, loop=None):
        """
        Realisation of Message Producer for RabbitMQ
        Required connection_url or params
        :param connection_url: str - amqp://user:password@host:port/virtual_host
        :param host: str
        :param port: str
        :param user: str
        :param password: str
        :param queue: str
        :param queue_durable: str
        :param exchange: str
        :param virtual_host: str
        :param loop: event loop
        """
        self.connection_url = connection_url or settings.RABBITMQ_URL
        self.virtual_host = virtual_host or settings.RABBITMQ_VIRTUAL_HOST
        self.host = host or settings.RABBITMQ_HOST
        self.port = port or settings.RABBITMQ_PORT
        self.queue = queue or settings.RABBITMQ_COMMAND_QUEUE
        self.user = user or settings.RABBITMQ_USER
        self.password = password or settings.RABBITMQ_PASS
        self.exchange_name = exchange or settings.RABBITMQ_EXCHANGE
        self.queue_durable = queue_durable or settings.RABBITMQ_QUEUE_DURABLE

        self.exchange_durable = exchange_durable or settings.RABBITMQ_EXCHANGE_DURABLE
        self.exchange_type = exchange_type or ExchangeType.__members__.get(
            settings.RABBITMQ_EXCHANGE_TYPE.upper(), ExchangeType.TOPIC
        )

        self.routing_key = routing_key or settings.RABBITMQ_ROUTING_KEY

        if loop is None:
            loop = asyncio.get_event_loop()

        self.loop = loop
        self.connection = None
        self.channel = None
        self.exchange = None

    async def connect(self):
        if self.connection is None or self.connection.is_closed:
            if self.connection_url:
                self.connection = await aio_pika.connect_robust(self.connection_url)
            else:
                self.connection = await aio_pika.connect_robust(
                    host=self.host, port=self.port,
                    login=self.user, password=self.password,
                    virtualhost=self.virtual_host,
                    loop=self.loop,
                )
                self.channel = await self.connection.channel()

                self.exchange = await self.channel.declare_exchange(
                    self.exchange_name, auto_delete=False, type=self.exchange_type,
                    durable=self.exchange_durable
                )
        return self.connection

    async def get_connection(self):
        if not self.connection or self.connection.is_closed:
            await self.connect()

        return self.connection

    async def get_channel(self):
        if not self.connection or self.connection.is_closed:
            await self.connect()

        if self.channel or self.channel.is_closed:
            """
            If connection is active, but channel closed
            """
            self.channel = await self.connection.channel()

        return self.channel

    async def close(self):
        if self.connection and self.connection.is_open:
            await self.connection.close()
            await self.channel.close()
            self.connection = None
            self.channel = None
            self.exchange = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def send(self, message: dict):
        if self.connection is None or self.exchange is None:
            await self.connect()

        body = ujson.dumps(message).encode()

        response = await self.exchange.publish(
            aio_pika.Message(body=body, content_type='application/json'),
            routing_key=self.routing_key
        )
        return response

    async def receive(self, callback):
        """
        Add listener on queue
        :param callback: function(aio_pika.IncomingMessage)
        :return:
        """
        channel = await self.get_channel()

        queue = await channel.declare_queue(
            self.queue, auto_delete=False, durable=self.queue_durable
        )
        return await queue.consume(callback)
