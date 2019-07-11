import asyncio
from abc import ABC
from typing import Dict, List, Optional, Tuple

from bridge.utils.bitrix24.api import Bitrix24
from bridge.utils.commands import Command, CommandResponse
from bridge.extensions import ext
from bridge.utils.commands.utils import fast_div_ceil, retry


class BaseCommandHandler(ABC):
    """
    Command Handler interface

    all request method should return List[Dict] where in dict place response from Bitrix24
    """

    async def dispatch(self, data: Dict) -> Optional[Dict]:
        raise NotImplementedError

    async def __call__(self, *args, **kwargs):
        return await self.dispatch(*args, **kwargs)

    async def list(self, data: Command) -> List[CommandResponse]:
        """
        Get all entities, use pagination (start=<number>)
        :param data:
        :return: list of CommandResponse
        """
        raise NotImplementedError

    async def batch(self, cmd: Command) -> List[CommandResponse]:
        """
        Make batch request with pagination if command numbers more than 50
        :param cmd:
        :return: list of CommandResponse
        """
        raise NotImplementedError

    async def default(self, cmd: Command) -> List[CommandResponse]:
        """
        Make single request
        :param cmd:
        :return: list of CommandResponse
        """
        raise NotImplementedError

    class Meta:
        abstract = True


class CommandHandler(BaseCommandHandler):

    def __init__(self, bx_client: Optional[Bitrix24] = None):
        self.bx_client = bx_client or ext.bitrix24

    async def dispatch(self, data: Dict, *args, **kwargs):
        cmd = Command(**data)

        if not cmd.method:
            pass # TODO add logging
            print("Method is None")
            return

        response = None
        try:
            handler = getattr(self, cmd.action, self.default)
            response = await handler(cmd)
        except Exception as e:
            pass # TODO add logging
            print(e)
            return

        return response

    def __call__(self, *args, **kwargs):
        return self.dispatch(*args, **kwargs)

    async def list(self, cmd: Command) -> List[CommandResponse]:
        """
        Make requests with pagination, get all list() response
        :param cmd:
        :return: List[CommandResponse], len(return) == 1
        """

        # remove pagination param if it exist in params
        cmd.params.pop('start', 0)

        # make first request for getting next and total values
        first_request_response = await self.bx_client.call_method(cmd.method, params=cmd.params)

        first_request_data = await first_request_response.json()
        total = first_request_data.get('total', 0)

        # additional requests count, exclude first_request (-1)
        requests_count = max(
            0,
            fast_div_ceil(
                x=total,
                y=self.bx_client.PAGE_SIZE,
                coeff=self.bx_client.PAGE_SIZE_MINIS_ONE
            ) - 1
        )

        # no copy, because first_request_data not used without other data
        responses_data: List[Dict] = first_request_data.get('result')

        if requests_count > 0:
            """
            Composite requests to batch command,
            Exclude start = 0, case it first_request,
            """
            batch_command = Command(
                method="batch",
                params={
                    "cmd": {
                        str(i): {
                            "method": cmd.method,
                            "params": {
                                **cmd.params,
                                "start": i * self.bx_client.PAGE_SIZE
                            }
                        }
                        for i in range(1, requests_count + 1)
                    }
                }
            )

            batch_result = await self.batch(batch_command)

            for res in batch_result:
                responses_data.extend(
                    res.result
                )

        cmd_response = CommandResponse(
            cmd=cmd,
            status_code=first_request_response.status,
            total=first_request_data.get('total'),
            result=responses_data
        )

        return [cmd_response]

    async def batch(self, cmd: Command) -> List[CommandResponse]:
        """
        Make batch request with pagination if command numbers more than 50

        For each request in batch return CommandResponse

        :param cmd:
        :return: list of CommandResponse, len(return) >= 1
        """
        # create list[tuple] of commands
        commands: List[Tuple] = list(cmd.params.pop('cmd', None).items())

        sub_commands_count = fast_div_ceil(
            x=len(commands),
            y=self.bx_client.PAGE_SIZE,
            coeff=self.bx_client.PAGE_SIZE_MINIS_ONE
        )

        # split command by PAGE_SIZE
        sub_commands: List[List[Tuple]] = [
            commands[i: i + self.bx_client.PAGE_SIZE]
            for i in range(0, sub_commands_count, self.bx_client.PAGE_SIZE)
        ]

        responses = []

        for sub_command in sub_commands:
            response = await retry(
                self.bx_client.call_batch,
                kwargs={
                    'calls': {
                        name: command
                        for name, command in sub_command
                    }
                }
            )
            res = await CommandResponse.from_client_response(cmd=cmd, response=response)
            responses.append(res)

        return responses

    async def default(self, cmd: Command) -> List[CommandResponse]:
        """
        Make single request
        :param cmd:
        :return: list of CommandResponse, len(return) == 1
        """

        response = await retry(
            self.bx_client.call_method,
            kwargs={
                "method": cmd.method,
                "params": cmd.params
            }
        )

        cmd_response = await CommandResponse.from_client_response(cmd=cmd, response=response)

        return [cmd_response]
