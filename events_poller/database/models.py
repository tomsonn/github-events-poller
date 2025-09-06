from datetime import datetime
from sqlalchemy import DateTime, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from events_poller.models.enum import EventTypeEnum


class Base(DeclarativeBase):
    pass


class Events(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[EventTypeEnum] = mapped_column(
        SAEnum(EventTypeEnum), nullable=False, index=True
    )
    actor_id: Mapped[int] = mapped_column(Integer, nullable=False)
    repository_id: Mapped[int] = mapped_column(Integer, nullable=False)
    repository_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False
    )
    action: Mapped[str] = mapped_column(String, nullable=False, index=True)
