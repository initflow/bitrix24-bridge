import uvicorn
import click

from bridge.app import create_app


def create_core():
    return create_app(debug=True, cli=True)


def init():
    """
    Init database, application
    :return:
    """


@click.group()
def cli():
    pass


@click.command()
@click.option('--host', default='0.0.0.0', help='Server host address')
@click.option('--port', default=8000, help='Server port')
@click.option('--log-level', default='info', help='Log level')
def run(host: str = '0.0.0.0', port: int = 8000, log_level: str = 'info'):
    uvicorn.run(create_core(), host=host, port=port, log_level=log_level)


@click.command()
@click.option('--host', default='0.0.0.0', help='Server host address')
@click.option('--port', default=8000, help='Server port')
@click.option('--log-level', default='info', help='Log level')
def debug(host: str = '0.0.0.0', port: int = 8000, log_level: str = 'info'):
    uvicorn.run(
        create_app(),
        host=host, port=port,
        log_level='debug',
        debug=True,
        reload=True,
        loop='uvloop',
        lifespan='on',
    )


cli.add_command(run)
cli.add_command(debug)

if __name__ == "__main__":
    cli()
