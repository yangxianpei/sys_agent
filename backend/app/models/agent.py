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


class Agent(BaseModel):
    __tablename__ = "agent"
    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: uuid.uuid4().hex[:32]
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(128), default="")
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"), nullable=True)
    logo: Mapped[str] = mapped_column(String(128), default="")
    is_custom: Mapped[int] = mapped_column(default=0)
    system_prompt: Mapped[str] = mapped_column(String(255), default="")
    llm_id: Mapped[str] = mapped_column(String(32))
    enable_memory: Mapped[int] = mapped_column(default=0)
    mcp_ids: Mapped[str] = mapped_column(JSON, default=[])
    tool_ids: Mapped[str] = mapped_column(JSON, default=[])
    agent_skill_ids: Mapped[str] = mapped_column(JSON, default=[])
    knowledge_ids: Mapped[str] = mapped_column(JSON, default=[])
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )
