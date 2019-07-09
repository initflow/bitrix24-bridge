import os

from environs import Env

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = Env()

DEBUG = env.bool('DEBUG', True)

if DEBUG:
    env.read_env(os.path.join(BASE_DIR, 'env.dev'))

SECRET_KEY = env.str("SECRET_KEY", "my$secret$key")

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', ['*'], subcast=str)
CORS_HOSTS = env.list('CORS_HOSTS', ['*'], subcast=str)

DATABASE = dict(
    driver=env.str("DB_DRIVER", 'postgresql'),
    user=env.str("DB_USER", 'postgres'),
    password=env.str("DB_PASSWORD", 'postgres'),
    host=env.str("DB_HOST", 'localhost'),
    port=env.str("DB_PORT", "5432"),
    dbname=env.str("DB_NAME", 'postgres'),
    url=env.str("DB_URL", None),
)

if DATABASE['url'] is None:
    """
    Build DATABASE url
    """
    DATABASE['url'] = f"{DATABASE['driver']}://{DATABASE['user']}" \
        f"{':' + DATABASE['password'] if DATABASE['password'] else ''}" \
        f"@{DATABASE['host']}{':' + DATABASE['port'] if DATABASE['port'] else ''}" \
        f"{'/' + DATABASE['dbname'] if DATABASE['dbname'] else ''}"

RABBITMQ_HOST = env.str("RABBITMQ_HOST", "127.0.0.1")
RABBITMQ_VIRTUAL_HOST = env.str("RABBITMQ_VIRTUAL_HOST", "/")
RABBITMQ_PORT = env.str("RABBITMQ_PORT", "5672")
RABBITMQ_USER = env.str("RABBITMQ_USER", "rabbitmq")
RABBITMQ_PASS = env.str("RABBITMQ_PASS", "rabbitmq")
RABBITMQ_EXCHANGE = env.str("RABBITMQ_EXCHANGE", "bitrix24")
RABBITMQ_ROUTING_KEY = env.str("RABBITMQ_ROUTING_KEY", "send.info")
RABBITMQ_MESSAGE_QUEUE = env.str("RABBITMQ_SEND_MESSAGE_QUEUE", "bitrix24-info")
RABBITMQ_QUEUE_DURABLE = env.bool("RABBITMQ_QUEUE_DURABLE", True)
RABBITMQ_EXCHANGE_DURABLE = env.bool("RABBITMQ_EXCHANGE_DURABLE", True)
RABBITMQ_EXCHANGE_TYPE = env.str("RABBITMQ_EXCHANGE_TYPE", "TOPIC")
RABBITMQ_COMMAND_QUEUE = env.str('RABBITMQ_COMMAND_QUEUE', "bitrix24-command")

RABBITMQ_URL = env.str("RABBITMQ_URL", None)

REQUESTS_PER_PERIOD = env.int('REQUESTS_PER_PERIOD', 100)
REQUESTS_PERIOD = env.int('REQUESTS_PERIOD', 15)

# Bitrix24 Settings

BITRIX24_CODE = env.str("BITRIX24_CODE", "")
BITRIX24_DOMAIN = env.str("BITRIX24_DOMAIN", '')
BITRIX24_CLIENT_ID = env.str("BITRIX24_CLIENT_ID", 'local..')
BITRIX24_CLIENT_SECRET = env.str("BITRIX24_CLIENT_SECRET", '')
BITRIX24_ACCESS_TOKEN = env.str("BITRIX24_ACCESS_TOKEN", '')
BITRIX24_REFRESH_TOKEN = env.str("BITRIX24_REFRESH_TOKEN", '')
BITRIX24_WEBHOOK_CODE = env.str("BITRIX24_WEBHOOK_CODE", '')
BITRIX24_USE_WEBHOOK = env.bool("BITRIX24_USE_WEBHOOK", True)
