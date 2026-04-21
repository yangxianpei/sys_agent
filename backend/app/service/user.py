from app.models.user import User
from app.utils.database import db_session, db_transession, get_logger
from .baseService import BaseService
from app.utils.jwt import create_token


class UserService(BaseService):
    def __init__(self):
        super().__init__()

    def register(self, username: str, password: str, email=""):
        with self.transession() as session:
            try:
                exit_username = (
                    session.query(User).filter(User.username == username).first()
                )
                if exit_username:
                    raise Exception("用户名已存在")
                user = User(username=username, password=password, email=email)
                self.logger.info("注册成功")
                session.add(user)
                session.flush()
                return user.to_dict()
            except Exception as e:
                raise e

    def login(self, username: str, password: str):
        with self.session() as session:
            try:
                exit_username = (
                    session.query(User).filter(User.username == username).first()
                )
                if exit_username:
                    token = create_token({"username": username, "id": exit_username.id})
                    return True, "登录成功", {**exit_username.to_dict(), "token": token}
                else:
                    raise Exception("用户名不存在")
            except Exception as e:
                self.logger.error("登录失败: %s", e)
                raise


user_service = UserService()
