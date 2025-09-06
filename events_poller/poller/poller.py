import asyncio
from datetime import datetime, timezone
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

    def _calculate_sleep(self, headers: httpx.Headers) -> int:
        """Calculate sleep based on the response headers.

        Docs: https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api?apiVersion=2022-11-28#handle-rate-limit-errors-appropriately
        """
        retry_after = headers.get("retry-after")
        rate_limit_remaining = headers.get("x-ratelimit-remaining")
        rate_limit_reset = headers.get("x-ratelimit-reset")
        logger.info(
            "rate limiting related header values",
            retry_after=retry_after,
            rate_limit_remaining=rate_limit_remaining,
            rate_limit_reset=rate_limit_reset,
        )

        if retry_after:
            # Temporary rate limit
            return int(retry_after)

        # 0 requests remaining, wait till `x-ratelimit-reset` time
        if not int(rate_limit_remaining):
            if not rate_limit_reset:
                return self._config.rate_limit_hard

            rate_limit_reset_datetime = datetime.fromtimestamp(
                int(rate_limit_reset), tz=timezone.utc
            )
            delta_time = datetime.now(timezone.utc) - rate_limit_reset_datetime
            return int(delta_time.total_seconds())

        return 0

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

    async def _fetch_data(self) -> tuple[list[EventModel], int]:
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

        data = self._parse_response(res)
        sleep = max(self._config.rate_limit_base, self._calculate_sleep(res.headers))
        return data, sleep

    async def run(self) -> None:
        try:
            while True:
                data, sleep = await self._fetch_data()
                await self._queue.put(data)
                logger.info("poller is going to sleep", sleep=sleep)
                await asyncio.sleep(sleep)
        except Exception:
            logger.exception("poller.died")
