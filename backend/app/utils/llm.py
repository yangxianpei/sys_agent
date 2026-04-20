from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from typing import Any
from app.utils.helper import build_tools_from_openapi, openapi_to_tools
from app.service.tool import tool_service
import json
import threading
from uuid import UUID
from app.models.usage_stats import Usage_stats
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.messages.ai import UsageMetadata, add_usage
from langchain_core.outputs import ChatGeneration, LLMResult
from app.config import Config
from app.utils.logger import get_logger
from app.utils.database import db_transession, db_session
from app.models.mcp import Mcp
import asyncio
from app.utils.mcp import list_tools_for_service
from app.models.llm import LLM

logger = get_logger(__name__)


def _normalize_stream_merged_model_name(name: str | None) -> str | None:
    """修正 LangChain 流式合并 AIMessageChunk 时的 model_name 重复拼接。

    langchain_core.utils.merge_dicts 对同名 str 键用 += 合并，且仅对 id / output_version /
    model_provider 在值相等时跳过；model_name 会被拼成如 glm-4-flashglm-4-flash。
    若整串可反复对半拆分且两半相同，则折叠为单段（覆盖 2^k 次重复）。"""
    if not name or not isinstance(name, str):
        return name
    n = len(name)
    while n >= 2 and n % 2 == 0:
        half = n // 2
        if name[:half] == name[half:]:
            name = name[:half]
            n = len(name)
        else:
            break
    return name


def _token_usage_to_usage_metadata(raw: dict | None) -> UsageMetadata | None:
    """把 OpenAI / 兼容接口返回的 usage 字典转成 UsageMetadata（兜底）。"""
    if not raw or not isinstance(raw, dict):
        return None
    pt = raw.get("prompt_tokens")
    if pt is None:
        pt = raw.get("input_tokens")
    ct = raw.get("completion_tokens")
    if ct is None:
        ct = raw.get("output_tokens")
    tt = raw.get("total_tokens")
    if pt is None and ct is None and tt is None:
        return None
    pt_i = int(pt or 0)
    ct_i = int(ct or 0)
    tt_i = int(tt) if tt is not None else pt_i + ct_i
    return {
        "input_tokens": pt_i,
        "output_tokens": ct_i,
        "total_tokens": tt_i,
    }


class LLM_instance:
    def __init__(self):
        self.agent_name = "simple_agent"
        self.llm = None
        self.agent = None
        self.tools = None
        self.tools_schema = None
        self.user_id: str | None = None
        self.agent_id: str | None = None
        # 会话内各模型「最终」累计用量；usage_by_model[模型名]["total_tokens"] 为累计总 token
        self.usage_by_model: dict[str, UsageMetadata] = {}
        self._usage_lock = threading.Lock()

    def reset_usage_stats(self) -> None:
        with self._usage_lock:
            self.usage_by_model.clear()

    async def init_llm(self, llm_config: LLM):
        llm = ChatOpenAI(
            model=llm_config.get("model", ""),
            api_key=llm_config.get("api_key", ""),
            base_url=llm_config.get("base_url", ""),
            temperature=0,
            streaming=True,
            stream_usage=True,
        )
        self.llm_config = llm_config
        self.llm = llm
        return llm

    def getllm(self):
        # 自定义 base_url 时 LangChain 默认不开启 stream_usage，流式下 usage_metadata 常为空；
        # 显式 True 才会带 stream_options.include_usage（需上游 OpenAI 兼容 API 支持）
        llm = ChatOpenAI(
            model=Config.REASONING_MODEL_ID,
            api_key=Config.REASONING_API_KEY,
            base_url=Config.REASONING_BASE_URL,
            temperature=0,
            streaming=True,
            stream_usage=True,
        )
        return llm

    async def init_simple_chat(self, tools):
        self.reset_usage_stats()
        self.agent = create_agent(model=self.llm, tools=tools).with_config(
            {"callbacks": [ToolTraceHandler(self)]}
        )

    async def init_tools_schema(self, user_id):
        if not self.llm:
            self.user_id = str(user_id) if user_id is not None else None
        if not self.tools_schema:
            tools = tool_service.get_tool_list_all(user_id)
            tools_schema_list = []
            for tool in tools:
                openai_schema = tool.get("openai_schema")
                if openai_schema:
                    tools_schema_list.extend(openapi_to_tools(openai_schema))
            self.tools_schema = tools_schema_list
            return tools_schema_list
        return self.tools_schema

    async def init_tools(self, user_id, tool_ids):
        self.user_id = str(user_id) if user_id is not None else None
        tools = tool_service.get_tool_list(user_id, tool_ids)
        tool_list = []
        for tool in tools:
            openai_schema = tool.get("openai_schema")
            if openai_schema:
                tool_list.extend(build_tools_from_openapi(openai_schema))
            self.tools = tool_list
        return tool_list

    async def chat(self, tools):
        await self.init_simple_chat(tools)
        return self.agent

    async def init_mcp(self, mcp_ids):
        result = []
        with db_session() as session:
            mcps = session.query(Mcp).filter(Mcp.mcp_id.in_(mcp_ids)).all()
            if len(mcps):
                mcp_tool_lists = await asyncio.gather(
                    *[
                        list_tools_for_service(
                            mcp.server_config,
                            self,
                            llm_id=self.llm_config.get("llm_id"),
                        )
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


class ToolTraceHandler(AsyncCallbackHandler):
    def __init__(self, llm_instance):
        super().__init__()
        self.llm_instance = llm_instance

    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """每次 Chat 模型调用结束时触发；从 AIMessage.usage_metadata 累加 token（统计在这里）。"""
        try:
            generation = response.generations[0][0]
        except IndexError:
            return

        if not isinstance(generation, ChatGeneration):
            return

        message = generation.message
        if not isinstance(message, AIMessage):
            return

        # 优先 AIMessage.usage_metadata；流式且未开 stream_usage 时多为空，再试 LLMResult.llm_output["token_usage"]
        usage_metadata = message.usage_metadata
        if (
            not usage_metadata
            and response.llm_output
            and isinstance(response.llm_output, dict)
        ):
            usage_metadata = _token_usage_to_usage_metadata(
                response.llm_output.get("token_usage")
            )

        if not usage_metadata:
            logger.debug(
                "on_llm_end: 无 token 用量（上游未返回 usage 或不支持 stream_options）；"
                "model=%s llm_output_keys=%s",
                getattr(message, "response_metadata", None),
                (
                    list(response.llm_output.keys())
                    if isinstance(response.llm_output, dict)
                    else None
                ),
            )
            return

        model_name = (message.response_metadata or {}).get("model_name")
        if (
            not model_name
            and response.llm_output
            and isinstance(response.llm_output, dict)
        ):
            model_name = response.llm_output.get("model_name")
        model_name = _normalize_stream_merged_model_name(model_name) or "unknown"

        # 本轮 LLM 增量（落库）；累计 total_tokens 在合并后的 usage_by_model[model_name]
        incremental_in = int(usage_metadata["input_tokens"])
        incremental_out = int(usage_metadata["output_tokens"])

        with self.llm_instance._usage_lock:
            if model_name not in self.llm_instance.usage_by_model:
                self.llm_instance.usage_by_model[model_name] = usage_metadata
            else:
                self.llm_instance.usage_by_model[model_name] = add_usage(
                    self.llm_instance.usage_by_model[model_name],
                    usage_metadata,
                )
        cumulative = self.llm_instance.usage_by_model.get(model_name)
        logger.info(
            "token_usage model=%s cumulative_total_tokens=%s",
            model_name,
            cumulative.get("total_tokens") if cumulative else None,
        )

        uid = getattr(self.llm_instance, "user_id", None)
        agent_id = getattr(self.llm_instance, "agent_id", None)
        if uid:
            try:
                with db_transession() as session:
                    session.add(
                        Usage_stats(
                            model=model_name,
                            agent_id=agent_id,
                            user_id=uid,
                            input_tokens=str(incremental_in),
                            output_tokens=str(incremental_out),
                        )
                    )
            except Exception as e:
                logger.warning("usage_stats 写入失败: %s", e)

    async def on_tool_start(self, serialized, input_str: str, **kwargs):
        logger.debug("[tool_start] %s", input_str)

    async def on_chat_model_start(self, serialized, messages, **kwargs):
        return None

    async def on_tool_end(self, output, **kwargs):
        logger.debug("[tool_end] %s", output)
        return output

    def on_tool_error(self, error: BaseException, **kwargs: Any) -> Any:
        logger.warning("[tool_error] %s", error)


llm_instance = LLM_instance()
