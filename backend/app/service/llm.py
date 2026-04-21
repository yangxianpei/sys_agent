from .baseService import BaseService
from app.models.llm import LLM
from langchain_core.messages import BaseMessage, ToolMessage
from starlette.responses import StreamingResponse
import json
import re
from app.service.work_session import work_session
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from app.utils.llm import llm_instance
from app.prompts.lingseek import (
    GenerateGuidePrompt,
    GenerateTaskPrompt,
    FixJsonPrompt,
    SystemMessagePrompt,
    ToolCallPrompt,
    GuidePromptTemplate,
)
from app.schema.lingseek import LingSeekTask, LingSeekTaskStep
from app.utils.helper import get_beijing_time
from typing import Any, Dict, List, Union, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LLMService(BaseService):
    def __init__(self):
        super().__init__()
        self.lingseek_llm = None

    async def register(self, model, base_url, user, api_key):
        with self.transession() as session:
            try:
                user_id = user.get("id", "")
                llm = LLM(
                    model=model,
                    base_url=base_url,
                    user_id=user_id,
                    api_key=api_key,
                )
                self.logger.info("添加模型成功")
                session.add(llm)
                session.flush()
                return llm.to_dict()
            except Exception as e:
                raise e

    def get_llm_list(self, user_id):
        with self.session() as session:
            llms = (
                session.query(LLM)
                .filter(LLM.user_id == user_id | LLM.user_id.is_(None))
                .all()
            )
            result = []
            if llms:
                result.extend(llm.to_dict() for llm in llms)
            return result

    def del_llm(self, llm_id):
        with self.transession() as session:
            llm = session.query(LLM).filter(LLM.llm_id == llm_id).first()
            if llm:
                session.delete(llm)
                session.flush()
                return llm.to_dict()
            return None

    def get_llm_by_id(self, llm_id):
        with self.transession() as session:
            llm = session.query(LLM).filter(LLM.llm_id == llm_id).first()
            if llm:
                return llm.to_dict()
            return None

    def get_default_llm(self):
        with self.transession() as session:
            llm = session.query(LLM).first()
            if llm:
                return llm.to_dict()
            return None

    def modify_llm(self, llm_id, model, base_url, api_key):
        with self.transession() as session:
            try:
                llm = session.query(LLM).filter(LLM.llm_id == llm_id).first()
                if not llm:
                    return None
                llm.model = model
                llm.base_url = base_url
                llm.api_key = api_key
                session.flush()
                session.refresh(llm)
                return llm.to_dict()
            except Exception as e:
                raise e

    @staticmethod
    async def _generate_title(agent, query):
        messages = [
            SystemMessage(
                content="根据提供的内容生成不超过10字的标题，仅输出标题，不要解释、不要多余内容。"
            ),  # 系统角色
            HumanMessage(content=query),  # 用户问题
        ]
        result = await llm_instance.llm.ainvoke(messages)
        content = getattr(result, "content", "")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict) and block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
            return "".join(parts).strip()
        return str(content).strip()

    async def simple_chat(
        self, query, model_id, session_id, mcp_servers, tool_ids, user_id
    ):
        llm_config = self.get_llm_by_id(model_id)

        history = work_session.get_session(session_id)
        if history:
            history_messages = [
                f"query: {message.get('query')}, answer: {message.get('answer')}\n"
                for message in history.get("contexts")
            ]
        else:
            history_messages = ["无历史对话"]
        system_prompt = f"""你是一个专业的AI助手，回答要简洁、准确、有礼貌。
        这是之前的对话历史，请参考上下文回答：
        你必须遵守规则：
        调用工具返回结果仅供内部参考，禁止原样输出JSON。
        请将结果整理为自然语言，给用户清晰回答。
        {"".join(history_messages)}
        """
        all_tools = []
        await llm_instance.init_llm(llm_config)
        tools = await llm_instance.init_tools(user_id, tool_ids)
        mcp_tools = await llm_instance.init_mcp(mcp_servers)
        all_tools.extend(tools)
        all_tools.extend(mcp_tools)
        messages = [
            SystemMessage(content=system_prompt),  # 系统角色
            HumanMessage(content=query),  # 用户问题
        ]

        agent = await llm_instance.chat(all_tools)

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
                if (
                    len(msg) == 2
                    and hasattr(msg[0], "content")
                    and isinstance(msg[1], dict)
                ):
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

        def _extract_msg_meta(chunk):
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

        def _is_tool_or_intermediate(msg, meta) -> bool:
            msg_cls = str(msg.__class__.__name__).lower()
            node = str(meta.get("langgraph_node", "")).lower()
            tool_calls = getattr(msg, "tool_calls", None) or []
            tool_call_chunks = getattr(msg, "tool_call_chunks", None) or []
            if node == "tools":
                return True
            if "toolmessage" in msg_cls:
                return True
            if tool_calls or tool_call_chunks:
                return True
            return False

        async def general_generate():
            try:
                yield "data: start\n\n"
                finally_answer = ""
                async for chunk in agent.astream(
                    input={"messages": messages}, stream_mode="messages"
                ):
                    msg, meta = _extract_msg_meta(chunk)
                    if _is_tool_or_intermediate(msg, meta):
                        continue
                    text = _chunk_text(msg)
                    if not text:
                        continue
                    finally_answer += text
                    obj = {"event": "task_result", "data": {"message": text}}
                    yield f"data: {json.dumps(obj)}\n\n"
                done_obj = {"event": "task_result", "data": {"message": ""}}
                yield f"data: {json.dumps(done_obj)}\n\n"
                title = await self._generate_title(agent, query)
                task = [{"query": query, "answer": finally_answer}]
                await work_session.create_session(
                    title=title,
                    agent="simple",
                    contexts=task,
                    user_id=user_id,
                    session_id=session_id,
                )
            except Exception as e:
                import traceback

                print("Error:", e)
                print(traceback.format_exc())
                yield f"data: {json.dumps({'event': 'error', 'data': {'message': str(e)}}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            general_generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    async def lingseek_agent(self, query, mcp_servers, tool_ids, user_id):
        llm_config = self.get_default_llm()
        all_tools = []
        self.lingseek_llm = await llm_instance.init_llm(llm_config)
        tools = await llm_instance.init_tools(user_id, tool_ids)
        mcp_tools = await llm_instance.init_mcp(mcp_servers)
        all_tools.extend(tools)
        all_tools.extend(mcp_tools)
        tools_schema = self._tools_to_schema(all_tools)
        tools_str = json.dumps(tools_schema, ensure_ascii=False, indent=2)
        lingseek_guide_prompt = GenerateGuidePrompt.format(
            tools_str=tools_str,
            query=query,
            guide_prompt_template=GuidePromptTemplate,
        )
        final_response = ""
        async for chunk in self._generate_guide_prompt(lingseek_guide_prompt):
            final_response += chunk.content
            yield {"event": "task_result", "data": {"message": chunk.content}}

    @staticmethod
    def _tools_to_schema(all_tools: List[Any]) -> List[Dict[str, Any]]:
        """
        将 LangChain tool 列表转换为 OpenAI function calling 风格 schema。
        """
        tools_schema: List[Dict[str, Any]] = []

        for tool in all_tools or []:
            name = getattr(tool, "name", None)
            if not name:
                continue

            description = getattr(tool, "description", "") or ""
            parameters: Dict[str, Any] = {
                "type": "object",
                "properties": {},
                "required": [],
            }

            args_schema = getattr(tool, "args_schema", None)
            if args_schema is not None:
                try:
                    # pydantic v2
                    if hasattr(args_schema, "model_json_schema"):
                        parameters = args_schema.model_json_schema()
                    # pydantic v1
                    elif hasattr(args_schema, "schema"):
                        parameters = args_schema.schema()
                except Exception:
                    # schema 提取失败时回退空参数定义，避免中断主流程
                    parameters = {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    }

            tools_schema.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": description,
                        "parameters": parameters,
                    },
                }
            )

        return tools_schema

    async def _generate_guide_prompt(self, lingseek_guide_prompt):
        """
        通过COT的方法使得模型回复的更加准确，但是展示的时候需要把思考内容隐藏
        """
        one = None
        sop_flag = False
        sop_content = ""
        answer = ""
        split_tags = ["<Thought_END>", "</Thought_END>"]
        async for one in self.lingseek_llm.astream(input=lingseek_guide_prompt):
            answer += f"{one.content}"
            if sop_flag:
                yield one
                sop_content += one.content
                continue
            for split_tag in split_tags:
                if answer.find(split_tag) != -1:
                    sop_flag = True
                    sop_content = answer.split(split_tag)[-1].strip()
                    if sop_content:
                        one.content = sop_content
                        yield one
                    break
        if not sop_content:
            one.content = answer
            yield one

    async def lingseek_start(self, lingseek_task: LingSeekTask, user_id):
        task = await self.generate_tasks(lingseek_task, user_id)
        tasks_graph = {}
        tasks_show = []
        steps = task.get("steps", [])
        llm_config = self.get_default_llm()
        llm = await llm_instance.init_llm(llm_config)
        for step in steps:
            task_step = LingSeekTaskStep(**step)
            tasks_graph[task_step.step_id] = task_step

        for step_id, step_info in tasks_graph.items():
            for input_step in step_info.input:
                if input_step in tasks_graph:
                    # 构建展示的任务列表图结构
                    tasks_show.append(
                        {
                            "start": tasks_graph[input_step].title,
                            "end": tasks_graph[step_id].title,
                        }
                    )
                else:
                    tasks_show.append(
                        {"start": "用户问题", "end": tasks_graph[step_id].title}
                    )
        yield {"event": "generate_tasks", "data": {"graph": tasks_show}}
        tool_ids = lingseek_task.plugins or []
        tools = await llm_instance.init_tools(user_id, tool_ids)
        tools_schema = await llm_instance.init_tools_schema(user_id)
        llm_config = self.get_default_llm()
        tool_llm = await llm_instance.init_llm(llm_config)
        binded_tool_llm = tool_llm.bind_tools(tools_schema)
        messages: List[BaseMessage] = [
            SystemMessage(content=SystemMessagePrompt),
            HumanMessage(content=lingseek_task.query),
        ]

        context_task = []
        for step_id, step_info in tasks_graph.items():
            step_context = []
            for input_step in step_info.input:
                if input_step in tasks_graph:
                    step_context.append(tasks_graph[input_step].model_dump())

            step_prompt = ToolCallPrompt.format(
                step_info=step_info, step_context=str(step_context)
            )
            step_messages = [
                SystemMessage(content=step_prompt),
                HumanMessage(content=lingseek_task.query),
            ]
            response = await binded_tool_llm.ainvoke(input=step_messages)
            tools_messages = []
            tools_messages = await self._parse_function_call_response(response, tools)

            step_info.result = "\n".join([msg.content for msg in tools_messages])

            context_task.append(step_info.model_dump())
            if tools_messages:  # 合到整体Messages
                messages.append(response)
                messages.extend(tools_messages)
            else:
                messages.append(HumanMessage(content=lingseek_task.query))
                messages.append(AIMessage(content=response.content))
            yield {
                "event": "step_result",
                "data": {"message": step_info.result or " ", "title": step_info.title},
            }
        final_response = ""
        logger.info("生产最终答案")
        # 最终总结阶段不再绑定 tools，避免继续产出 tool_call 导致 content 为空。
        async for chunk in llm.astream(messages):
            chunk_content = self._message_content_to_text(chunk.content)
            if chunk_content:
                final_response += chunk_content
                yield {"event": "task_result", "data": {"message": chunk_content}}

        # 兜底：若流式阶段没有文本，退回非流式调用，保证最终答案可返回。
        if not final_response.strip():
            fallback = await llm.ainvoke(input=messages)
            fallback_content = self._message_content_to_text(fallback.content)
            if fallback_content.strip():
                yield {"event": "task_result", "data": {"message": fallback_content}}

    async def _parse_function_call_response(self, message: AIMessage, tools):
        tool_messages = []
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args")
                tool_call_id = tool_call.get("id")

                content = await self._process_tools_result(tool_name, tool_args, tools)
                tool_messages.append(
                    ToolMessage(
                        content=content, name=tool_name, tool_call_id=tool_call_id
                    )
                )

        return tool_messages

    async def _process_tools_result(self, tool_name, tool_args, tools):
        for tool in tools:
            if tool.name == tool_name:
                ret = await tool.ainvoke(tool_args)
                return ret
        return ""

    async def generate_tasks(self, lingseek_task: LingSeekTask, user_id):
        tools_schema = await llm_instance.init_tools_schema(user_id)
        tools_str = json.dumps(tools_schema, ensure_ascii=False, indent=2)

        lingseek_task_prompt = GenerateTaskPrompt.format(
            tools_str=tools_str,
            query=lingseek_task.query,
            guide_prompt=lingseek_task.guide_prompt,
            current_time=get_beijing_time(),
        )

        response_task = await self._generate_tasks(lingseek_task_prompt)

        return response_task

    async def _generate_tasks(self, lingseek_task_prompt):
        llm_config = self.get_default_llm()
        conversation_json_model = await llm_instance.init_llm(llm_config)
        response = await conversation_json_model.ainvoke(input=lingseek_task_prompt)
        raw_content = self._message_content_to_text(response.content)

        try:
            content = self._loads_possible_json(raw_content)
            return content
        except Exception as err:
            logger.warning("任务拆解初次 JSON 解析失败: %s", str(err))
            fix_message = FixJsonPrompt.format(
                json_content=raw_content, json_error=str(err)
            )
            fix_response = await conversation_json_model.ainvoke(input=fix_message)
            fixed_raw_content = self._message_content_to_text(fix_response.content)
            try:
                fix_content = self._loads_possible_json(fixed_raw_content)
                return fix_content
            except Exception as fix_err:
                logger.exception(
                    "任务拆解 JSON 修复仍失败, raw=%s, fixed_raw=%s",
                    raw_content,
                    fixed_raw_content,
                )
                raise ValueError(
                    f"任务拆解 JSON 解析失败: {fix_err}. "
                    f"原始返回: {raw_content[:300]}. "
                    f"修复返回: {fixed_raw_content[:300]}"
                ) from fix_err

    @staticmethod
    def _message_content_to_text(content: Any) -> str:
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict):
                    if block.get("type") == "text":
                        parts.append(str(block.get("text", "")))
                    else:
                        parts.append(str(block))
                else:
                    parts.append(str(block))
            return "".join(parts).strip()
        return str(content).strip()

    @staticmethod
    def _loads_possible_json(text: str):
        if not text:
            raise ValueError("模型未返回内容")
        try:
            return json.loads(text)
        except Exception:
            pass

        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if fence_match:
            return json.loads(fence_match.group(1).strip())

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1].strip())
        raise ValueError("无法在模型输出中提取有效 JSON")


llm_service = LLMService()
