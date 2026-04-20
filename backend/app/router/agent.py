from fastapi import APIRouter, Body, Depends, Request, Query
from app.utils.schemas import RespoceModel, resp_200, resp_500
from app.service.llm import llm_service
from app.schema.agent import AgentSchema
from app.service.agent import agent_service
from starlette.responses import StreamingResponse
import json
from app.prompts.lingseek import Mars_System_Prompt, reasoning
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from typing import List
from app.service.marsAgent import MarsAgent

api_router = APIRouter(prefix="/v1", tags=["Agent"])


@api_router.post("/create_agent", response_model=RespoceModel)
async def create_agent(*, request: Request, agent: AgentSchema):
    user = request.state.user
    try:
        item = await agent_service.create_agent(user_id=user.get("id"), agent=agent)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.get("/get_agent_all", response_model=RespoceModel)
async def get_agent_all(*, request: Request):
    user = request.state.user
    try:
        item = await agent_service.get_agent_all(user_id=user.get("id"))
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.get("/agent_all_list", response_model=RespoceModel)
async def agent_all_list(*, request: Request):
    user = request.state.user
    try:
        item = await agent_service.agent_list(user_id=user.get("id"))
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.post("/modfy_agent", response_model=RespoceModel)
async def modfy_agent(*, agent: AgentSchema):
    try:
        item = await agent_service.modif_agent(agent=agent)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.delete("/del_agent", response_model=RespoceModel)
async def del_agent(
    agent_id: str = Body(..., embed=True, description="agent_id"),
):
    try:
        item = agent_service.del_agent(agent_id)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.get("/get_agent_by_id", response_model=RespoceModel)
async def get_agent_by_id(*, id: str = Query(None, embed=True, description="id")):
    try:
        item = await agent_service.get_agent_by_id(id)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.post("/search_agent", response_model=RespoceModel)
async def search_agent(*, name: str = Body(..., embed=True, description="name")):
    try:
        item = agent_service.search_agent(name)
        return resp_200(item)
    except Exception as e:
        return resp_500(None)


@api_router.post("/completion", response_model=RespoceModel)
async def completion(
    *,
    request: Request,
    dialog_id: str = Body(..., embed=True, description="name"),
    user_input: str = Body(..., embed=True, description="user_input"),
):
    user = request.state.user
    user_id = user.get("id", "")

    async def general_generate():
        async for chunk in agent_service.completion(dialog_id, user_input, user_id):
            yield chunk

    return StreamingResponse(
        general_generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


class MarsExampleEnum:
    Autobuild_Agent = 1
    Deep_Search = 2
    AI_News = 3
    Query_Knowledge = 4


@api_router.post("/mars/example")
async def chat_mars_example(
    *,
    request: Request,
    example_id: int = Body(..., description="例子ID", embed=True),
):
    user = request.state.user
    id = user.get("id")
    mars_agent = MarsAgent(user_id=id)
    mars_agent.init_normal_agent()
    await mars_agent.init_all_tool()

    user_input = ""
    if example_id == MarsExampleEnum.Autobuild_Agent:
        user_input = "帮我生成一个智能体，它可以给我预报每天的天气情况并且可以帮我生成图片，名称跟描述的话请你给他起一个吧，智能体名称字数要处于2-10字之间"
    elif example_id == MarsExampleEnum.AI_News:
        user_input = "请帮我生成一份今天的AI日报，然后总结之后提供给我一个AI日报的图片，不需要详细内容"
    elif example_id == MarsExampleEnum.Query_Knowledge:
        user_input = (
            "请你帮我查询我所有的知识库，然后告诉我知识库中都是什么信息.列出所有."
        )
    elif example_id == MarsExampleEnum.Deep_Search:
        user_input = "使用深度搜索查泰山游玩攻略"

    messages: List[BaseMessage] = [
        SystemMessage(content=Mars_System_Prompt.format(memory_content="")),
        HumanMessage(content=user_input),
    ]
    messages2: List[BaseMessage] = [
        SystemMessage(content=reasoning.format(input=user_input)),
        HumanMessage(content=user_input),
    ]

    async def general_generate():
        async for chunk in mars_agent.ainvoke_stream(messages, messages2):
            # dict 必须用 JSON，否则 f"{dict}" 为 Python repr（单引号），前端解析会得到空
            if isinstance(chunk, dict):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            else:
                yield f"data: {json.dumps({'message': str(chunk)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(general_generate(), media_type="text/event-stream")


@api_router.post("/mars/chat")
async def chat_mars_example(
    *,
    request: Request,
    user_input: str = Body(..., description="用户输入", embed=True),
):
    user = request.state.user
    id = user.get("id")
    mars_agent = MarsAgent(user_id=id)
    mars_agent.init_normal_agent()
    await mars_agent.init_all_tool()

    messages: List[BaseMessage] = [
        SystemMessage(content=Mars_System_Prompt.format(memory_content="")),
        HumanMessage(content=user_input),
    ]
    messages2: List[BaseMessage] = [
        SystemMessage(content=reasoning.format(input=user_input)),
        HumanMessage(content=user_input),
    ]

    async def general_generate():
        async for chunk in mars_agent.ainvoke_stream(messages, messages2):
            # dict 必须用 JSON，否则 f"{dict}" 为 Python repr（单引号），前端解析会得到空
            if isinstance(chunk, dict):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            else:
                yield f"data: {json.dumps({'message': str(chunk)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(general_generate(), media_type="text/event-stream")
