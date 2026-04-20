from app.service.agent import agent_service
import asyncio
from .baseService import BaseService
from app.utils.mcp import list_tools_for_service
from app.models.llm import LLM
from app.models.tool import Tool
from app.models.mcp import Mcp
from app.utils.helper import build_tools_from_openapi
from app.models.knowledge import Knowledge, Knowledge_Doc
from langchain_core.tools import tool
from app.service.vectordb.milvus import milvus
from app.models.agent_skill import AgentSkill
from app.utils.skill_agent import SkillAgent
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
import re
from app.config import Config
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent, AgentState
import json
from typing import Any, ClassVar, Dict, List
import time
from app.utils.logger import get_logger
from app.utils.llm import ToolTraceHandler
from langchain_core.messages.ai import UsageMetadata
import threading

logger = get_logger(__name__)


class MarsAgent(BaseService):
    def __init__(self, user_id):
        self.user_id = user_id
        self.get_llm()
        self.usage_by_model: Dict[str, UsageMetadata] = {}
        self._usage_lock = threading.Lock()
        self.agent_name = "Mars_agent"

    def init_normal_agent(self):
        self.normal_agent = create_agent(model=self.llm).with_config(
            {"callbacks": [ToolTraceHandler(self)]}
        )

    async def init_all_tool(self):
        tools = []
        tools.extend(await self.get_mcp())
        tools.extend(await self.get_tool())
        tools.extend(await self.get_kd())
        tools.extend(await self.get_skill())
        self.agent = create_agent(model=self.llm, tools=tools).with_config(
            {"callbacks": [ToolTraceHandler(self)]}
        )

    def get_llm(self):
        with self.session() as session:
            llm = session.query(LLM).filter(LLM.user_id == self.user_id).first()
            self.llm_id = llm.llm_id

        self.llm = ChatOpenAI(
            base_url=Config.REASONING_BASE_URL,
            model=Config.REASONING_MODEL_ID,
            api_key=Config.REASONING_API_KEY,
            max_retries=3,
        )

    async def get_mcp(self):
        with self.transession() as session:
            result = []
            mcps = session.query(Mcp).filter(Mcp.user_id == self.user_id).all()
            mcp_tool_lists = await asyncio.gather(
                *[
                    list_tools_for_service(mcp.server_config, self.llm_id)
                    for mcp in mcps
                ],
                return_exceptions=True,
            )
            for idx, mcp_tool in enumerate(mcp_tool_lists):
                if isinstance(mcp_tool, BaseException):
                    if isinstance(mcp_tool, asyncio.CancelledError):
                        raise mcp_tool
                    logger.warning(
                        "MCP list_tools 失败已跳过 user_id=%s index=%s: %s",
                        self.user_id,
                        idx,
                        mcp_tool,
                    )
                    continue
                if isinstance(mcp_tool, list):
                    result.extend(mcp_tool)
                else:
                    result.append(mcp_tool)
            return result

    async def get_tool(self):
        with self.transession() as session:
            result = []
            tools = session.query(Tool).filter(Tool.user_id == self.user_id).all()
            for tool in tools:
                result.extend(build_tools_from_openapi(tool.openai_schema))

            return result

    async def get_kd(self):
        with self.transession() as session:
            result = []
            kds = (
                session.query(Knowledge).filter(Knowledge.user_id == self.user_id).all()
            )
            for kd in kds:
                result.append(self.init_knowledge(kd.id, kd.name, kd.description))
            return result

    def init_knowledge(self, knowledge_ids, name, des):
        # 动态说明不能用运行时写入的 __doc__（@tool 在定义时就会解析文档字符串）；
        # parse_docstring=True 且文档不符合 Google 规范时会触发 ValueError。
        tool_description = (
            f"此工具: {name}\n详情: {des}\n"
            "通过检索知识库获取信息。参数 query 为用户问题。"
        )

        @tool(name, parse_docstring=False, description=tool_description)
        async def retrival_knowledge(query: str) -> str:
            with self.session() as session:
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

    async def get_skill(self):
        with self.transession() as session:
            result = []
            skills = (
                session.query(AgentSkill)
                .filter(AgentSkill.user_id == self.user_id)
                .all()
            )
            for skill in skills:
                result.extend(self.init_skill(skill.id, self.llm_id))

            return result

    def init_skill(self, skill_id, llm_id):
        # in_ 需要序列；GeneralAgent 传的是列表，此处每次传的是单个 id
        ids = (
            list(skill_id)
            if isinstance(skill_id, (list, tuple))
            else ([skill_id] if skill_id is not None else [])
        )
        if not ids:
            return []

        with self.session() as session:
            skills = session.query(AgentSkill).filter(AgentSkill.id.in_(ids)).all()
            agent_skill_as_tools = []

            def create_skill_agent_as_tool(agent_skill: AgentSkill):
                @tool(
                    agent_skill.as_tool_name,
                    parse_docstring=False,
                    description=agent_skill.description or "调用技能 Agent",
                )
                async def call_skill_agent(query: str) -> str:
                    skill_agent = SkillAgent(agent_skill, llm_id)
                    await skill_agent.init_skill_agent()
                    messages = await skill_agent.ainvoke([HumanMessage(content=query)])
                    return "\n".join([message.content for message in messages])

                return call_skill_agent

            for agent_skill in skills:
                agent_skill_as_tools.append(create_skill_agent_as_tool(agent_skill))

        return agent_skill_as_tools

    async def astream(self, messages):
        try:
            yield {
                "type": "response_chunk",
                "time": time.time(),
                "data": "#### 现在开始，我会边梳理思路边完成这项任务😊\n",
            }
            finally_answer = ""
            async for chunk in self.normal_agent.astream(
                input={"messages": messages}, stream_mode="messages"
            ):
                if self.reasoning_interrupt.is_set():
                    break
                msg, meta = self._extract_msg_meta(chunk)
                text = _chunk_text(msg)
                # messages 流里常有 tool_calls / 元数据帧，正文为空；跳过避免 SSE 里连续「空」
                if not text:
                    continue
                finally_answer += text
                yield {
                    "type": "reasoning_chunk",
                    "time": time.time(),
                    "data": text,
                }
        except Exception as e:
            logger.error(f"推理模型流式输出错误: {e}")

    def _extract_msg_meta(self, chunk):
        if isinstance(chunk, tuple) and chunk:
            if chunk[0] == "messages" and len(chunk) > 1:
                payload = chunk[1]
                if isinstance(payload, tuple) and payload:
                    msg = payload[0]
                    meta = (
                        payload[1]
                        if len(payload) > 1 and isinstance(payload[1], dict)
                        else {}
                    )
                    return msg, meta
                return payload, {}
            if len(chunk) == 2 and isinstance(chunk[1], dict):
                return chunk[0], chunk[1]
        return chunk, {}

    async def ainvoke_stream(
        self, messages: List[BaseMessage], messages2: List[BaseMessage]
    ):
        # 用于中断推理模型输出的事件
        self.reasoning_interrupt = asyncio.Event()
        self.is_call_tool = False

        async for reasoning_chunk in self.astream(messages2):
            yield reasoning_chunk

        # 带工具的 Mars Agent：messages 为主输出，custom 为 get_stream_writer；直接 yield，不用队列
        async for chunk in self.agent.astream(
            input={"messages": messages},
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
                self.is_call_tool = True
                payload = data
                if _ns is not None:
                    if isinstance(data, dict):
                        payload = {**data, "subgraph_namespace": _ns}
                    else:
                        payload = {"payload": data, "subgraph_namespace": _ns}
                yield {
                    "type": "event",
                    "time": time.time(),
                    "data": payload,
                }
            elif mode == "messages":
                if not isinstance(data, (list, tuple)) or len(data) < 1:
                    continue
                text = _chunk_text(data[0])
                if not text:
                    continue
                self.is_call_tool = True
                yield {
                    "type": "mars_chunk",
                    "time": time.time(),
                    "data": text,
                }


def _chunk_text(msg) -> str:
    if msg is None:
        return ""

    if isinstance(msg, tuple):
        # stream_mode="messages" 的 chunk 常见结构是:
        # (message_obj, meta) 或 ("messages", (message_obj, meta))
        if msg and msg[0] == "messages" and len(msg) > 1:
            payload = msg[1]
            if isinstance(payload, tuple) and payload:
                return _chunk_text(payload[0])
            return _chunk_text(payload)
        if len(msg) == 2 and hasattr(msg[0], "content") and isinstance(msg[1], dict):
            return _chunk_text(msg[0])
        for item in msg:
            if isinstance(item, dict):
                continue
            text = _chunk_text(item)
            if text:
                return text
        return ""

    if isinstance(msg, list):
        return "".join(_chunk_text(item) for item in msg)

    raw = getattr(msg, "content", msg)
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw
    if isinstance(raw, dict):
        if raw.get("type") == "text":
            return str(raw.get("text", ""))
        # langgraph/langsmith 的 meta 字典不应输出到前端
        return ""
    if isinstance(raw, list):
        parts = []
        for block in raw:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts)
    return str(raw)
