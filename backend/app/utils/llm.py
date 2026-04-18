from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from typing import Any
from app.utils.helper import build_tools_from_openapi, openapi_to_tools
from app.service.tool import tool_service
import json
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import HumanMessage, SystemMessage


class LLM_instance:
    def __init__(self):
        self.llm = None
        self.agent = None
        self.tools = None
        self.tools_schema = None

    def getllm(self):
        llm = ChatOpenAI(
            model="deepseek-chat",
            api_key="sk-1cbbc25ad77a47c7aba4a487d964f48f",
            base_url="https://api.deepseek.com/v1",
            temperature=0,
            streaming=True,
        )
        return llm

    async def init_simple_chat(self, tools):
        self.llm = self.getllm()
        self.agent = create_agent(model=self.llm, tools=tools).with_config(
            {"callbacks": [ToolTraceHandler(self)]}
        )

    async def init_tools_schema(self, user_id):
        if not self.llm:
            self.llm = self.getllm()
        if not self.tools_schema:
            tools = tool_service.get_tool_list(user_id)
            tools_schema_list = []
            for tool in tools:
                openai_schema = tool.get("openai_schema")
                if openai_schema:
                    tools_schema_list.extend(openapi_to_tools(openai_schema))
            self.tools_schema = tools_schema_list
            return tools_schema_list
        return self.tools_schema

    async def init_tools(self, user_id):
        if not self.llm:
            self.llm = self.getllm()
        if not self.tools:
            tools = tool_service.get_tool_list(user_id)
            tool_list = []
            for tool in tools:
                openai_schema = tool.get("openai_schema")
                if openai_schema:
                    tool_list.extend(build_tools_from_openapi(openai_schema))
            self.tools = tool_list
            return tool_list
        return self.tools

    async def chat(self, tools):
        if not self.agent:
            await self.init_simple_chat(tools)

        return self.agent


class ToolTraceHandler(AsyncCallbackHandler):
    def __init__(self, llm_instance):
        super().__init__()
        self.llm_instance = llm_instance

    async def on_tool_start(
        self,
        serialized,
        input_str: str,
        **kwargs,
    ):
        print(f"[tool_start] {input_str}")

    async def on_chat_model_start(self, serialized, messages, **kwargs):
        # 显式实现该回调，避免框架在异步回调分发时抛 NotImplementedError
        return None

    async def on_tool_end(self, output, **kwargs):
        print(f"[tool_end]", output)
        # Tool 输出可能是 dict/tuple/list 等复杂结构，先转成纯字符串再作为消息内容
        if isinstance(output, str):
            output_text = output
        else:
            try:
                output_text = json.dumps(output, ensure_ascii=False, default=str)
            except Exception:
                output_text = str(output)

        messages = [
            SystemMessage(
                content="根据提供的内容,理解内容,输出理解后的内容。"
            ),  # 系统角色
            HumanMessage(content=output_text),  # 用户问题
        ]
        # llm = self.llm_instance.getLLM()
        # result = await llm.ainvoke(messages)
        return output

    def on_tool_error(self, error: BaseException, **kwargs: Any) -> Any:
        print(f"[tool_error] error={error}")


llm_instance = LLM_instance()
