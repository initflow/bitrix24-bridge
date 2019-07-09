from starlette.routing import Route

from bridge.api.views import (
    Index,
    Test,
    Auth,
)

routes = [
    Route(r'/', endpoint=Index, methods=["GET", "POST"]),
    Route(r'/test', endpoint=Test, methods=["GET", ]),
    Route(r'/auth', endpoint=Auth, methods=["GET", ]),

]
