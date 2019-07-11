# import asyncio
import asyncio
import warnings
from typing import Optional, Dict, Coroutine
from urllib.parse import urlencode

import aiohttp
import ujson

from bridge.utils.bitrix24.drivers import LimitedHttpDriver, HttpDriver
from .exceptions import *
from .utils import prepare_batch


class Request(object):
    """
    Lazy support object, always return coroutine
    """
    __slots__ = (
        '_api',
        '_method_name',
    )

    is_request = True

    def __init__(self, api: 'Bitrix24', method_name: str):
        self._api = api
        self._method_name = method_name

    @property
    def api(self):
        return self._api

    def __getattr__(self, method_name: str):
        return self.__class__(self._api, f"{self._method_name}.{method_name}")

    def __call__(self, **method_args) -> Coroutine:
        """
        Pseudo-async function
        :param method_args:
        :return: coroutine
        """

        if self.api.use_webhook and self.api.webhook_code:
            """
            Perform use webhook only
            """
            return self.api.call_webhook(
                method=self._method_name,
                params=method_args,
                code=self.api.webhook_code
            )

        return self.api.call_method(
            method=self._method_name,
            params=method_args
        )


class Bitrix24(object):
    _client_endpoint_template = 'https://{domain}/rest/'
    _oauth_endpoint_template = 'https://{domain}/oauth/{action}/'
    _webhook_endpoint_template = 'https://{domain}/rest/{user_id}/{code}/'

    TRANSPORTS = ['json', 'xml']

    # constant list() page size, it is not pagination param
    PAGE_SIZE = 50
    PAGE_SIZE_MINIS_ONE = PAGE_SIZE - 1  # fast math.ceil(x / y) coefficient

    timeout = 60

    _request_class = Request

    is_request = False

    _RETRY_HTTP_CODES = [500, 503]

    def __init__(self, domain: str, *,
                 code: Optional[str] = None,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 access_token: Optional[str] = None,
                 client_endpoint: Optional[str] = None,
                 expires_in: int = 3600,
                 refresh_token: Optional[str] = None,
                 scope: str = '',
                 server_endpoint: Optional[str] = None,
                 server_domain: Optional[str] = None,
                 transport: str = 'json',
                 user_id: int = 1,
                 webhook_code: Optional[str] = None,
                 auth_domain: Optional[str] = None,
                 loop=None,
                 driver: Optional[HttpDriver] = None,
                 use_webhook: bool = False,
                 ):
        """
        Api for Bitrix24

        :param domain: https://<domain>/
        :param code: auth code
        :param client_id:
        :param client_secret:
        :param access_token: if token already was requested
        :param client_endpoint: if used custom endpoint
        :param expires_in: by default expire time 3600 seconds = 1 hour
        :param refresh_token: refresh token, by default expire time 1 month
        :param scope:
        :param server_endpoint: if custom server endpoint
        :param transport:
        :param user_id:
        :param webhook_code:
        :param auth_domain:
        :param loop:
        :param driver:
        :param use_webhook:
        """
        if not loop:
            """
            Only if api used in main thread
            """

            loop = asyncio.get_event_loop()
        self._loop = loop

        if not driver:
            driver = LimitedHttpDriver

        self.driver = driver(
            # loop=loop,
            json_serialize=ujson.dumps
        )

        self.access_token = access_token
        self.client_id = client_id

        if client_endpoint:
            client_endpoint = client_endpoint.strip()
            if not client_endpoint.endswith('/'):
                warnings.warn(f"client_endpoint = {client_endpoint} must endswith a slash", ResourceWarning)
                client_endpoint += '/'

        self.client_endpoint = client_endpoint
        self.client_secret = client_secret

        domain = domain.strip()
        if domain.endswith('/') or domain.find('://') >= 0:
            warnings.warn(f"domain = {domain} must be without protocol and an ending slash", ResourceWarning)
            domain = domain.rstrip('/')

            p = domain.find('://')
            if p >= 0:
                domain = domain.split('://')[1]

        self.domain = domain
        self.expires_in = expires_in  # Tokens expire in 1 hour by default
        self.refresh_token = refresh_token
        self.scope = scope  # The default value means all available scopes

        if server_endpoint:
            if not server_endpoint.endswith('/'):
                warnings.warn(f"client_endpoint = {server_endpoint} must endswith a slash", ResourceWarning)
                server_endpoint += '/'

        self.server_endpoint = server_endpoint  # Must endswith a slash

        transport = transport.strip()
        if transport not in self.TRANSPORTS:
            raise IncorrectTransportType(f"transport should be one of {self.TRANSPORTS}")

        self.transport = transport
        self.auth_domain = auth_domain

        self.user_id = user_id  # The default value means current user
        self.webhook_code = webhook_code

        self.use_webhook = use_webhook

        self.code = code

        self.server_domain = server_domain

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        if self.driver and not self.driver.closed:
            try:
                await self.driver.close()
            except:
                pass

    def __getattr__(self, method_name):
        return self._request_class(self, method_name)

    def __call__(self, method_name, **method_kwargs):
        return getattr(self, method_name)(**method_kwargs)

    @property
    def tokens(self) -> Dict[str, str]:
        """
        Returns current access and refresh tokens of the instance.
        :return: dict Access and refresh tokens
        """
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token
        }

    def register_code(self, code):
        """
        Callback function for getting code
        :param code:
        :return:
        """
        self.code = code

    def _resolve_oauth_endpoint(self, action: str, query: Optional[Dict] = None) -> str:
        """
        Builds an OAuth URL with/out query parameters.
        :param action: str Action name of an OAuth endpoint
        :param query: dict Query parameters
        :return: str OAuth endpoint
        """
        endpoint = self._oauth_endpoint_template.format(
            domain=self.auth_domain or self.domain,
            action=action
        )
        if query is not None:
            endpoint += '?{}'.format(urlencode(query))
        return endpoint

    def _resolve_call_url(self, method, endpoint=None):
        return '{endpoint}{method}.{transport}'.format(
            endpoint=endpoint or self._resolve_client_endpoint(),
            method=method,
            transport=self.transport
        )

    def _resolve_client_endpoint(self) -> str:
        """
        Returns correct client endpoint even if wasn't provided.
        :return: str Client endpoint
        """
        return self.client_endpoint or self._client_endpoint_template.format(domain=self.domain)

    def _resolve_webhook_endpoint(self, code: Optional[str] = None):
        """
        Build an endpoint for webhook with authentication code.
        :param code:
        :return: str Webhook endpoint
        """
        return self._webhook_endpoint_template.format(
            domain=self.domain,
            user_id=self.user_id,
            code=code or self.webhook_code
        )

    async def _request_tokens(self, query: Dict) -> Dict:
        """
        The request handler of an OAuth tokens endpoint.
        :param query: dict Query parameters
        :return: dict
        """
        url = self._resolve_oauth_endpoint('token')
        try:
            response = await self.driver.get(url, params=query)
        except aiohttp.ClientError:
            response = {}
        return response

    async def request_tokens(self, code: Optional[str] = None, **extra_query) -> None:
        """
        Requests access and refresh tokens of a Bitrix24 server. See:
        https://training.bitrix24.com/rest_help/oauth/app_authentication.php
        :param code: str Authentication request code
        :param extra_query: dict Additional query parameters
        """
        query = extra_query.copy()
        query.update({
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code or self.code,
            'grant_type': 'authorization_code',
            'scope': self.scope
        })
        result: Dict = await self._request_tokens(query)
        self.access_token = result.get('access_token')
        self.client_endpoint = result.get('client_endpoint')
        self.domain = result.get('domain')
        self.expires_in = result.get('expires_in')
        self.refresh_token = result.get('refresh_token')
        self.scope = result.get('scope')
        self.server_endpoint = result.get('server_endpoint')
        self.user_id = result.get('user_id')

    async def refresh_tokens(self, **extra_query) -> None:
        """
        Refreshes class tokens by appropriate requested tokens.
        :param extra_query: dict Additional query parameters
        """
        query = extra_query.copy()
        query.update({
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        })
        result: Dict = await self._request_tokens(query)
        self.access_token = result.get('access_token')
        self.refresh_token = result.get('refresh_token')

    def resolve_authorize_endpoint(self, **extra_query) -> str:
        """
        Builds an authorize URL to request an authorization code from. See:
        https://training.bitrix24.com/rest_help/oauth/app_authentication.php
        a remote server using a browser.
        :param extra_query: dict Additional query parameters
        :return: str Authorize endpoint
        """
        query = extra_query.copy()
        query.update({
            'client_id': self.client_id,
            'response_type': 'code'
        })
        endpoint = self._resolve_oauth_endpoint('authorize', query=query)
        return endpoint

    async def call_method(self, method: str, params: Optional[Dict] = None) -> aiohttp.ClientResponse:
        """
        Requests any Bitrix24 method with/out parameters. See:
        https://training.bitrix24.com/rest_help/js_library/rest/callMethod.php
        :param method: str Dot-noted method name
        :param params: dict Request parameters
        :return: aiohttp.ClientResponse
        """

        if self.use_webhook:
            """
            If perform use_webhook, redirect commands
            """
            return await self.call_webhook(method=method, params=params)

        url: str = self._resolve_call_url(method)
        query = {
            'auth': self.access_token
        }
        try:
            response: aiohttp.ClientResponse = await self.driver.post(url, json=params, params=query)
        except aiohttp.ClientError:
            response = {}
        result = response
        return result

    async def call_batch(self, calls: Dict, halt_on_error: bool = False) -> aiohttp.ClientResponse:
        """
        Groups many single methods into a request. Can include macros
        to access the results of the previous calls in the batch. See:
        https://training.bitrix24.com/rest_help/js_library/rest/callBatch.php
        :param calls: dict Sub-methods with params
        :param halt_on_error: bool Halt on error
        :return: aiohttp.ClientResponse
        """
        result: aiohttp.ClientResponse = await self.call_method('batch', {
            'cmd': prepare_batch(calls),
            'halt': halt_on_error
        })
        return result

    async def call_bind(self, event: str, handler: str, auth_type=None) -> aiohttp.ClientResponse:
        """
        Installs a new event handler. See:
        https://training.bitrix24.com/rest_help/general/event_bind.php
        :param event: str Event name
        :param handler: str Handler URL
        :param auth_type: int User ID
        :return: aiohttp.ClientResponse
        """
        result: aiohttp.ClientResponse = await self.call_method('event.bind', {
            'auth_type': auth_type or self.user_id,
            'event': event,
            'handler': handler
        })
        return result

    async def call_unbind(self, event: str, handler: str, auth_type=None) -> aiohttp.ClientResponse:
        """
        Uninstalls a previously installed event handler. See:
        https://training.bitrix24.com/rest_help/general/event_unbind.php
        :param event: str Event name
        :param handler: str Handler URL
        :param auth_type: int User ID
        :return: aiohttp.ClientResponse
        """
        result: aiohttp.ClientResponse = await self.call_method('event.unbind', {
            'auth_type': auth_type or self.user_id,
            'event': event,
            'handler': handler
        })
        return result

    async def call_webhook(self, method: str, params: Dict = None, code: Optional[str] = None) -> aiohttp.ClientResponse:
        """
        Call a simplified version of rest-events and rest-teams that does not
        require a program to write.
        https://www.bitrix24.com/apps/webhooks.php
        :param method:
        :param code:
        :param params:
        :return: aiohttp.ClientResponse
        """
        endpoint = self._resolve_webhook_endpoint(code)
        url = self._resolve_call_url(method, endpoint=endpoint)

        try:
            response: aiohttp.ClientResponse = await self.driver.post(url, json=params)
        except aiohttp.ClientError as e:
            response = {}

        return response
