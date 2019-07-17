from typing import Dict, Optional, Any
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


def dfs(data: Any, path: Optional[str] = None):
    if isinstance(data, (dict,)):
        return "&".join(
            dfs(
                next_data,
                f"{path}[{key}]" if path else key
            )
            for key, next_data in data.items()
        )
    elif isinstance(data, (list, tuple)):
        return "&".join(
            dfs(
                next_data,
                f"{path}[{i}]" if path else i
            )
            for i, next_data in enumerate(data)
        )
    else:
        return f"{path}={str(data)}" if path else str(data)


def bitrix_urlencode(data):
    result = dfs(data)

    return result


def prepare_batch(calls: Dict) -> Dict[str, str]:
    commands = {}
    for name, call in calls.items():
        # TODO remove isinstance()
        if isinstance(call, str):
            command = call
        elif isinstance(call, (tuple, list)):
            try:
                command = '{}?{}'.format(call[0], bitrix_urlencode(call[1]))
            except IndexError:
                raise IncorrectCall(name, call)
        elif isinstance(call, dict):
            try:
                command = '{}?{}'.format(call['method'], bitrix_urlencode(call['params']))
            except KeyError:
                raise IncorrectCall(name)
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
