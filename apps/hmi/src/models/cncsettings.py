from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from ..db import db


class CNCSettings(db.Model):
    """
    CNC Settings Model
    """
    __tablename__ = 'cnc'

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(20), unique=True)
    value: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)

    def __repr__(self):
        return f"{self.key} = {self.value}"
