from typing import Dict, Optional
from urllib.parse import urlencode

import aiohttp
import ujson

from .exceptions import IncorrectCall


def get_request_params(request_params):
    return {param['key']: param['value'] for param in request_params}


async def resolve_response(response: aiohttp.ClientResponse) -> Dict:
    """

    :param response:
    :return:
    """
    if not response:
        return {}
    try:
        # TODO check ujson.loads
        result = await response.json(loads=ujson.loads)
    except:
        result = {}
    return result


def prepare_batch(calls: Dict) -> Dict[str, str]:
    commands = {}
    for name, call in calls.items():
        # TODO remove isinstance()
        if isinstance(call, str):
            command = call
        elif isinstance(call, (tuple, list)):
            try:
                command = '{}?{}'.format(call[0], urlencode(call[1]))
            except IndexError:
                raise IncorrectCall(name, call)
        else:
            raise IncorrectCall(name, call)
        commands[name] = command
    return commands


class Response(object):
    __slots__ = [
        'status',
        'data',
        'url',
        'params',
    ]

    def __init__(self, data: Optional[Dict] = None,
                 url: Optional[str] = None,
                 status: int = 200,
                 params: Optional[Dict] = None
                 ):
        self.data = data or {}
        self.status = status
        self.url = url
        self.params = params