from starlette.responses import JSONResponse


def get_debug_response(**kwargs):
    return JSONResponse({
        "teta": "is_test"
    },
        **kwargs,
    )