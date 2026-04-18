from fastapi import APIRouter, Body, Depends, Request
from app.utils.schemas import RespoceModel, resp_200, resp_500
from app.service.user import user_service
from app.service.mcp.mcpClient import mcp_servcie


api_router = APIRouter(prefix="/v1", tags=["MCP"])


@api_router.post("/regist_mcp", response_model=RespoceModel)
async def regist_mcp(
    request: Request,
    mcp_name: str = Body(..., description="MCP名字"),
    mcpServers: dict = Body(..., description="MCP服务配置"),
    logo: str = Body(None, description="MCP图标"),
):
    user = request.state.user
    try:
        item = await mcp_servcie.register_mcp(mcp_name, mcpServers, user, logo)
        return resp_200(item)
    except Exception as e:
        return resp_500(None, f"添加失败 {e}")
    except ValueError as e:
        return resp_500(None, f"{e}")


@api_router.delete("/regist_mcp", response_model=RespoceModel)
async def regist_mcp(
    mcp_id: str = Body(..., embed=True, description="MCPid"),
):
    try:
        (message, items) = await mcp_servcie.del_mcp(mcp_id)
        return resp_200(items, message)
    except Exception as e:
        return resp_500(None, f"{e}")


@api_router.post("/regist_mcp_modify", response_model=RespoceModel)
async def regist_mcp(
    mcp_id: str = Body(..., embed=True, description="MCPid"),
    mcp_name: str = Body(..., description="MCP名字"),
    mcpServers: dict = Body(..., description="MCP服务配置"),
    logo: str = Body(None, description="MCP图标"),
):
    try:
        (message, items) = await mcp_servcie.modify_mcp(
            mcp_id=mcp_id, mcp_name=mcp_name, mcpServers=mcpServers, logo=logo
        )
        return resp_200(items, message)
    except Exception as e:
        return resp_500(None, f"{e}")


@api_router.get("/regist_mcp", response_model=RespoceModel)
async def regist_mcp(request: Request):
    try:
        user = request.state.user
        mcp_list = await mcp_servcie.get_mcp_list(user_id=user.get("id", ""))
        return resp_200(mcp_list, "获取成功")
    except Exception as e:
        return resp_500(None, f"{e}")
