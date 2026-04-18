from fastapi import APIRouter, Body, Depends, Request, Query
from app.utils.schemas import RespoceModel, resp_200, resp_500
from app.service.llm import llm_service
from app.schema.agent import AgentSchema
from app.service.agent import agent_service
from starlette.responses import StreamingResponse
import json

api_router = APIRouter(prefix="/v1", tags=["Agent"])


@api_router.post("/create_agent", response_model=RespoceModel)
async def create_agent(*, request: Request, agent: AgentSchema):
    user = request.state.user
    try:
        item = await agent_service.create_agent(user_id=user.get("id"), agent=agent)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.get("/get_agent_all", response_model=RespoceModel)
async def get_agent_all(*, request: Request):
    user = request.state.user
    try:
        item = await agent_service.get_agent_all(user_id=user.get("id"))
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.get("/agent_all_list", response_model=RespoceModel)
async def agent_all_list(*, request: Request):
    user = request.state.user
    try:
        item = await agent_service.agent_list(user_id=user.get("id"))
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.post("/modfy_agent", response_model=RespoceModel)
async def modfy_agent(*, agent: AgentSchema):
    try:
        item = await agent_service.modif_agent(agent=agent)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.delete("/del_agent", response_model=RespoceModel)
async def del_agent(
    agent_id: str = Body(..., embed=True, description="agent_id"),
):
    try:
        item = agent_service.del_agent(agent_id)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.get("/get_agent_by_id", response_model=RespoceModel)
async def get_agent_by_id(*, id: str = Query(None, embed=True, description="id")):
    try:
        item = await agent_service.get_agent_by_id(id)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.post("/search_agent", response_model=RespoceModel)
async def search_agent(*, name: str = Body(..., embed=True, description="name")):
    try:
        item = agent_service.search_agent(name)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.post("/completion", response_model=RespoceModel)
async def completion(
    *,
    dialog_id: str = Body(..., embed=True, description="name"),
    user_input: str = Body(..., embed=True, description="user_input"),
):
    async def general_generate():
        async for chunk in agent_service.completion(dialog_id, user_input):
            yield chunk

    return StreamingResponse(
        general_generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
