from typing import Optional, Set, List, Union, Dict

import aiohttp

from bridge.utils.commands import RETRY_CODES


def fast_div_ceil(x: int, y: int, coeff: Optional[int] = None) -> int:
    """
    Fast math.ceil(x / y) analog

    without coeff as constant
    >>> timeit.timeit('(x + y - 1) // y', setup='x = 666; y = 50')
    Out: 0.09578710899950238

    with coeff as constant
    >>> timeit.timeit('(x + 49) // y', setup='x = 666; y = 50')
    Out: 0.06215050799801247


    Default math.ceil
    >>> timeit.timeit('math.ceil(x / y)', setup='import math; x = 666; y = 50')
    Out: 0.15119207400130108

    :param x:
    :param y:
    :param coeff:
    :return:
    """
    if coeff is None:
        coeff = y - 1
    return (x + coeff) // y


async def retry(
        async_func,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None,
        retry_codes: Union[Set, List] = RETRY_CODES,
        max_count: int = 3
) -> aiohttp.ClientResponse:
    """
    Wrapper over api func,
    :param max_count:
    :param async_func:
    :param retry_codes:
    :param args:
    :param kwargs:
    :return:
    """
    counter = 0
    work = True
    response = None

    while work:
        response = await async_func(
            *args,
            **kwargs
        )
        if response.status in retry_codes and counter < max_count:
            counter += 1
        else:
            work = False

    return response
