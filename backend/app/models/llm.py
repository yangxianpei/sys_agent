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
from sqlalchemy.dialects.postgresql import JSON


class LLM(BaseModel):
    __tablename__ = "llm"
    llm_id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: uuid.uuid4().hex[:32], index=True
    )
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    base_url: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    api_key: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
