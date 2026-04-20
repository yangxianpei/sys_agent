from app.models.tool import Tool
from .baseService import BaseService
from app.utils.jwt import create_token
from app.models.user import User
from app.utils.helper import is_json_equal
from app.utils.image_manager import image_control
from app.utils.default_data import openapi_json1, openapi_json2, openapi_json3


class ToolService(BaseService):
    def __init__(self):
        super().__init__()

    async def register(
        self,
        name: str,
        openai_schema: dict,
        user: User,
        logo,
        description,
        auth_config=None,
    ):
        with self.transession() as session:
            try:
                user_id = user.get("id", "")
                tool = Tool(
                    name=name,
                    openai_schema=openai_schema,
                    user_id=user_id,
                    logo=logo,
                    type=2,
                    description=description,
                    auth_config=auth_config,
                )
                self.logger.info("添加工具成功")
                session.add(tool)
                session.flush()
                return tool.to_dict()
            except Exception as e:
                raise e

    def generate_sys_tool(self):
        default_tool = [openapi_json1, openapi_json2, openapi_json3]
        with self.transession() as session:
            tools = session.query(Tool).filter(Tool.user_id.is_(None)).all()
            if len(tools) == len(default_tool):
                return
            for tool in default_tool:
                title = tool.get("info", "").get("title", "")
                has_tool = (
                    session.query(Tool)
                    .filter(Tool.name == title, Tool.user_id.is_(None))
                    .first()
                )
                if has_tool is not None or not title:
                    continue
                tool = Tool(
                    name=title,
                    openai_schema=tool,
                    type=1,
                    description=title,
                )
                self.logger.info(f"添加{title}默认工具成功")
                session.add(tool)
                session.flush()

    def get_tool_list(self, user_id, tool_ids):
        self.generate_sys_tool()
        with self.session() as session:
            tools = session.query(Tool).filter(Tool.tool_id.in_(tool_ids)).all()
            result = []
            if tools:
                result.extend(tool.to_dict() for tool in tools)
            return result

    def get_tool_list_all(self, user_id):
        self.generate_sys_tool()
        with self.session() as session:
            tools = session.query(Tool).filter(Tool.tool_id == user_id).all()
            sys_tools = session.query(Tool).filter(Tool.user_id.is_(None)).all()
            result = [tool.to_dict() for tool in sys_tools]
            if tools:
                result.extend(tool.to_dict() for tool in tools)
            return result

    def del_tool(self, tool_id):
        with self.transession() as session:
            tool = session.query(Tool).filter(Tool.tool_id == tool_id).first()
            if tool:
                session.delete(tool)
                session.flush()
                return tool.to_dict()
            return None

    async def modify_tool(
        self,
        name: str,
        openai_schema: dict,
        logo,
        tool_id,
        auth_config=None,
        description="",
    ):
        with self.transession() as session:
            try:
                tool = session.query(Tool).filter(Tool.tool_id == tool_id).first()
                if not tool:
                    return None
                tool.name = name
                tool.description = description
                tool_dict = tool.to_dict()
                old_openai_schema = tool_dict.get("openai_schema", "")
                tool.auth_config = auth_config
                if not is_json_equal(old_openai_schema, openai_schema):
                    tool.openai_schema = openai_schema
                old_logo = tool_dict.get("logo", "")
                if logo != old_logo:
                    image_control.del_image(old_logo)
                    tool.logo = logo
                self.logger.info("更改工具成功")
                session.flush()
                session.refresh(tool)
                return tool_dict
            except Exception as e:
                raise e


tool_service = ToolService()
