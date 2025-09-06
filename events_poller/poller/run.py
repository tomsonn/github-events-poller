import asyncio

from events_poller.controllers.database import DatabaseController
from events_poller.database.engine import Database
from events_poller.logger import logger
from events_poller.poller.poller import GitHubApiPoller
from events_poller.poller.worker import DBWorker
from events_poller.settings import DatabaseConfig, GitHubApiConfig, poller_config


async def main() -> None:
    # Create one database connection pool for all workers, they will acquire from it
    # pass it in the constructor of DBWorker
    db = Database(DatabaseConfig())
    controller = DatabaseController(db)

    # Create a queue with max_size where the data will be put and processed by workers
    queue = asyncio.Queue(maxsize=poller_config.queue_size)

    # Create a new tasks for workers handling data in a queue
    try:
        workers = [
            asyncio.create_task(
                DBWorker(
                    database=db,
                    controller=controller,
                    name=f"worker-{i + 1}",
                    queue=queue,
                ).work()
            )
            for i in range(poller_config.workers_count)
        ]

        # Create a new task for polling the data from GitHub
        scheduler = asyncio.create_task(
            GitHubApiPoller(gh_poller_config=GitHubApiConfig(), queue=queue).run()
        )

        # Add all tasks into event loop
        await asyncio.gather(scheduler, *workers)
    except Exception:
        raise
    finally:
        # Close connection gracefully
        await db.close_connection()


if __name__ == "__main__":
    try:
        # Create an event loop so tasks can be executed asynchronuosly
        asyncio.run(main())
    except Exception as e:
        logger.exception("event_poller.exception", error=str(e))
