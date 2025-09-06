from enum import StrEnum


class EventTypeEnum(StrEnum):
    WATCH_EVENT = "WatchEvent"
    PR_EVENT = "PullRequestEvent"
    ISSUES_EVENT = "IssuesEvent"
