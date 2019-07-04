from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from webargs import fields
from webargs_starlette import use_args

from bridge.api.utils import get_debug_response


class Index(HTTPEndpoint):

    @use_args({"test": fields.Str(required=False)})
    async def get(self, request: Request):

        return get_debug_response()

    async def post(self, request: Request):
        return get_debug_response()


