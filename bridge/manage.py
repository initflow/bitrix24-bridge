import uvicorn

from bridge.app import create_app


def create_core():
    return create_app(debug=True, cli=True)


def init():
    """
    Init database, application
    :return:
    """


def run():
    uvicorn.run(create_core(), host='0.0.0.0', port=8000, log_level='info')


if __name__ == "__main__":
    init()
