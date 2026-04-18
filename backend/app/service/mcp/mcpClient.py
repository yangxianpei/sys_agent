from mcp.client.stdio import stdio_client

# 从mcp模块导入ClientSession和StdioServerParameters
from mcp import ClientSession, StdioServerParameters
from mcp.client.streamable_http import streamable_http_client
import json
from ..baseService import BaseService
from app.models.mcp import Mcp
from fastapi import HTTPException
from app.utils.image_manager import image_control
from app.utils.helper import is_json_equal


class McpServcie(BaseService):
    async def connect_http_mcp(self, url):
        async with streamable_http_client(url) as transport:
            # transport 通常是一个 tuple 或封装对象
            read, write = transport[:2]  # 关键：手动取前两个

            async with ClientSession(read, write) as session:
                await session.initialize()

                tools = await session.list_tools()
                tools_list = []
                for t in tools.tools:
                    tools_list.append(
                        {
                            "name": t.name,
                            "description": t.description,
                            "input_schema": t.inputSchema,
                        }
                    )

                return tools_list

    async def register_mcp(self, mcp_name, mcpServers, user: dict, logo=""):
        server_keys = list(mcpServers.keys())
        server_name = server_keys[0] if server_keys else None
        amap_maps = mcpServers.get(server_name, [])
        connect_type = amap_maps.get("type", "")
        url = amap_maps.get("url", "")
        tools = await self.connect_http_mcp(url)
        mcp_servers_json = {"mcpServers": mcpServers}
        with self.transession() as session:
            mcp = Mcp(
                name=mcp_name,
                user_name="admin",
                connect_type=connect_type,
                tools=tools,
                status=1,
                user_id=user.get("id", ""),
                logo=logo,
                server_config=mcp_servers_json,
            )
            session.add(mcp)
            session.flush()
            self.logger.info("添加mcp成功")

            return mcp.to_dict()

    async def del_mcp(self, mcp_id):
        with self.transession() as session:
            exit_mcp = session.query(Mcp).filter(Mcp.mcp_id == mcp_id).first()
            if exit_mcp is None:
                return "此ID不存在", []
            else:
                dict_mcp = exit_mcp.to_dict()
                image_path = dict_mcp.get("logo", "")
                if image_path:
                    image_control.del_image(image_path)
                session.delete(exit_mcp)
                return "删除成功", [dict_mcp]

    async def get_mcp_list(self, user_id):
        with self.transession() as session:
            mcp_list = session.query(Mcp).filter(Mcp.user_id == user_id).all()
            if mcp_list is not None:
                return [mcp.to_dict() for mcp in mcp_list]
            else:
                return []

    async def modify_mcp(self, mcp_name, mcp_id, mcpServers, logo):
        with self.transession() as session:
            exit_mcp = session.query(Mcp).filter(Mcp.mcp_id == mcp_id).first()
            if exit_mcp is None:
                return "此ID不存在", []
            else:
                exit_mcp.name = mcp_name
                dict_mcp = exit_mcp.to_dict()
                old_logo = dict_mcp.get("logo")
                if old_logo != logo:
                    image_control.del_image(old_logo)
                    exit_mcp.logo = logo
                server_config = dict_mcp.get("server_config")
                mcp_servers_json = {"mcpServers": mcpServers}
                if not is_json_equal(server_config, json.dumps(mcp_servers_json)):
                    server_keys = list(mcpServers.keys())
                    server_name = server_keys[0] if server_keys else None
                    amap_maps = mcpServers.get(server_name, [])
                    connect_type = amap_maps.get("type", "")
                    url = amap_maps.get("url", "")
                    tools = await self.connect_http_mcp(url)
                    exit_mcp.connect_type = connect_type
                    exit_mcp.tools = tools
                    exit_mcp.server_config = mcp_servers_json

                session.commit()
                session.refresh(exit_mcp)
                return "修改成功", [exit_mcp.to_dict()]


mcp_servcie = McpServcie()
