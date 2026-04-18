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
