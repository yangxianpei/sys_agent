from datetime import datetime

from app.models.base import BaseModel

# 导入ORM映射相关的类型声明和字段映射函数
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Boolean, String, DateTime, JSON
from typing import List
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from sqlalchemy.sql import func
import uuid


class Tool(BaseModel):
    __tablename__ = "tool_server"
    tool_id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: uuid.uuid4().hex[:32]
    )
    auth_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    description: Mapped[str] = mapped_column(String(128))
    openai_schema: Mapped[str] = mapped_column(JSON, nullable=False)
    logo: Mapped[str] = mapped_column(String(128), nullable=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"), nullable=True)
    type: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
