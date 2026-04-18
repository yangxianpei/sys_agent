from typing import Generic, TypeVar
from app.utils.logger import get_logger, Logger
from app.utils.database import db_session, db_transession, get_logger

T = TypeVar("T")


class BaseService(Generic[T]):
    def __init__(self):
        self.logger = get_logger(__name__)

    def session(self):
        return db_session()

    def transession(self):
        return db_transession()
