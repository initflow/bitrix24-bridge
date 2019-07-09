import asyncio

from aio_counter import AioCounter


def wait_free_slot(func):
    """
    decorator for request function
    1) try get slot from rpp queue or wait new free slot
    2) if get slot from rpr, try get slot from parallel queue or wait free slot
    :param func:
    :return:
    """

    async def wrapper(self, *args, **kwargs):
        await self._rate_limitter.inc(ttl=self.REQUEST_PERIOD)  # try get rpp slot
        response = await func(self, *args, **kwargs)
        return response

    return wrapper


class LimitRateDriverMixin:
    """
    Control request rate
    """
    REQUEST_PER_PERIOD = 100  # not more 100 request per period
    REQUEST_PERIOD = 20

    def __init__(self,
                 request_per_preiod: int = None,
                 requests_period: int = None,
                 *args, **kwargs
                 ):
        """
        _queue_parallel - control max parallel request
        _queue_rps - control request per period
        :param request_per_preiod:
        :param requests_period:
        :param max_parallel_request_count:
        """
        super().__init__(*args, **kwargs)

        self._rate_limitter = AioCounter(
            max_count=request_per_preiod or self.REQUEST_PER_PERIOD,
            start_count=0,
            ttl=requests_period or self.REQUEST_PERIOD
        )

        self._tik = 2  # seconds
        self._tak = 2  # seconds

        self.task = asyncio.ensure_future(self.dispatcher(), loop=self._loop)

    async def dispatcher(self):
        while True:
            await asyncio.sleep(self._tik, loop=self._loop)
            if self._rate_limitter.full():
                await asyncio.sleep(self._tak, loop=self._loop)
                try:
                    self._rate_limitter.dec_nowait()
                except:
                    pass

    @wait_free_slot
    async def get(self, *args, **kwargs):
        return await super().get(*args, **kwargs)

    @wait_free_slot
    async def post(self, *args, **kwargs):
        return await super().post(*args, **kwargs)

    @wait_free_slot
    async def put(self, *args, **kwargs):
        return await super().put(*args, **kwargs)

    @wait_free_slot
    async def delete(self, *args, **kwargs):
        return await super().delete(*args, **kwargs)

    async def close(self):
        await super().close()
        self._rate_limitter.close()
