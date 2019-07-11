from typing import Union, Dict, List, Optional

import aiohttp

RETRY_CODES = {
    409, 429, 500, 502, 503, 504
}
HTTP_OK = 200


class Command:
    """
    Command object
    :param action: Optional[str] - action name (e.g. list, batch), if None or empty make post request
    :param method: str - e.g. profile, crm.product.list
    :param params: Optional[Dict] - json params for request
    :param meta: Dict - meta information, will be return with response (used only for sync request-response)
    """
    __slots__ = [
        'action',
        'method',
        'params',
        'meta',
    ]

    def __init__(self, **data):
        """

        :rtype: object
        """
        if data is None:
            data = {}

        for f in self.__slots__:
            setattr(self, f, data.get(f))

        if not self.action:
            """
            If action not defined, use default - single request
            """
            self.action = 'default'

    def data(self) -> dict:
        return {
            f: getattr(self, f) for f in self.__slots__
        }


class CommandResponse:
    """
    CommandResponse object
    :param action: Optional[str] - action name (e.g. list, batch), if None or empty make post request
    :param method: str - e.g. profile, crm.product.list
    :param params: Optional[Dict] - json params for request
    :param next: Optional[int] - for list requests next value, for feature build one response
    :param total: Optional[int] - for list requests total value
    :param meta: Dict - meta information, will be return with response (used only for sync request-response)
    """
    __slots__ = [
        'action',
        'method',
        'params',
        'result',
        'status_code',
        'next',
        'total',
        'meta',
    ]

    def __init__(self, cmd: Command,
                 status_code: int = HTTP_OK,
                 next: Optional[int] = None,
                 total: Optional[int] = None,
                 result: Optional[List[Dict]] = None,
                 ):
        if cmd is None:
            raise ValueError("cmd: Command should not be None")

        cmd_data = cmd.data()

        for f in self.__slots__:
            setattr(self, f, cmd_data.get(f))

        self.result = result or []
        self.status_code = status_code
        self.next = next
        self.total = total

        if result and (next is None or total is None) and len(self.result) == 1:
            """
            Special case, if result have single response
            """
            self.next = next or self.result[1].get('next')
            self.total = total or self.result[1].get('total')

    def data(self) -> dict:
        return {
            f: getattr(self, f) for f in self.__slots__
        }

    @staticmethod
    async def from_client_response(cmd: Command, response: aiohttp.ClientResponse) -> 'CommandResponse':
        """
        Build CommandResponse from Command and aiohttp.ClientResponse
        :param self:
        :param cmd:
        :param response:
        :return:
        """
        data = {}

        try:
            """
            response._body should be read in context manager before and saved in object cache
            """
            data = await response.json()
        except Exception as e:
            pass
            print(e)

        return CommandResponse(
            cmd=cmd,
            status_code=response.status,
            next=data.get('next'),
            total=data.get('total'),
            result=[data]
        )


class ResponseModem:

    @staticmethod
    def get_entity(data: CommandResponse):
        return data.data()

    def __new__(cls,
                data: Union[CommandResponse, List[CommandResponse]],
                many: bool = False, *args, **kwargs) -> Union[Dict, List]:
        """
        Convert CommandResponse Entity or List[CommandResponse] to message
        :param data:
        :param many:
        :param args:
        :param kwargs:
        :return:
        """
        if many:
            result = [
                cls.get_entity(data=unit) for unit in data
            ]
        else:
            result = cls.get_entity(data=data)

        return result
