from enum import StrEnum


class EventTypeEnum(StrEnum):
    WATCH_EVENT = "WatchEvent"
    PR_EVENT = "PullRequestEvent"
    ISSUES_EVENT = "IssuesEvent"


class GraphTypeEnum(StrEnum):
    AVG_TIME = "avg-time"
    TOTAL_COUNT = "total-count"
