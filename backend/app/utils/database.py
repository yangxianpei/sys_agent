from sqlalchemy.orm.session import Session
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
import app.models  # noqa: F401
from app.config import Config
from app.utils.logger import get_logger
import traceback
from typing import Generator

logger = get_logger(__name__)

engine = create_engine(Config.DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)

Session_instance = sessionmaker[Session](bind=engine, autoflush=False, autocommit=False)


# 需要查询数据库的方法
@contextmanager
def db_session() -> Generator[Session, None, None]:
    session = Session_instance()
    try:
        yield session
    except Exception as e:
        logger.info(f"数据库会话错误:{e}")
        raise
    finally:
        session.close()


# 需要操作数据库的方法
@contextmanager
def db_transession()-> Generator[Session, None, None]:
    session = Session_instance()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"数据库事务错误:{e} {traceback.format_exc()}")
        raise
    except Exception as e:
        session.rollback()
        logger.info(f"数据库会话错误:{e} {traceback.format_exc()}")
        raise
    finally:
        session.close()


def init_db():
    try:
        logger.info("初始化数据表结构")
        # 使用引擎来创建数据库的表结构
        Base.metadata.create_all(engine)
        logger.info("数据表结构生成")
    except Exception as e:
        logger.error(f"初始化数据表结构失败{e}")
        raise


def seed_db():
    """初始化基础数据（幂等执行，可重复调用）。"""
    from app.models.llm import LLM
    from app.models.mcp import Mcp

    model = (Config.REASONING_MODEL_ID or "").strip()
    base_url = (Config.REASONING_BASE_URL or "").strip()
    api_key = (Config.REASONING_API_KEY or "").strip()

    with db_transession() as session:
        # 默认 LLM：配置不完整时仅跳过 LLM，不影响其他初始化（例如默认 MCP）。
        if not (model and base_url and api_key):
            logger.info("seed_db: 默认LLM配置不完整，跳过LLM初始化")
        else:
            exists = (
                session.query(LLM)
                .filter(
                    LLM.user_id.is_(None),
                    LLM.model == model,
                    LLM.base_url == base_url,
                )
                .first()
            )
            if exists:
                logger.info("seed_db: 默认LLM已存在，跳过插入")
            else:
                session.add(
                    LLM(
                        model=model,
                        base_url=base_url,
                        api_key=api_key,
                        user_id=None,
                    )
                )
                logger.info("seed_db: 默认LLM初始化完成")

        # 默认 MCP 列表：后续新增默认项，直接在此列表 append 即可。
        default_mcps = [
            {
                "name": "吃什么",
                "server_name": "howtocook-mcp",
                "type": "streamable_http",
                "url": "https://mcp.api-inference.modelscope.net/254a381cefa740/mcp",
            }
        ]

        for item in default_mcps:
            default_mcp_name = item["name"]
            default_mcp_server_name = item["server_name"]
            default_mcp_type = item["type"]
            default_mcp_url = item["url"]
            default_mcp_server_config = {
                "mcpServers": {
                    default_mcp_server_name: {
                        "type": default_mcp_type,
                        "url": default_mcp_url,
                    }
                }
            }
            exists_mcp = (
                session.query(Mcp)
                .filter(
                    Mcp.user_id.is_(None),
                    Mcp.name == default_mcp_name,
                )
                .first()
            )
            if exists_mcp:
                logger.info("seed_db: 默认MCP[%s]已存在，跳过插入", default_mcp_name)
                continue

            session.add(
                Mcp(
                    name=default_mcp_name,
                    user_name="system",
                    connect_type=default_mcp_type,
                    tools=[],
                    status=1,
                    user_id=None,
                    logo="",
                    server_config=default_mcp_server_config,
                )
            )
            logger.info("seed_db: 默认MCP[%s]初始化完成", default_mcp_name)
