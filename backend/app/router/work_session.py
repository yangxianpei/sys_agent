from fastapi import APIRouter, Body, Depends, Request
from app.utils.schemas import RespoceModel, resp_200, resp_500
from app.service.work_session import work_session


api_router = APIRouter(prefix="/v1", tags=["session"])


@api_router.post("/create_session", response_model=RespoceModel)
async def create_session(
    request: Request,
    title: str = Body(..., description="title"),
    agent: str = Body(..., description="agent"),
    api_key: str = Body(..., description="api_key"),
):
    user = request.state.user
    try:
        item = await work_session.create_session(title, agent, user, api_key)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.get("/session_list", response_model=RespoceModel)
async def session_list(
    request: Request,
):
    user = request.state.user
    try:
        item = work_session.get_session_list(user_id=user.get("id", ""))
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.post("/get_session_by_id", response_model=RespoceModel)
async def get_session_by_id(
    session_id: str = Body(..., embed=True, description="session_id"),
):
    try:
        item = work_session.get_session(session_id=session_id)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.delete("/del_session_by_id", response_model=RespoceModel)
async def del_session_by_id(
    session_id: str = Body(..., embed=True, description="session_id"),
):
    try:
        item = work_session.del_llm(session_id=session_id)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


# @api_router.post("/modify_llm", response_model=RespoceModel)
# def modify_llm(
#     llm_id: str = Body(..., description="id"),
#     model: str = Body(..., description="名字"),
#     base_url: str = Body(..., description="base_url"),
#     api_key: str = Body(..., description="api_key"),
# ):
#     try:
#         item = llm_service.modify_llm(llm_id, model, base_url, api_key)
#         return resp_200(item)
#     except Exception as e:
#         return resp_500(None)


# @api_router.delete("/del_llm", response_model=RespoceModel)
# async def del_llm(
#     llm_id: str = Body(..., embed=True, description="llm_id"),
# ):
#     try:
#         item = llm_service.del_llm(llm_id)
#         return resp_200(item)
#     except Exception as e:
#         return resp_500(None)
