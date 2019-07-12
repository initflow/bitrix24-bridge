import json
from typing import Dict, Union, Any

import aio_pika
import ujson

from bridge.extensions import ext
from bridge.utils.amqp.amqp import MessageClient
from bridge.utils.commands import CommandResponse, ResponseModem
from bridge.utils.commands.handlers import BaseCommandHandler


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

    def __init__(self, client: MessageClient, command_handler: BaseCommandHandler = None):
        """
        Handle command message from RabbitMQ queue, start process and send result back
        :param client: amqp.MessageClient
        """
        self.client = client
        self.command_handler = command_handler or ext.command_handler

    async def handle(self, message: aio_pika.IncomingMessage) -> None:
        async with message.process() as msg:
            data = await self.json(msg.body)
            ext.logger.info(data)

            response: CommandResponse = await self.command_handler(data)

            response_data = {
                "result": ResponseModem(response)
            }

            await self.client.send(
                response_data
            )
