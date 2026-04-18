from fastapi import APIRouter, Body, Depends, Request
from app.utils.schemas import RespoceModel, resp_200, resp_500
from app.service.tool import tool_service

api_router = APIRouter(prefix="/v1", tags=["Tool"])


@api_router.post("/regist_tool", response_model=RespoceModel)
async def tool(
    request: Request,
    name: str = Body(..., description="名字"),
    openai_schema: dict = Body(..., description="服务配置"),
    logo: str = Body(None, description="图标"),
    description: str = Body(None, description="描述"),
    auth_config: dict = Body(None, description="Auth"),
):
    user = request.state.user
    try:
        item = await tool_service.register(
            name, openai_schema, user, logo, description, auth_config
        )
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.get("/tool_list", response_model=RespoceModel)
async def tool_list(
    request: Request,
):
    user = request.state.user
    try:
        item = tool_service.get_tool_list(user_id=user.get("id", ""))
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.post("/modify_tool", response_model=RespoceModel)
async def tool(
    tool_id: str = Body(..., description="id"),
    name: str = Body(..., description="名字"),
    openai_schema: dict = Body(..., description="服务配置"),
    logo: str = Body(None, description="图标"),
    description: str = Body(None, description="描述"),
    auth_config: dict = Body(None, description="Auth"),
):
    try:
        item = await tool_service.modify_tool(
            name, openai_schema, logo, tool_id, auth_config, description
        )
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.delete("/del_tool", response_model=RespoceModel)
async def tool_del(
    tool_id: str = Body(..., embed=True, description="id"),
):
    try:
        item = tool_service.del_tool(tool_id)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)
