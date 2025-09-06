import asyncio

from events_poller.logger import logger
from events_poller.poller.worker import DBWorker
from events_poller.settings import DatabaseConfig, poller_config


async def poll(queue: asyncio.Queue): ...


async def main() -> None:
    queue = asyncio.Queue(maxsize=poller_config.queue_size)
    workers = [
        asyncio.create_task(
            DBWorker(
                name=f"worker-{i + 1}", queue=queue, db_config=DatabaseConfig()
            ).work()
        )
        for i in range(poller_config.workers_count)
    ]
    scheduler = asyncio.create_task(poll())
    await asyncio.gather(scheduler, *workers)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception("event_poller.exception", error=str(e))
