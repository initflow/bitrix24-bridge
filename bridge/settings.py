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
