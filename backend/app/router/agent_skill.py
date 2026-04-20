from fastapi import APIRouter, Body, Depends, Request
from app.utils.schemas import RespoceModel, resp_200, resp_500
from app.service.agent_skill import agent_skill_service
from app.schema.agent import (
    Agent_Skill_Schema,
    AgentSkillFileAddReq,
    AgentSkillFileUpdateReq,
)

api_router = APIRouter(prefix="/v1", tags=["Agent_skill"])


@api_router.post("/regist_agent_skill", response_model=RespoceModel)
async def regist_agent_skill(
    *,
    request: Request,
    name: str = Body(..., description="名字"),
    description: str = Body(..., description="描述"),
):
    user = request.state.user
    try:
        agent_skill = {"name": name, "description": description}
        user_id = user.get("id", "")
        item = agent_skill_service.create_agent_skill(
            user_id, Agent_Skill_Schema(**agent_skill)
        )
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.get("/list_agent_skill", response_model=RespoceModel)
async def list_agent_skill(
    *,
    request: Request,
):
    user = request.state.user
    try:
        user_id = user.get("id", "")
        item = agent_skill_service.list_agent_skill(user_id)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.delete("/del_agent_skill", response_model=RespoceModel)
async def del_agent_skill(
    *,
    id: str = Body(..., embed=True, description="id"),
):
    try:
        item = agent_skill_service.del_agent_skill(id)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.post("/file/add", summary="Agent Skill新增文件")
async def add_agent_skill_file(req: AgentSkillFileAddReq):
    try:
        result = agent_skill_service.add_agent_skill_file(**req.model_dump())
        return resp_200(data=result)
    except Exception as err:
        return resp_500(None, message=str(err))


@api_router.post("/file/update", summary="Agent Skill新增文件")
async def update(req: AgentSkillFileUpdateReq):
    try:
        path = req.path
        agent_skill_id = req.agent_skill_id
        content = req.content
        result = agent_skill_service.update_agent_skill_file(
            path, agent_skill_id, content
        )
        return resp_200(data=result)
    except Exception as err:
        return resp_500(None, message=str(err))
