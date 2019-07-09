import aiohttp

from .utils import resolve_response, Response
from .mixin import LimitRateDriverMixin


class BaseDriver:
    def __init__(self, timeout=10, loop=None):
        self.timeout = timeout
        self._loop = loop

    async def get(self, url, params, timeout=None):
        '''
        :param url:
        :param params: dict of query params
        :return: response
        '''
        raise NotImplementedError

    async def post(self, url, data, timeout=None):
        '''
        :param url:
        :param data: dict of payload
        :return: response
        '''
        raise NotImplementedError

    async def put(self, url, params, timeout=None):
        '''
        :param params: dict of query params
        :return: response
        '''
        raise NotImplementedError

    async def delete(self, url, data, timeout=None):
        '''
        :param data: dict pr string
        :return: response
        '''
        raise NotImplementedError

    async def close(self):
        raise NotImplementedError


class HttpDriver(BaseDriver):
    def __init__(self, timeout=10, loop=None, session=None, auth=None, json_serialize=None):
        """
        Wrapper over async http clients,
        In Basic realisation session=aiohttp.ClientSession
        :param timeout:
        :param loop: required if api used not in main thread
        :param session: if try optimize and reuse connections
        :param auth:
        :param json_serialize: json.dumps function
        """
        super().__init__(timeout, loop)
        if not session:
            self.session = aiohttp.ClientSession(loop=loop, auth=auth, json_serialize=json_serialize)
        else:
            self.session = session

    async def get(self, url, timeout=None, *args, **kwargs):
        async with self.session.get(url, timeout=timeout or self.timeout, *args, **kwargs) as response:
            await resolve_response(response)
            return response

    async def post(self, url, timeout=None, *args, **kwargs):
        async with self.session.post(url, timeout=timeout or self.timeout, *args, **kwargs) as response:
            """
            Process response body before release response: ClientResponse 
            """
            await resolve_response(response)
            return response

    async def put(self, url, timeout=None, *args, **kwargs):
        async with self.session.get(url, timeout=timeout or self.timeout, *args, **kwargs) as response:
            await resolve_response(response)
            return response

    async def delete(self, url, timeout=None, *args, **kwargs):
        async with self.session.get(url, timeout=timeout or self.timeout, *args, **kwargs) as response:
            await resolve_response(response)
            return response

    async def close(self):
        await self.session.close()

    @property
    def closed(self):
        return self.session.closed


class LimitedHttpDriver(LimitRateDriverMixin, HttpDriver):
    pass
