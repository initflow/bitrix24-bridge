import asyncio
import os
from typing import List

from aiologger import Logger
from aiologger.formatters.base import Formatter
from aiologger.handlers.files import AsyncFileHandler
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.routing import Route

from bridge import settings
from bridge.utils.amqp.handlers import AMQPHandler
from bridge.utils.commands.handlers import CommandHandler
from .extensions import ext
from .routes import routes
from .utils.amqp.amqp import RabbitMQClient
from .utils.bitrix24.api import Bitrix24


def create_app(debug=True, cli=False) -> Starlette:
    """
    Should be sync
    :param debug:
    :param cli:
    :return:
    """
    app = Starlette(
        debug=debug,
        routes=routes
    )

    app = configure_app(app, debug)

    app.add_event_handler('startup', on_startup_event)
    app.add_event_handler('shutdown', on_shutdown_event)

    return app


async def on_startup_event(*args, **kwargs):
    """
    Setup runtime objects

    AMQP listener should start always after creating bitrix client and start main app
    :param args:
    :param kwargs:
    :return:
    """
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

    ext.command_handler = CommandHandler(ext.bitrix24)

    ext.loop = asyncio.get_running_loop()

    ext.amqp_client = RabbitMQClient(
        loop=ext.loop
    )

    configure_logger(ext.loop)

    # listener should start last
    await ext.amqp_client.receive(
        callback=AMQPHandler(
            client=ext.amqp_client,
            command_handler=ext.command_handler
        ).handle
    )

    ext.logger.info("App started")


async def on_shutdown_event(*args, **kwargs):
    """
    For graceful shutdown need stop clients: bitrix, amqp
    :param args:
    :param kwargs:
    :return:
    """
    # close Http Session connection
    ext.bitrix24.close()
    # close AMQP connection
    ext.amqp_client.close()


def configure_logger(loop):
    """
    Setup logger

    Logger should work with app in same loop

    :param loop:
    :return:
    """
    ext.logger = Logger.with_default_handlers(
        name='bitrix24-bridge',
        loop=loop
    )

    file_handler = AsyncFileHandler(
        filename=os.path.join(settings.LOGGING_DIR, 'bridge.log'),
        loop=loop,
    )

    # https://github.com/B2W-BIT/aiologger/issues/60
    file_handler.formatter = Formatter(
        fmt="%(levelname)s:%(asctime)s:%(pathname)s:%(lineno)d:%(message)s"
    )
    ext.logger.add_handler(
        file_handler
    )


def configure_app(app: Starlette, debug=False) -> Starlette:
    if not debug:
        """
        Off Trusted Host checking and CORS for debug
        """
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
        app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_HOSTS)

    # app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

    return app


async def add_routes(app: Starlette, routes: List[Route]) -> Starlette:
    """
    Manually adding routes to app
    :param app:
    :param routes:
    :return:
    """
    app.routes.extend(routes)
    return app
