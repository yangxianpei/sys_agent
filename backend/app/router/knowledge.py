from fastapi import APIRouter, Body, Form, Request, UploadFile, File
from app.utils.schemas import RespoceModel, resp_200, resp_500
from app.service.knowledge import knowledge_service
from app.schema.agent import Knowledge_Schema
from app.service.agent import agent_service
import uuid
from app.config import Config

api_router = APIRouter(prefix="/v1", tags=["knowledge"])


@api_router.post("/create_knowledge", response_model=RespoceModel)
async def create_knowledge(*, request: Request, knowledge: Knowledge_Schema):
    user = request.state.user
    try:
        item = knowledge_service.create_knowledge(
            user_id=user.get("id"), knowledge=knowledge
        )
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.post("/modify_knowledge", response_model=RespoceModel)
async def create_knowledge(*, knowledge: Knowledge_Schema):

    try:
        item = knowledge_service.modify_knowledge(knowledge=knowledge)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.get("/knowledge_list", response_model=RespoceModel)
async def knowledge_list(*, request: Request):
    user = request.state.user
    try:
        item = knowledge_service.knowledge_list(user_id=user.get("id"))
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.delete("/knowledge_del", response_model=RespoceModel)
async def knowledge_list(
    *, knowledge_id: str = Body(..., embed=True, description="knowledge_id")
):
    try:
        item = knowledge_service.knowledge_del(knowledge_id)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.post("/knowledge_upload_doc", response_model=RespoceModel)
async def upload_image(
    file: UploadFile = File(..., description="文件"),
    knowledge_id: str = Form(..., description="knowledge_id"),
):
    item = await knowledge_service.knowledge_upload_doc(file, knowledge_id)
    return resp_200(item)


@api_router.post("/knowledge_doc_list", response_model=RespoceModel)
async def knowledge_doc_list(
    knowledge_id: str = Body(..., embed=True, description="knowledge_id")
):
    try:
        item = knowledge_service.knowledge_doc_list(knowledge_id)
        return resp_200(item)
    except Exception as e:
        return resp_500(None, f"上传失败 {e}")
    except ValueError as e:
        return resp_500(None, f"{e}")


@api_router.delete("/knowledge_doc_del", response_model=RespoceModel)
async def knowledge_doc_del(doc_id: str = Body(..., embed=True, description="doc_id")):
    try:
        item = knowledge_service.knowledge_doc_del(doc_id)
        return resp_200(item)
    except Exception as e:
        return resp_500(None, f"删除失败 {e}")
    except ValueError as e:
        return resp_500(None, f"{e}")
