from pydantic import BaseModel
from typing import Generic, TypeVar, Any
import traceback

# pydantic 校验库

# 创建泛型
DataT = TypeVar("DataT")


class RespoceModel(BaseModel, Generic[DataT]):
    """统一响应模型"""

    code: int
    message: str
    data: DataT | None


def resp_200(data: Any, message="SUCCESS") -> RespoceModel:
    return RespoceModel(code=200, message=message, data=data)


def resp_500(data: Any, message="ERROR") -> RespoceModel:
    return RespoceModel(
        code=500, message=f"{message} {traceback.format_exc()}", data=data
    )
