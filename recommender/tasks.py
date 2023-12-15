import os

from celery import Celery


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery(
    "proj",
    broker="amqp://guest@localhost//",
    backend="rpc://",
)


