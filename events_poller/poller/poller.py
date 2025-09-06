import asyncio
from datetime import datetime
import httpx

from events_poller.logger import logger
from events_poller.models.enum import EventTypeEnum
from events_poller.models.models import EventModel
from events_poller.settings import GitHubApiConfig


class GitHubApiPoller:
    def __init__(self, gh_poller_config: GitHubApiConfig, queue: asyncio.Queue) -> None:
        self._queue = queue
        self._aclient = httpx.AsyncClient()
        self._config = gh_poller_config

    def _parse_response(self, response: httpx.Response) -> list[EventModel]:
        events = response.json()
        return [
            EventModel(
                event_id=e["id"],
                event_type=EventTypeEnum(e["type"]),
                actor_id=e["actor"]["id"],
                repository_id=e["repo"]["id"],
                repository_name=e["repo"]["name"],
                created_at=datetime.strptime(e["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                action=e["payload"]["action"],
            )
            for e in events
            if e["type"] in EventTypeEnum
        ]

    async def _fetch_data(self) -> list[EventModel]:
        try:
            res = await self._aclient.get(
                self._config.url,
                headers=self._config.headers.model_dump(),
                params=self._config.params.model_dump(),
            )
            res.raise_for_status()
        except httpx.HTTPStatusError:
            logger.exception("Http error from server", status_code=res.status_code)

        logger.info(
            "Data fetched successfuly from the GitHubApi", status_code=res.status_code
        )
        return self._parse_response(res)

    async def run(self) -> None:
        try:
            while True:
                data: list[EventModel] = await self._fetch_data()
                await self._queue.put(data)
                await asyncio.sleep(self._config.rate_limit)
        except Exception:
            logger.exception("poller.died")
