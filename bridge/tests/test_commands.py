import math

import pytest

from bridge.utils.commands import Command, CommandResponse, ResponseModem
from bridge.utils.commands.utils import fast_div_ceil


def test_fast_div_ceil():
    assert fast_div_ceil(5, 3, 2) == 2

    for x in range(1, 100):
        for y in range(1, 100):
            res = math.ceil(x / y)
            assert fast_div_ceil(x, y, y - 1) == res
            assert fast_div_ceil(x, y) == res


@pytest.fixture
def fixture_command_data():
    return {
        'action': "action",
        'method': "method",
        'params': {"1": 1, "2": 2, "3": 3},
        'meta': {"meta": 42},
    }


def test_command_class(fixture_command_data):
    c = Command(**fixture_command_data)

    for k, v in c.data().items():
        assert k in fixture_command_data
        assert v == fixture_command_data[k]

    c = Command()

    assert c.action == 'default'
    assert c.method is None
    assert c.params == {}
    assert c.meta == {}


def test_command_response_class(fixture_command_data):
    command = Command(**fixture_command_data)

    response = CommandResponse(command)

    assert response.action == command.action
    assert response.method == command.method
    assert response.params == command.params
    assert response.meta == command.meta


def test_response_modem(fixture_command_data):
    command = Command(**fixture_command_data)
    response = CommandResponse(command)

    output = ResponseModem([response])

    assert isinstance(output, list)
    assert len(output) == 1

    for data in output:
        assert data == response.data()

    output = ResponseModem(response, many=False)

    assert not isinstance(output, list)
    assert isinstance(output, dict)

    assert output == response.data()


