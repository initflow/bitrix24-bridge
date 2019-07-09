import json
from typing import Dict, Union, Any

import aio_pika
import ujson

from bridge.utils.amqp.amqp import MessageClient


class AbstractHandler(object):
    _json_loads = json.loads

    class Meta:
        abstract = True

    async def handle(self, message) -> None:
        raise NotImplementedError

    async def json(self, message: Union[str, bytes]) -> Any:
        """
        Parse JSON from string or bytes

        @override _json_loads to change processor

        :param message:
        :return:
        """
        return self._json_loads(message)


class AMQPHandler(AbstractHandler):

    _json_loads = ujson.loads

    def __init__(self, client: MessageClient):
        self.client = client

    async def handle(self, message: aio_pika.IncomingMessage) -> None:
        async with message.process() as msg:
            data = await self.json(msg.body)
            print(data)

            await self.client.send(data)
