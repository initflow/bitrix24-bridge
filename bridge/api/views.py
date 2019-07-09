import aiohttp
from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from bridge.api.utils import get_debug_response
from bridge.conf import settings


class Index(HTTPEndpoint):

    async def get(self, request: Request, *args, **kwargs):
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        domain = request.query_params.get('domain')
        scope = request.query_params.get('scope')
        member_id = request.query_params.get('member_id')
        server_domain = request.query_params.get('server_domain')

        bx24 = settings.bitrix24
        bx24.register_code(code=code)
        bx24.scope = scope
        bx24.domain = domain
        bx24.server_domain = server_domain

        pars = {k: v for k, v in request.query_params.items()}

        return get_debug_response(**pars)

    async def post(self, request: Request, *args, **kwargs):
        return get_debug_response()


class Auth(HTTPEndpoint):
    async def get(self, request: Request, *args, **kwargs):
        bx24 = settings.bitrix24
        url = bx24.resolve_authorize_endpoint()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, allow_redirects=True) as response:
                await response.json()

        return JSONResponse(await response.json())


class Test(HTTPEndpoint):

    async def get(self, request: Request, *args, **kwargs):
        bx24 = settings.bitrix24
        r = await bx24.crm.productsection.list()

        r = await r.json()
        return JSONResponse(r)
