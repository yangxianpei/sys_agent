from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from app.config import Config
from app.router.agent import api_router as agent_session_router
from app.router.com import api_router as com_router
from app.router.knowledge import api_router as knowledge_session_router
from app.router.llm import api_router as llm_router
from app.router.mcp import api_router as mcp_router
from app.router.tool import api_router as tool_router
from app.router.user import api_router
from app.router.work_session import api_router as work_session_router
from app.router.dialog import api_router as diolog_session_router
from app.router.agent_skill import api_router as agent_skill_session_router
from app.router.usage_stats import api_router as usage_stats_router
from app.utils.database import init_db, seed_db
from app.utils.jwt import verify_token
from app.utils.logger import get_logger

app = FastAPI(
    title="hello agent",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,  # 关闭 Swagger UI  # 关闭 ReDoc
)

logger = get_logger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router, prefix="/api")
app.include_router(mcp_router, prefix="/api", dependencies=[Depends(verify_token)])
app.include_router(com_router, prefix="/api", dependencies=[Depends(verify_token)])
app.include_router(tool_router, prefix="/api", dependencies=[Depends(verify_token)])
app.include_router(llm_router, prefix="/api", dependencies=[Depends(verify_token)])
app.include_router(
    work_session_router, prefix="/api", dependencies=[Depends(verify_token)]
)
app.include_router(
    agent_session_router, prefix="/api", dependencies=[Depends(verify_token)]
)
app.include_router(
    knowledge_session_router, prefix="/api", dependencies=[Depends(verify_token)]
)
app.include_router(
    diolog_session_router, prefix="/api", dependencies=[Depends(verify_token)]
)
app.include_router(
    agent_skill_session_router, prefix="/api", dependencies=[Depends(verify_token)]
)
app.include_router(
    usage_stats_router, prefix="/api", dependencies=[Depends(verify_token)]
)
BASE_DIR = Path(__file__).parent.parent
uploads_dir = BASE_DIR / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    "/uploads",
    StaticFiles(directory=str(uploads_dir)),
    name="uploads",
)


@app.on_event("startup")
async def startup_init_db():
    init_db()
    seed_db()


@app.exception_handler(FastAPIHTTPException)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException | FastAPIHTTPException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "data": None, "message": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"code": 422, "data": None, "message": str(exc)},
    )


def create_app():
    logger.info("初始化应用")
    init_db()
    seed_db()
    uvicorn.run(
        "app.init:app",
        host=Config.APP_HOST,
        port=Config.APP_PORT,
        reload=Config.APP_DEBUG,
    )
