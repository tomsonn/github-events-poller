from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from events_poller.models.enum import EventTypeEnum


class Base(DeclarativeBase):
    pass


class Events(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int]
    event_type: Mapped[EventTypeEnum]
    actor_id: Mapped[int]
    repository_id: Mapped[int]
    repository_name: Mapped[str]
    created_at: Mapped[datetime]
    action: Mapped[str]
