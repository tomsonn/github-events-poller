from datetime import datetime
from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql.functions import now

from events_poller.models.enum import EventTypeEnum


class Base(DeclarativeBase):
    pass


class Events(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    event_type: Mapped[EventTypeEnum] = mapped_column(
        SAEnum(EventTypeEnum), nullable=False, index=True
    )
    actor_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    repository_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    repository_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    action: Mapped[str] = mapped_column(String, nullable=False, index=True)
    inserted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=now()
    )
