from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
import databases
from bridge import settings
from bridge.routes import routes


def create_app(debug=True, cli=False) -> Starlette:
    app = Starlette(
        debug=debug,
        routes=routes
    )

    app = configure_app(app, debug)

    return app


def configure_app(app: Starlette, debug=False) -> Starlette:
    if not debug:
        """
        Off Trusted Host checking and CORS for debug
        """
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
        app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_HOSTS)

    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

    return app


async def configure_extensions():
    pass


async def add_routes(app: Starlette) -> Starlette:
    app.routes.extend(routes)
    return app
