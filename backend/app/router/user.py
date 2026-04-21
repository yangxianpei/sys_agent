from fastapi import APIRouter, Body, Depends
from app.utils.schemas import RespoceModel, resp_200, resp_500
from app.service.user import user_service
from app.utils.jwt import verify_token
from app.service.mcp.mcpClient import mcp_servcie

api_router = APIRouter(prefix="/v1", tags=["用户"])


@api_router.get("/test")
async def test():
    await mcp_servcie.connect_http_mcp()
    return {"message": "Hello World"}


@api_router.post("/login", response_model=RespoceModel)
def login(
    username: str = Body(..., description="用户名"),
    password: str = Body(..., description="密码"),
):
    try:
        flag, message, exit_username = user_service.login(username, password)
        return resp_200(exit_username, message)
    except:
        return resp_500(None, "登录失败")


@api_router.post("/register", response_model=RespoceModel)
def register(
    username: str = Body(..., description="用户名"),
    password: str = Body(..., description="密码"),
    email: str = Body(description="邮箱"),
):
    try:
        res = user_service.register(username, password, email)
        return resp_200(res, "注册成功")
    except Exception as e:
        return resp_500(None, f"{e}")
