import asyncio

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from bridge.utils.amqp.handlers import AMQPHandler
from .extensions import ext
from .routes import routes
from .utils.amqp.amqp import RabbitMQConsumer, RabbitMQClient
from .utils.bitrix24.api import Bitrix24
from bridge import settings


def create_app(debug=True, cli=False) -> Starlette:
    app = Starlette(
        debug=debug,
        routes=routes
    )

    app = configure_app(app, debug)

    app.add_event_handler('startup', on_startup_event)
    app.add_event_handler('shutdown', on_shutdown_event)

    return app


async def on_startup_event(*args, **kwargs):
    # TODO maybe need load from db
    ext.bitrix24 = Bitrix24(
        code=settings.BITRIX24_CODE,
        domain=settings.BITRIX24_DOMAIN,
        client_id=settings.BITRIX24_CLIENT_ID,
        client_secret=settings.BITRIX24_CLIENT_SECRET,
        access_token=settings.BITRIX24_ACCESS_TOKEN,
        refresh_token=settings.BITRIX24_REFRESH_TOKEN,
        webhook_code=settings.BITRIX24_WEBHOOK_CODE,
        use_webhook=True,
    )

    ext.loop = asyncio.get_running_loop()

    ext.amqp_client = RabbitMQClient(
        loop=ext.loop
    )

    await ext.amqp_client.receive(
        callback=AMQPHandler(client=ext.amqp_client).handle
    )


async def on_shutdown_event(*args, **kwargs):
    # close Http Session connection
    ext.bitrix24.close()
    # close AMQP connection
    ext.amqp_client.close()


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
