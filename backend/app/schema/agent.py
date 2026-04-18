from typing import List, Any, Optional
from pydantic import BaseModel
from pydantic import Field


class AgentSchema(BaseModel):
    name: str
    description: str
    logo: str = ""
    is_custom: int = 0
    llm_id: str
    system_prompt: str = ""
    enable_memory: int = 0
    mcp_ids: list[str] = []
    tool_ids: list[str] = []
    agent_skill_ids: list[str] = []
    knowledge_ids: list[str] = []
    agent_id: Optional[str] = None


class Knowledge_Schema(BaseModel):
    name: str
    description: str
    id: Optional[str] = None


class DialogSchema(BaseModel):
    name: str
    agent_id: Optional[str] = None
    history: list[str] = []
    agent_type: str
    diolog_id: Optional[str] = None


class MCPResponseFormat(BaseModel):
    mcp_as_tool_name: str = Field(
        ...,
        description="根据该mcp服务下提供的工具描述生成一个工具名称，要求是2-4个英文单词组成，用下划线_隔开",
    )
    description: str = Field(
        ...,
        description="根据该mcp服务下提供的工具描述生成一个子Agent描述，当主Agent在什么场景下能够调用这个Agent的描述，描述需要加上：子智能体可以调用多个自身工具，所以将用户问题整合询问一次即可。字数在100字符以内",
    )
