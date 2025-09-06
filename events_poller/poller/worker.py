import asyncio
from events_poller.controllers.database import DatabaseController
from events_poller.database.engine import Database
from events_poller.logger import logger
from events_poller.models.models import EventModel


class DataInsertedMismatch(Exception): ...


class DBWorker:
    def __init__(
        self,
        database: Database,
        controller: DatabaseController,
        name: str,
        queue: asyncio.Queue,
    ) -> None:
        self._database = database
        self._controller = controller

        self._name = name
        self._queue = queue

    async def work(self) -> None:
        try:
            while True:
                data_to_process: list[EventModel] = await self._queue.get()
                logger.info("queue_task.found", worker_name=self._name)

                try:
                    data_inserted_count = await self._controller.insert_data_bulk(
                        data_to_process
                    )
                    if len(data_to_process) != data_inserted_count:
                        logger.warning(
                            "Number of queued data and stored data doesn't match. Most probably some duplicates were found",
                            diff=len(data_to_process) - data_inserted_count,
                        )
                    logger.info("queue_task.successful", worker_name=self._name)
                except Exception as e:
                    logger.exception(
                        "queue_task.error", worker_name=self._name, error=str(e)
                    )
                finally:
                    self._queue.task_done()
                    logger.info("queue_task.done")

        except Exception as e:
            logger.exception("worker.died", worker_name=self._name, error=str(e))
