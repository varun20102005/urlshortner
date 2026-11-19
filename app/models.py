
from datetime import datetime

from sqlalchemy import BigInteger, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class URL(Base):
    __tablename__ = "urls"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    short_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False
    )

    original_url: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )
    click_count: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(
    DateTime,
    nullable=True
    )