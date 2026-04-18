from fastapi import APIRouter, Body, Depends, Request
from app.utils.schemas import RespoceModel, resp_200, resp_500
from app.service.llm import llm_service
from app.models.work_session import Session
from pydantic import BaseModel
from starlette.responses import StreamingResponse
import asyncio
import json
from app.schema.lingseek import LingSeekTask

api_router = APIRouter(prefix="/v1", tags=["LLM"])


@api_router.post("/regist_llm", response_model=RespoceModel)
async def regist_llm(
    request: Request,
    model: str = Body(..., description="名字"),
    base_url: str = Body(..., description="base_url"),
    api_key: str = Body(..., description="api_key"),
):
    user = request.state.user
    try:
        item = await llm_service.register(model, base_url, user, api_key)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.get("/llm_list", response_model=RespoceModel)
async def llm_list(
    request: Request,
):
    user = request.state.user
    try:
        item = llm_service.get_llm_list(user_id=user.get("id", ""))
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.post("/modify_llm", response_model=RespoceModel)
def modify_llm(
    llm_id: str = Body(..., description="id"),
    model: str = Body(..., description="名字"),
    base_url: str = Body(..., description="base_url"),
    api_key: str = Body(..., description="api_key"),
):
    try:
        item = llm_service.modify_llm(llm_id, model, base_url, api_key)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.delete("/del_llm", response_model=RespoceModel)
async def del_llm(
    llm_id: str = Body(..., embed=True, description="llm_id"),
):
    try:
        item = llm_service.del_llm(llm_id)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.post("/simple/chat", summary="工作台日常对话")
async def simple_chat(
    request: Request,
    query: str = Body(..., description="用户输入内容"),
    model_id: str = Body(..., description="模型ID"),
    session_id: str = Body(None, description="会话ID"),
):
    user = request.state.user
    return await llm_service.simple_chat(
        query, model_id, session_id, user_id=user.get("id", "")
    )


@api_router.post("/lingseek/guide_prompt", summary="工作台日常对话")
async def guide_prompt(
    request: Request,
    query: str = Body(..., embed=True, description="用户输入内容"),
):
    user = request.state.user

    async def general_generate():
        async for chunk in llm_service.lingseek_agent(
            query, user_id=user.get("id", "")
        ):
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(
        general_generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@api_router.post("/task_start", summary="灵寻开始执行任务")
async def task_start(
    *,
    request: Request,
    task: LingSeekTask,
):
    user = request.state.user

    async def general_generate():
        async for chunk in llm_service.lingseek_start(task, user_id=user.get("id", "")):
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(
        general_generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
