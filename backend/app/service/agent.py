from .baseService import BaseService
from app.models.agent import Agent
from app.schema.agent import AgentSchema
from app.service.mcp.mcpClient import mcp_servcie
from app.service.tool import tool_service
from app.service.llm import llm_service
from app.service.knowledge import knowledge_service
from app.service.agent_skill import agent_skill_service
from app.utils.general_agent import GeneralAgent
from app.models.dialog import Dialog
from typing import List
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
import json
from app.prompts.lingseek import system_prompt


class Agent_service(BaseService):
    def __init__(self):
        super().__init__()

    async def create_agent(self, user_id, agent: AgentSchema):
        with self.transession() as session:
            try:
                agent = Agent(
                    name=agent.name,
                    description=agent.description,
                    logo=agent.logo,
                    user_id=user_id,
                    llm_id=agent.llm_id,
                    tool_ids=agent.tool_ids,
                    mcp_ids=agent.mcp_ids,
                    agent_skill_ids=agent.agent_skill_ids,
                    knowledge_ids=agent.knowledge_ids,
                )
                session.add(agent)
                session.flush()
                return agent.to_dict()
            except Exception as e:
                raise e

    async def agent_list(self, user_id):
        with self.session() as session:
            try:
                agent_list = session.query(Agent).filter(Agent.user_id == user_id).all()
                if agent_list:
                    return [agent.to_dict() for agent in agent_list]
                return []
            except Exception as e:
                raise e

    async def get_agent_by_id(self, id):
        with self.session() as session:
            try:
                agent = session.query(Agent).filter(Agent.id == id).first()
                if agent:
                    return agent.to_dict()
                return ""
            except Exception as e:
                raise e

    async def modif_agent(self, agent: AgentSchema):
        with self.transession() as session:
            try:
                has_agent = (
                    session.query(Agent).filter(Agent.id == agent.agent_id).first()
                )
                if has_agent:
                    has_agent.name = agent.name
                    has_agent.description = agent.description
                    has_agent.system_prompt = agent.system_prompt
                    has_agent.logo = agent.logo
                    has_agent.llm_id = agent.llm_id
                    has_agent.tool_ids = agent.tool_ids
                    has_agent.mcp_ids = agent.mcp_ids
                    has_agent.agent_skill_ids = agent.agent_skill_ids
                    has_agent.knowledge_ids = agent.knowledge_ids
                    session.flush()
                    session.refresh(has_agent)
                    return has_agent.to_dict()
                else:
                    return None
            except Exception as e:
                raise e

    async def get_agent_all(self, user_id):
        mcps = await mcp_servcie.get_mcp_list(user_id)
        tool = tool_service.get_tool_list_all(user_id)
        llms = llm_service.get_llm_list(user_id)
        docs = knowledge_service.knowledge_list(user_id)
        skills = agent_skill_service.list_agent_skill(user_id)
        return {
            "tools": tool,
            "mcps": mcps,
            "llms": llms,
            "docs": docs,
            "skills": skills,
        }

    def del_agent(self, agent_id):
        with self.transession() as session:
            llm = session.query(Agent).filter(Agent.id == agent_id).first()
            if llm:
                session.delete(llm)
                session.flush()
                return llm.to_dict()
            return None

    def search_agent(self, name):
        with self.session() as session:
            try:
                agent_list = (
                    session.query(Agent).where(Agent.name.ilike(f"%{name}%")).all()
                )
                return [agent.to_dict() for agent in agent_list]
            except Exception as e:
                raise e

    async def completion(self, dialog_id, user_input, user_id):
        with self.transession() as session:
            dialog = session.query(Dialog).filter(Dialog.dialog_id == dialog_id).first()
            if dialog:
                agent = session.query(Agent).filter(Agent.id == dialog.agent_id).first()
                agent_dict = agent.to_dict()
                generalAgent = GeneralAgent(agent_dict, user_id)
                await generalAgent.init_agent()

                if dialog.history:
                    history_messages = [
                        f"query: {message.get('query')}, answer: {message.get('answer')}\n"
                        for message in dialog.history
                    ]
                else:
                    history_messages = []
                history_prompt = f"""
                以下是历史记录
                {"".join(history_messages)}
                """
                style_prompt = f"""
                用户偏好
                {agent.system_prompt}
                """
                messages: List[BaseMessage] = [
                    SystemMessage(content=system_prompt),
                    SystemMessage(content=style_prompt),
                    SystemMessage(content=history_prompt),
                    HumanMessage(content=user_input),
                ]
                response_content = ""
                async for event in generalAgent.astream(messages):
                    # 兼容 chunk 可能是 dict 或 tuple；含 type=error（流内错误）
                    if event.get("type") == "response_chunk":
                        yield f"data: {json.dumps(event)}\n\n"
                        response_content += event["data"].get("chunk", "")
                    else:
                        yield f"data: {json.dumps(event)}\n\n"
                task = {"query": user_input, "answer": response_content}
                history = dialog.history
                if len(history) > 20:
                    history = dialog.history[-19:]
                dialog.history = history + [task]
                session.flush()
                session.refresh(dialog)


agent_service = Agent_service()
