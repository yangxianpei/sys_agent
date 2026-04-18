from fastapi import APIRouter, Body, Depends, Request, Query
from app.utils.schemas import RespoceModel, resp_200, resp_500
from app.service.llm import llm_service
from app.schema.agent import DialogSchema
from app.service.dialog import dialog_service

api_router = APIRouter(prefix="/v1", tags=["Dialog"])


@api_router.post("/create_dialog", response_model=RespoceModel)
async def create_agent(*, request: Request, dialog: DialogSchema):
    user = request.state.user
    try:
        item = dialog_service.create_dialog(user_id=user.get("id"), dialog=dialog)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.get("/diolog_list", response_model=RespoceModel)
async def diolog_list(*, request: Request):
    user = request.state.user
    try:
        item = dialog_service.dialog_list(user_id=user.get("id"))
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.delete("/diolog_del", response_model=RespoceModel)
async def diolog_del(dialog_id: str = Body(..., embed=True, description="名字")):
    try:
        item = dialog_service.delete_one(dialog_id)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)
