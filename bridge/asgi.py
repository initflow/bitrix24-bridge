from bridge import settings
from bridge.app import create_app

"""
Module used for starting app with ASGI server as gunicorn

for gunicorn:

    >> gunicorn bridge.asgi:app -w 1 -k uvicorn.workers.UvicornWorker

"""
app = create_app(debug=settings.DEBUG)