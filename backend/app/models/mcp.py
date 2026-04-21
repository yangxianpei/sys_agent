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


class Mcp(BaseModel):
    __tablename__ = "mcp_server"
    mcp_id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: uuid.uuid4().hex[:32]
    )
    server_config: Mapped[str] = mapped_column(JSON, nullable=False)

    logo: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"))
    user_name: Mapped[str] = mapped_column(String(128), nullable=False)
    connect_type: Mapped[str] = mapped_column(String(64), default=True, nullable=False)
    # description="sse ,stdio ,http"
    tools: Mapped[list[str]] = mapped_column(JSON)
    status: Mapped[int] = mapped_column(default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
