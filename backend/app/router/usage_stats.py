from fastapi import APIRouter, Body, Depends, Request
from app.utils.schemas import RespoceModel, resp_200, resp_500
from app.service.usage_stats import usage_stats
from app.schema.agent import UsageStatsRequest

api_router = APIRouter(prefix="/v1", tags=["usage_stats"])


@api_router.get("/get_model", response_model=RespoceModel)
async def get_model(
    *,
    request: Request,
):
    user = request.state.user
    try:
        item = usage_stats.get_model(user_id=user.get("id"))
        return resp_200(item)
    except Exception as e:
        return resp_500(None, f"添加失败 {e}")
    except ValueError as e:
        return resp_500(None, f"{e}")


@api_router.get("/get_agent", response_model=RespoceModel)
async def get_model(
    *,
    request: Request,
):
    user = request.state.user
    try:
        item = usage_stats.get_agent(user_id=user.get("id"))
        return resp_200(item)
    except Exception as e:
        return resp_500(None, f"添加失败 {e}")
    except ValueError as e:
        return resp_500(None, f"{e}")


@api_router.post("/usage_count", response_model=RespoceModel)
async def get_model(*, request: Request, usageStatsRequest: UsageStatsRequest):
    user = request.state.user
    try:
        item = usage_stats.get_count(
            user_id=user.get("id"), usageStatsRequest=usageStatsRequest
        )
        return resp_200(item)
    except Exception as e:
        return resp_500(None, f"添加失败 {e}")
    except ValueError as e:
        return resp_500(None, f"{e}")


@api_router.post("/usage", response_model=RespoceModel)
async def get_model(*, request: Request, usageStatsRequest: UsageStatsRequest):
    user = request.state.user
    try:
        item = usage_stats.get_count_use(
            user_id=user.get("id"), usageStatsRequest=usageStatsRequest
        )
        return resp_200(item)
    except Exception as e:
        return resp_500(None, f"添加失败 {e}")
    except ValueError as e:
        return resp_500(None, f"{e}")
