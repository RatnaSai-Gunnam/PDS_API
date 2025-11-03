from datetime import date
from sqlalchemy import String, Integer, Date
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class Legislator(Base):
    __tablename__ = "legislators"

    govtrack_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    birthday: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10))
    type: Mapped[str] = mapped_column(String(5))
    state: Mapped[str] = mapped_column(String(2))
    district: Mapped[int | None] = mapped_column(Integer, nullable=True)
    party: Mapped[str] = mapped_column(String(50))
    url: Mapped[str | None] = mapped_column(String(255), nullable=True)

