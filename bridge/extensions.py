import asyncio

from databases import Database

from bridge import settings


loop = asyncio.get_event_loop()
database = Database(
    settings.DATABASE['url']
)