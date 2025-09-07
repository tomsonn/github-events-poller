import asyncio
from datetime import datetime, timezone
import re
import httpx
from pydantic import AnyHttpUrl

from events_poller.logger import logger
from events_poller.models.enum import EventTypeEnum
from events_poller.models.models import EventModel, GitHubApiResponseMetaModel
from events_poller.settings import GitHubApiConfig, GitHubApiParams


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
            delta_time = rate_limit_reset_datetime - datetime.now(timezone.utc)
            return int(delta_time.total_seconds())

        return 0

    def _parse_pagination_link(self, headers: httpx.Headers) -> AnyHttpUrl | None:
        pattern = r'rel="next", <(.*)>;'
        link_header = headers.get("link", "")

        if link_candidates := re.search(pattern, link_header):
            pagination_link = link_candidates.group(1)
            logger.info("Link to next page found", pagination_link=pagination_link)
            return pagination_link

    def _parse_response(self, response: httpx.Response) -> list[EventModel]:
        events = response.json()
        return [
            EventModel(
                event_id=e["id"],
                event_type=EventTypeEnum(e["type"]),
                actor_id=e["actor"]["id"],
                repository_id=e["repo"]["id"],
                repository_name=e["repo"]["name"],
                created_at=datetime.fromisoformat(
                    e["created_at"].replace("Z", "+00:00")
                ),
                action=e["payload"]["action"],
            )
            for e in events
            if e["type"] in EventTypeEnum
        ]

    async def _fetch_data(
        self, url: AnyHttpUrl, params: GitHubApiParams | None = None
    ) -> GitHubApiResponseMetaModel:
        try:
            logger.info("Trying to fetch data from GitHubApi", url=str(url))
            res = await self._aclient.get(
                str(url),
                headers=self._config.headers.model_dump(),
                params=params.model_dump() if params else params,
            )
            res.raise_for_status()
        except httpx.HTTPStatusError:
            logger.warning("Http error from server", status_code=res.status_code)

        logger.info(
            "Data fetched successfuly from the GitHubApi", status_code=res.status_code
        )

        data = []
        if httpx.codes.is_success(res.status_code):
            data = self._parse_response(res)

        rate_limit = self._calculate_sleep(res.headers)
        sleep = max(self._config.rate_limit_base, rate_limit)
        pagination_link = self._parse_pagination_link(res.headers)

        return GitHubApiResponseMetaModel(
            data=data,
            sleep=sleep,
            rate_limited=rate_limit != 0,
            pagination_link=pagination_link,
        )

    async def run(self) -> None:
        try:
            # default values for the very first iteration
            url = self._config.url
            params = self._config.params

            while True:
                response_meta = await self._fetch_data(url, params)
                if response_meta.data:
                    await self._queue.put(response_meta.data)
                else:
                    logger.warning("No data fetched from the GitHubApi")

                # If we are forced to wait, or we fetched the full response available
                if response_meta.rate_limited or not response_meta.pagination_link:
                    logger.info("poller is going to sleep", sleep=response_meta.sleep)
                    url = self._config.url
                    params = self._config.params
                    await asyncio.sleep(response_meta.sleep)
                else:
                    logger.info("poller is skipping the sleep")
                    url = response_meta.pagination_link
                    params = None

        except Exception:
            logger.exception("poller.died")
