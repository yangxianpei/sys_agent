from datetime import datetime

from app.models.base import BaseModel

# 导入ORM映射相关的类型声明和字段映射函数
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Boolean, String, DateTime
from typing import List
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSON
import uuid


class Session(BaseModel):
    __tablename__ = "work_session"
    session_id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: uuid.uuid4().hex[:32]
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    agent: Mapped[str] = mapped_column(String(128), nullable=False)
    contexts: Mapped[dict] = mapped_column(JSON)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
