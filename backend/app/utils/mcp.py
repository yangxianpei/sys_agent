from mcp import ClientSession, McpError, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from langchain_core.tools import StructuredTool
from app.utils.logger import get_logger
from pydantic import Field, create_model
import json
import asyncio
from app.utils.database import db_session
from langchain_openai import ChatOpenAI
from app.models.llm import LLM
from langchain.agents import create_agent
from typing import Any, Awaitable, Callable, List
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain.agents.structured_output import ToolStrategy
from app.schema.agent import MCPResponseFormat
from langchain.agents.middleware import wrap_tool_call
from datetime import datetime

logger = get_logger(__name__)
import httpx
import httpcore

from mcp.shared._httpx_utils import MCP_DEFAULT_SSE_READ_TIMEOUT, MCP_DEFAULT_TIMEOUT
from mcp.types import CONNECTION_CLOSED
from contextlib import asynccontextmanager
import anyio.lowlevel
from langgraph.config import get_stream_writer
from app.utils.openai_tool_name import sanitize_openai_tool_name


def _json_type_to_python(schema_type: str | None):
    mapping = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    return mapping.get(str(schema_type or "").lower(), str)


def _schema_type_to_example(schema_type: str | None):
    t = str(schema_type or "").lower()
    if t == "integer":
        return 1
    if t == "number":
        return 1.0
    if t == "boolean":
        return True
    if t == "array":
        return []
    if t == "object":
        return {}
    return "示例值"


def _normalize_input_schema(raw) -> dict:
    """统一为 MCP / LangChain 可用的 JSON Schema 对象。"""
    if isinstance(raw, dict):
        return raw
    return {"type": "object", "properties": {}, "required": []}


def _extract_tool_meta(tool) -> tuple[str, str, dict]:
    """从 MCP SDK Tool 或 LangChain BaseTool 提取名称、描述与 input schema。"""
    name = str(getattr(tool, "name", "") or "")
    description = str(getattr(tool, "description", "") or "")
    args_schema = getattr(tool, "args_schema", None)
    schema = None
    if args_schema is not None:
        if hasattr(args_schema, "model_json_schema"):
            schema = args_schema.model_json_schema()
        elif hasattr(args_schema, "schema"):
            schema = args_schema.schema()
    else:
        raw = getattr(tool, "inputSchema", None) or getattr(tool, "input_schema", None)
        if raw is None:
            schema = None
        elif isinstance(raw, dict):
            schema = raw
        elif hasattr(raw, "model_dump"):
            schema = raw.model_dump()
        else:
            schema = str(raw)
    return name, description, _normalize_input_schema(schema)


def _build_mcp_langchain_parts(tool_name: str, tool_desc: str, input_schema: dict):
    """单次遍历 properties，同时生成 Pydantic args_schema 与给 LLM 的完整描述。"""
    properties = input_schema.get("properties", {}) or {}
    required = set(input_schema.get("required", []) or [])
    fields = {}
    lines = []
    example = {}
    for pname, meta in properties.items():
        py_type = _json_type_to_python(meta.get("type"))
        default = ... if pname in required else None
        desc = str(meta.get("description", "") or "")
        fields[pname] = (py_type, Field(default=default, description=desc))
        p_type = str(meta.get("type", "string"))
        p_desc = str(meta.get("description", "") or "")
        enum_values = meta.get("enum", []) or []
        enum_text = f" 可选值: {enum_values}" if enum_values else ""
        req_text = "是" if pname in required else "否"
        desc_text = f" 说明: {p_desc}" if p_desc else ""
        lines.append(
            f"- {pname} | 类型: {p_type} | 必填: {req_text}{desc_text}{enum_text}"
        )
        example[pname] = _schema_type_to_example(p_type)
    required_text = "、".join(required) if required else "无（可传空对象）"
    schema_text = "\n".join(lines) if lines else "- 无参数"
    example_text = (
        json.dumps(example, ensure_ascii=False, indent=2) if example else "{}"
    )
    full_desc = f"""
MCP工具名: {tool_name}
简介: {tool_desc}
参数定义:
{schema_text}
必填参数名: {required_text}
调用参数JSON示例:
{example_text}

规则：
1. 严格按参数定义传参，键名必须与参数名完全一致
2. 不要臆造未定义参数，缺少必填参数时先补齐再调用
3. 重要:请使用当天最新日期为 {datetime.now().strftime("%Y-%m-%d")}
4. 调用后基于结果给出自然语言回答，不要原样输出JSON
5. 默认都要调用当日最新日期,请调用日期mcp
"""
    model_name = f"{tool_name.title().replace('_', '')}McpArgs"
    args_schema = create_model(model_name, **fields)
    return args_schema, full_desc


def _normalize_mcp_tool_result(tool_result):
    content_list = getattr(tool_result, "content", None) or []
    text_parts = []
    for item in content_list:
        text = getattr(item, "text", None)
        if text is None and isinstance(item, dict):
            text = item.get("text")
        if text is not None:
            text_parts.append(str(text))

    if text_parts:
        merged_text = "\n".join([t for t in text_parts if t.strip()])
        if merged_text.strip():
            return merged_text

    if hasattr(tool_result, "model_dump"):
        return json.dumps(tool_result.model_dump(), ensure_ascii=False)
    if isinstance(tool_result, dict):
        return json.dumps(tool_result, ensure_ascii=False)

    return str(tool_result)


def _should_retry_mcp_error(e: McpError) -> bool:
    """传输层错误经 MCP 会话转成 McpError（如 CONNECTION_CLOSED / 读超时）时可重试。"""
    code = e.error.code
    return code in (CONNECTION_CLOSED, httpx.codes.REQUEST_TIMEOUT)


async def _mcp_client_message_handler(message):
    """默认 message_handler 会吞掉读流里的 Exception；收到传输错误时抛出以触发会话清理与待处理请求的 CONNECTION_CLOSED。"""
    if isinstance(message, Exception):
        raise message
    await anyio.lowlevel.checkpoint()


async def _with_mcp_retry(
    op_name: str,
    coro_factory,
    max_attempts: int = 5,
    base_delay: float = 0.6,
):
    """网络类错误时重试；共尝试 max_attempts 次（含首次），仍失败则抛出最后一次异常。"""
    for attempt in range(1, max_attempts + 1):
        try:
            return await coro_factory()
        except McpError as e:
            if not _should_retry_mcp_error(e):
                raise
            last_error = e
        except (
            httpx.RemoteProtocolError,
            httpx.ReadError,
            httpx.TimeoutException,
            httpcore.RemoteProtocolError,
            httpcore.ReadError,
            httpcore.TimeoutException,
        ) as e:
            last_error = e

        if attempt >= max_attempts:
            logger.error(
                "%s failed after %s attempts, re-raising: %s",
                op_name,
                max_attempts,
                last_error,
            )
            raise last_error
        delay = base_delay * (2 ** (attempt - 1))
        logger.warning(
            f"{op_name} failed (attempt {attempt}/{max_attempts}), retry after {delay:.1f}s: {last_error}"
        )
        await asyncio.sleep(delay)
    raise RuntimeError(f"{op_name} failed unexpectedly")


async def _mcp_session_run(mcp_service, fn: Callable[[ClientSession], Awaitable[Any]]):
    """建立 transport + ClientSession.initialize() 后执行 fn(session)。"""
    async with mcp_transport_streams(mcp_service) as (read, write):
        async with ClientSession(
            read, write, message_handler=_mcp_client_message_handler
        ) as session:
            await session.initialize()
            return await fn(session)


@asynccontextmanager
async def mcp_transport_streams(mcp_service):
    cfg = get_first_mcp_server(mcp_service)
    if cfg.get("protocol") == "stdio":
        stdioServerParameters = StdioServerParameters(
            command=str(cfg.get("command") or ""),
            args=[str(arg) for arg in (cfg.get("args", []))],
            env={str(k): str(v) for k, v in cfg.get("env", {}).items()},
        )
        async with stdio_client(stdioServerParameters) as (read, write):
            yield read, write
    else:
        headers = {str(k): str(v) for k, v in (cfg.get("headers") or {}).items()}
        url = cfg.get("url") or ""
        async with mcp_httpx_client_factory(headers=headers) as http_client:
            async with streamable_http_client(url, http_client=http_client) as (
                read,
                write,
                _,
            ):
                yield read, write


def get_first_mcp_server(config: dict):
    servers = config.get("mcpServers", {})

    if not servers:
        return None
    name, server = next(iter(servers.items()))

    protocol = server.get("protocol") or server.get("type") or "streamable_http"
    return {
        "name": name,
        "protocol": protocol,
        "type": server.get("type"),
        "url": server.get("url"),
        "command": server.get("command"),
        "args": server.get("args", []),
        "env": server.get("env", {}),
        "headers": server.get("headers", {}),
    }


def mcp_httpx_client_factory(headers=None, timeout=None, auth=None):
    kwargs = {"follow_redirects": True}
    if timeout is None:
        kwargs["timeout"] = httpx.Timeout(
            MCP_DEFAULT_TIMEOUT, read=MCP_DEFAULT_SSE_READ_TIMEOUT
        )
    else:
        kwargs["timeout"] = timeout
    if headers is not None:
        kwargs["headers"] = headers
    if auth is not None:
        kwargs["auth"] = auth

    return httpx.AsyncClient(**kwargs)


def _safe_tool_name(name) -> str:
    if isinstance(name, str) and name.strip():
        return name.strip()[:128]
    if isinstance(name, (list, tuple)) and name:
        return _safe_tool_name(name[0])
    if name is None:
        return "mcp_sub_agent"
    return str(name).strip()[:128] or "mcp_sub_agent"


def _message_content_text(message) -> str:
    c = getattr(message, "content", "")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts = []
        for block in c:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            elif isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                parts.append(str(block.get("text", "")))
        return "\n".join(parts)
    return str(c)


def wrap_mcp_agent_as_structured_tool(mcp_agent, mcp_as_tool_name, description):
    safe_name = sanitize_openai_tool_name(_safe_tool_name(mcp_as_tool_name))
    safe_desc = str(description or "")[:4000]

    async def call_mcp_agent(query: str, config: RunnableConfig):
        messages = [
            SystemMessage(
                content="""
你是一个结果整合助手。

你会收到来自工具（MCP）的返回结果，请遵循以下规则：

1. 只基于工具返回的数据回答，不要编造或补充不存在的信息
2. 提炼关键信息，去除冗余内容
3. 用清晰、简洁的语言输出结果
4. 如果有多个结果，进行合理归纳或分点说明
5. 如果数据为空或不完整，明确说明“未查询到相关结果”
6. 不要输出工具调用过程或中间推理
7. 如果是查询mcp服务把查询的引用原地址链接也发出来

输出要求：
- 优先使用中文
- 结构清晰（必要时使用分点）
- 避免重复内容"""
            ),  # 系统角色
            HumanMessage(content=query),  # 用户问题
        ]
        msgs = await mcp_agent.ainvoke(messages, config=config)
        return "\n".join(_message_content_text(m) for m in msgs)

    return StructuredTool.from_function(
        coroutine=call_mcp_agent,
        name=safe_name,
        description=safe_desc,
        metadata={
            "skip_main_agent_tool_middleware": True,
            "mcp_tool": True,
        },
    )


def build_tool(mcp_service, t, used_names: set | None = None):
    tool_name, tool_desc, input_schema = _extract_tool_meta(t)
    api_tool_name = sanitize_openai_tool_name(tool_name, used=used_names)
    args_schema, full_desc = _build_mcp_langchain_parts(
        tool_name, tool_desc, input_schema
    )

    async def call_mcp_tool(_tool_name=tool_name, **kwargs):
        async def call(session: ClientSession):
            try:
                raw = await session.call_tool(_tool_name, arguments=kwargs)
                return _normalize_mcp_tool_result(raw)
            except Exception as e:
                raise e

        return await _with_mcp_retry(
            f"mcp.call_tool:{_tool_name}",
            lambda: _mcp_session_run(mcp_service, call),
        )

    return StructuredTool.from_function(
        coroutine=call_mcp_tool,
        name=api_tool_name,
        description=full_desc,
        args_schema=args_schema,
    )


async def list_tools_for_service(mcp_service, father_self, llm_id: str | None = None):
    async def list_from_session(session: ClientSession):
        try:
            tools_result = await session.list_tools()
            return getattr(tools_result, "tools", None) or []
        except Exception as e:
            raise e

    raw_tools = await _with_mcp_retry(
        "mcp.list_tools",
        lambda: _mcp_session_run(mcp_service, list_from_session),
    )

    used_names: set[str] = set()
    tools = [build_tool(mcp_service, t, used_names) for t in raw_tools]

    if not (llm_id and str(llm_id).strip()):
        return tools

    first_server = get_first_mcp_server(mcp_service) or {}
    server_label = str(first_server.get("name") or "MCP")
    mcp_agent = MCPAgent(tools, llm_id, father_self, server_name=server_label)
    structured_response = await mcp_agent.generate_name_description(tools)
    return wrap_mcp_agent_as_structured_tool(
        mcp_agent,
        structured_response.mcp_as_tool_name,
        structured_response.description,
    )


class MCPAgent:
    def __init__(self, tools, llm_id, father_self, server_name: str | None = None):
        from app.utils.llm import ToolTraceHandler

        self.tools = tools
        self.server_name = (server_name or "MCP").strip() or "MCP"
        self.llm = None
        self.agent = None
        middleware = self.setup_agent_middlewares()
        self.father_self = father_self
        with db_session() as session:
            llm_config = session.query(LLM).filter(LLM.llm_id == llm_id).first()
            if llm_config:
                self.llm = ChatOpenAI(
                    model=llm_config.model,
                    api_key=llm_config.api_key,
                    base_url=llm_config.base_url,
                    timeout=httpx.Timeout(600.0, connect=30.0, read=600.0),
                    max_retries=3,
                )
                self.agent = create_agent(
                    model=self.llm,
                    tools=self.tools,
                    middleware=middleware,
                ).with_config({"callbacks": [ToolTraceHandler(father_self)]})

    async def emit_event(self, event):
        try:
            writer = get_stream_writer()
        except RuntimeError:
            return
        if writer is not None:
            writer(event)

    async def ainvoke(
        self, messages: List[BaseMessage], config: RunnableConfig | None = None
    ) -> List[BaseMessage] | str:
        result = await self.agent.ainvoke({"messages": messages}, config=config)
        messages = []
        for message in result["messages"][:-1]:
            if not isinstance(message, HumanMessage) and not isinstance(
                message, SystemMessage
            ):
                messages.append(message)
        return messages

    async def generate_name_description(self, tools):
        from app.utils.llm import ToolTraceHandler

        tool_list = [
            {"name": n, "description": d, "input_schema": s}
            for n, d, s in (_extract_tool_meta(t) for t in tools)
        ]
        prompt = f"""请你根据工具描述来生成一个mcp_as_tool_name 和 description的Json数据格式
{json.dumps(tool_list, ensure_ascii=False)}
"""
        agent = create_agent(
            model=self.llm, response_format=ToolStrategy(MCPResponseFormat)
        ).with_config({"callbacks": [ToolTraceHandler(self.father_self)]})
        result = agent.invoke({"messages": [HumanMessage(content=prompt)]})
        return result["structured_response"]

    def setup_agent_middlewares(self):

        @wrap_tool_call
        async def add_tool_call_args(request, handler):
            tool_name = (
                request.tool_call.get("name", "")
                if isinstance(request.tool_call, dict)
                else ""
            )
            await self.emit_event(
                {
                    "status": "START",
                    "title": f"Sub-Agent - {self.server_name} 执行可用工具: {tool_name}",
                    "messages": f"正在调用工具 {tool_name}...",
                }
            )
            try:
                tool_result = await handler(request)
            except Exception as e:
                # 必须先 END，否则前端会一直停在「进行中」
                await self.emit_event(
                    {
                        "status": "END",
                        "title": f"Sub-Agent - {self.server_name} 执行可用工具: {tool_name}",
                        "messages": f"调用失败: {type(e).__name__}: {e}",
                        "error": True,
                    }
                )
                raise
            await self.emit_event(
                {
                    "status": "END",
                    "title": f"Sub-Agent - {self.server_name} 执行可用工具: {tool_name}",
                    "messages": f"{tool_result}",
                }
            )
            return tool_result

        return [add_tool_call_args]
