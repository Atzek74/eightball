import asyncio

from fastapi import APIRouter

from lnbits.db import Database
from lnbits.helpers import template_renderer
from lnbits.tasks import create_permanent_unique_task
from loguru import logger

logger.debug("This logged message is from eightball/__init__.py, you can debug in your extension using 'import logger from loguru' and 'logger.debug(<thing-to-log>)'.")

db = Database("ext_eightball")

eightball_ext: APIRouter = APIRouter(
    prefix="/eightball", tags=["EightBall"]
)

eightball_static_files = [
    {
        "path": "/eightball/static",
        "name": "eightball_static",
    }
]


def eightball_renderer():
    return template_renderer(["eightball/templates"])


from .lnurl import *
from .tasks import wait_for_paid_invoices
from .views import *
from .views_api import *

scheduled_tasks: list[asyncio.Task] = []

def eightball_stop():
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as ex:
            logger.warning(ex)

def eightball_start():
    task = create_permanent_unique_task("ext_eightball", wait_for_paid_invoices)
    scheduled_tasks.append(task)