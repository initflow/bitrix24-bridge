from starlette.routing import Route

from bridge.api.views import (
    Index,
)

routes = [
    Route(r'/', endpoint=Index, methods=["GET", "POST"]),
]
