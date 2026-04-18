from datetime import datetime

from app.models.base import BaseModel

# 导入ORM映射相关的类型声明和字段映射函数
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Boolean, String, DateTime
from typing import List
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from sqlalchemy.sql import func
import uuid


class User(BaseModel):
    __tablename__ = "user"
    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: uuid.uuid4().hex[:32]
    )
    email: Mapped[str] = mapped_column(String(128))
    username: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, index=True
    )
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    addresses: Mapped[List["Address"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Address(BaseModel):
    __tablename__ = "address"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"))
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    iphone_number: Mapped[int] = mapped_column(nullable=False)
    user: Mapped["User"] = relationship(back_populates="addresses")
