import pytest

from bridge.utils.bitrix24.utils import bitrix_urlencode, get_request_params, prepare_batch


@pytest.fixture
def fixture_batch_command_params():
    return {
        "test_dict": {
            "first": 1,
            "second": 2,
            "third": 3,
        },
        "test_list": [
            'first',
            'second',
            'third',
        ]
    }


def test_bitrix_urlencode(fixture_batch_command_params):
    output = "test_dict[first]=1&test_dict[second]=2&test_dict[third]=3" \
             "&test_list[0]=first&test_list[1]=second&test_list[2]=third"

    assert bitrix_urlencode(fixture_batch_command_params) == output


def test_get_request_params():
    in_put = [
        {
            "key": 1,
            "value": 11
        },
        {
            "key": 2,
            "value": 22
        }
    ]

    output = {
        1: 11,
        2: 22,
    }

    assert get_request_params(in_put) == output


@pytest.fixture
def fixture_batch_commands():
    return {
        "first_command": [
            "fixture1",
            {
                "1": 1,
                "2": 2,
                "3": 3,
            }
        ],
        "second_command": {
            "method": "fixture2",
            "params": {
                "1": 1,
                "2": 2,
                "3": 3,
            }
        },
        "third_command": "command_body"
    }


def test_prepare_batch(fixture_batch_commands):
    output = {}

    result = prepare_batch(fixture_batch_commands)

    for k, v in result.items():
        assert k in fixture_batch_commands
        assert isinstance(v, (str, ))


