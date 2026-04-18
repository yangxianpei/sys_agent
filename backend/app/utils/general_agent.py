from .database import db_session, db_transession
from app.utils.logger import get_logger
from app.schema.agent import AgentSchema
from langchain.agents import create_agent, AgentState
from sqlalchemy.orm.session import Session
from langchain_openai import ChatOpenAI
from app.models.agent import Agent
from app.models.tool import Tool
from app.models.mcp import Mcp
from app.models.knowledge import Knowledge, Knowledge_Doc
from app.utils.helper import build_tools_from_openapi
from app.utils.mcp import list_tools_for_service
import asyncio
import time
from langchain_core.messages import (
    BaseMessage,
    AIMessageChunk,
)
from typing import AsyncGenerator, List, Dict, Any, Optional, Tuple
from app.models.llm import LLM
import httpx
import re
from datetime import datetime
from langchain_core.tools import tool
from app.service.vectordb.milvus import milvus
from langchain.agents.middleware import wrap_tool_call
from langgraph.config import get_stream_writer

logger = get_logger(__name__)


@tool
def get_current_date() -> str:
    """获取当前系统日期（格式：YYYY-MM-DD）"""
    return datetime.now().strftime("%Y-%m-%d")


class GeneralAgent:
    def __init__(self, agent_config: AgentSchema):
        self.tool_ids = []
        self.mcp_ids = []
        self.knowledge_ids = []
        self.agent_config = agent_config
        self.agent = None
        # init_knowledge 会为每个知识库注册唯一 tool name -> 展示名
        self.tool_name_mapp: Dict[str, str] = {}

    async def emit_event(self, event):
        try:
            writer = get_stream_writer()
        except RuntimeError:
            return
        if writer is not None:
            writer(event)

    def setup_agent_middlewares(self):

        @wrap_tool_call
        async def add_tool_call_args(request, handler):
            tool = request.tool
            meta = (tool.metadata or {}) if tool else {}
            # 子 MCP 聚合工具等：由子 Agent 自己发流式事件，主 Agent 不再包一层 START/END
            skip_main = bool(
                meta.get("skip_main_agent_tool_middleware") or meta.get("mcp_tool")
            )
            if skip_main:
                return await handler(request)

            tool_name = (
                request.tool_call.get("name", "")
                if isinstance(request.tool_call, dict)
                else ""
            )
            name = self.tool_name_mapp.get(tool_name, tool_name)
            await self.emit_event(
                {
                    "status": "START",
                    "title": f"Agent - 执行可用工具: {name}",
                    "messages": f"正在调用工具 {name}...",
                }
            )
            try:
                tool_result = await handler(request)
            except Exception as e:
                # 必须先 END，否则前端会一直停在「进行中」
                await self.emit_event(
                    {
                        "status": "END",
                        "title": f"Agent - 执行可用工具: {name}",
                        "messages": f"调用失败: {type(e).__name__}: {e}",
                        "error": True,
                    }
                )
                raise
            await self.emit_event(
                {
                    "status": "END",
                    "title": f"Agent - 执行可用工具: {name}",
                    "messages": f"{tool_result}",
                }
            )
            return tool_result

        return [add_tool_call_args]

    def init_llm(self):
        with db_session() as session:
            llm_id = self.agent_config.get("llm_id", "")
            llm_config = session.query(LLM).filter(LLM.llm_id == llm_id).first()
            if llm_config:
                api_key = llm_config.api_key
                base_url = llm_config.base_url
                model = llm_config.model
                llm = ChatOpenAI(
                    model=model,
                    api_key=api_key,
                    base_url=base_url,
                    # 流式长连接：避免读超时过短；对端提前断连时 SDK 可重试整次请求
                    timeout=httpx.Timeout(600.0, connect=30.0, read=600.0),
                    max_retries=3,
                )
            return llm

    def _knowledge_tool_name(self, knowledge_ids) -> str:
        """每个知识库唯一 tool 名，便于区分调用与 tool_name_mapp 展示。"""
        if isinstance(knowledge_ids, (list, tuple)):
            key = "_".join(str(x) for x in knowledge_ids) if knowledge_ids else "empty"
        else:
            key = str(knowledge_ids)
        safe = re.sub(r"[^a-zA-Z0-9_-]", "_", key).strip("_") or "kb"
        name = f"knowledge_{safe}"
        return name[:64]

    def init_knowledge(self, knowledge_ids, name, des):
        # 动态说明不能用运行时写入的 __doc__（@tool 在定义时就会解析文档字符串）；
        # parse_docstring=True 且文档不符合 Google 规范时会触发 ValueError。
        tool_description = (
            f"此工具: {name}\n详情: {des}\n"
            "通过检索知识库获取信息。参数 query 为用户问题。"
        )
        unique_tool_name = self._knowledge_tool_name(knowledge_ids)
        self.tool_name_mapp[unique_tool_name] = f"知识库: {name}"

        @tool(unique_tool_name, parse_docstring=False, description=tool_description)
        async def retrival_knowledge(query: str) -> str:
            with db_session() as session:
                kids = knowledge_ids or []
                if not isinstance(kids, (list, tuple)):
                    kids = [kids]
                if not kids:
                    return ""
                doc_ids = (
                    session.query(Knowledge_Doc)
                    .filter(Knowledge_Doc.knowledge_id.in_(kids))
                    .all()
                )
                ids = [doc.id for doc in doc_ids]
                return milvus.search(query, ids)

        return retrival_knowledge

    async def init_config(self):
        with db_session() as session:
            try:
                result = []
                agent_id = self.agent_config.get("id", "")
                llm_id = self.agent_config.get("llm_id", "")

                agent_config = session.query(Agent).filter(Agent.id == agent_id).first()
                if agent_config:
                    tool_ids = agent_config.tool_ids
                    mcp_ids = agent_config.mcp_ids
                    knowledge_ids = agent_config.knowledge_ids or []
                    kds = (
                        session.query(Knowledge)
                        .filter(Knowledge.id.in_(knowledge_ids))
                        .all()
                    )
                    if kds:
                        for kd in kds:
                            result.append(
                                self.init_knowledge(kd.id, kd.name, kd.description)
                            )
                    tools = session.query(Tool).filter(Tool.tool_id.in_(tool_ids)).all()
                    for tool in tools:
                        result.extend(build_tools_from_openapi(tool.openai_schema))
                    mcps = session.query(Mcp).filter(Mcp.mcp_id.in_(mcp_ids)).all()
                    if mcps:
                        mcp_tool_lists = await asyncio.gather(
                            *[
                                list_tools_for_service(mcp.server_config, llm_id)
                                for mcp in mcps
                            ]
                        )
                        for mcp_tool in mcp_tool_lists:
                            if isinstance(mcp_tool, list):
                                result.extend(mcp_tool)
                            else:
                                result.append(mcp_tool)
                        # TODO 默认工具
                        # result.append(get_current_date)

                return result
            except Exception as e:
                raise e

    async def init_agent(self):
        if self.agent:
            return self.agent
        logger.info("开始初始化llm")
        llm = self.init_llm()
        logger.info("开始初始化MCp 和 tools")
        tools = await self.init_config()
        middleware = self.setup_agent_middlewares()
        self.agent = create_agent(model=llm, tools=tools, middleware=middleware)
        return self.agent

    def wrap_event(
        self,
        data: Any,
        subgraph_namespace: Optional[Tuple[str, ...]] = None,
    ):
        """发送流式事件（含子 MCP / 子图 custom）。

        subgraphs=True 时，子图里 get_stream_writer 写入的 payload 会作为 custom 冒泡；
        外层收到 (namespace, \"custom\", data)，可把 namespace 一并塞进 data 便于展示来源。
        """
        payload: Any = data
        if subgraph_namespace is not None:
            if isinstance(data, dict):
                payload = {**data, "subgraph_namespace": subgraph_namespace}
            else:
                payload = {
                    "payload": data,
                    "subgraph_namespace": subgraph_namespace,
                }
        event = {"type": "event", "timestamp": time.time(), "data": payload}
        return event

    async def astream(
        self, messages: List[BaseMessage]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式调用主方法。出错时 yield type=error，便于 SSE 展示；不再向调用方抛异常。"""
        response_content = ""
        try:
            # subgraphs=True：工具内嵌套的子 Agent（如 MCP 子图）里 get_stream_writer 的 custom
            # 才会进入外层流；此时每项为 (namespace, mode, payload)；未开子图流时为 (mode, payload)
            async for chunk in self.agent.astream(
                input={
                    "messages": messages,
                    "model_call_count": 0,
                    "user_id": 111,
                },
                stream_mode=["messages", "custom"],
                subgraphs=True,
            ):
                _ns = None
                if isinstance(chunk, tuple) and len(chunk) == 3:
                    _ns, mode, data = chunk
                elif isinstance(chunk, tuple) and len(chunk) == 2:
                    mode, data = chunk
                else:
                    continue

                if mode == "custom":
                    yield self.wrap_event(data, subgraph_namespace=_ns)
                elif mode == "messages":
                    if (
                        isinstance(data, (list, tuple))
                        and len(data) >= 1
                        and isinstance(data[0], AIMessageChunk)
                        and data[0].content
                    ):
                        response_content += data[0].content
                        yield {
                            "type": "response_chunk",
                            "timestamp": time.time(),
                            "data": {
                                "chunk": data[0].content,
                                "accumulated": response_content,
                            },
                        }
        except Exception as e:
            logger.exception("GeneralAgent.astream 失败: %s", e)
            yield {
                "type": "error",
                "timestamp": time.time(),
                "data": {
                    "message": str(e),
                    "error_type": type(e).__name__,
                },
            }
