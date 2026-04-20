import copy

from sqlalchemy.orm.attributes import flag_modified

from .baseService import BaseService
from app.models.agent_skill import AgentSkill
from app.schema.agent import Agent_Skill_Schema, AgentSkillFolder, AgentSkillFile


class Agent_skill_service(BaseService):
    def __init__(self):
        super().__init__()

    @staticmethod
    def create_folder(name, description):
        default_skill_readme = f"""
            ---
                name: {name}
                description: {description}
            ---
            """
        default_folde = AgentSkillFolder(name=name, path=f"/{name}")
        default_folde.folder.append(
            AgentSkillFile(
                name="SKILL.md",
                path=f"/{name}/SKILL.md",
                type="file",
                content=default_skill_readme,
            )
        )
        default_folde.folder.append(
            AgentSkillFolder(name="reference", path=f"/{name}/reference")
        )
        default_folde.folder.append(
            AgentSkillFolder(name="scripts", path=f"/{name}/scripts")
        )
        return default_folde.model_dump()

    def create_agent_skill(self, user_id, agent_skill: Agent_Skill_Schema):
        with self.transession() as session:
            try:
                as_tool_name = agent_skill.name + "_skill"
                name = agent_skill.name
                description = agent_skill.description
                agent_skill = AgentSkill(
                    name=name,
                    description=description,
                    as_tool_name=as_tool_name,
                    user_id=user_id,
                    folder=Agent_skill_service.create_folder(name, description),
                )
                session.add(agent_skill)
                session.flush()
                return agent_skill.to_dict()
            except Exception as e:
                raise e

    def list_agent_skill(self, user_id):
        with self.transession() as session:
            try:
                agent_skills = (
                    session.query(AgentSkill)
                    .filter(AgentSkill.user_id == user_id)
                    .all()
                )
                return [agent_skill.to_dict() for agent_skill in agent_skills]
            except Exception as e:
                raise e

    def del_agent_skill(self, id):
        with self.transession() as session:
            try:
                agent_skill = (
                    session.query(AgentSkill).filter(AgentSkill.id == id).first()
                )
                session.delete(agent_skill)
                session.flush()
                return agent_skill.to_dict()
            except Exception as e:
                raise e

    def add_agent_skill_file(self, agent_skill_id, path, name):
        with self.transession() as session:
            try:
                agent_skill = (
                    session.query(AgentSkill)
                    .filter(AgentSkill.id == agent_skill_id)
                    .first()
                )
                agent_skill_copy = agent_skill.folder.copy()
                for item in agent_skill_copy.get("folder", []):
                    # path 匹配根目录下的某个目录（如 /Search-Skill/reference）
                    if item["path"] == path:
                        if "folder" not in item:
                            item["folder"] = []  # 确保有 folder 列表
                        item["folder"].append(
                            {
                                "name": name,
                                "type": "file",
                                "path": f"{path.rstrip('/')}/{name}",
                                "content": "",
                            }
                        )
                        break
                agent_skill.folder = agent_skill_copy
                flag_modified(agent_skill, "folder")
                session.flush()
                session.refresh(agent_skill)
                return agent_skill.to_dict()
            except Exception as e:
                raise e

    def update_agent_skill_file(self, path, agent_skill_id, content):
        with self.transession() as session:
            try:
                agent_skill = (
                    session.query(AgentSkill)
                    .filter(AgentSkill.id == agent_skill_id)
                    .first()
                )
                agent_skill_copy = agent_skill.folder.copy()
                for item in agent_skill_copy.get("folder", []):
                    if item["path"] == path:
                        item["content"] = content
                        break

                    # 如果是 reference 或 scripts 目录，检查其子项
                    if (
                        item.get("name") in ("reference", "scripts")
                        and "folder" in item
                    ):
                        for subitem in item["folder"]:
                            if subitem["path"] == path:
                                subitem["content"] = content

                agent_skill.folder = agent_skill_copy
                flag_modified(agent_skill, "folder")
                session.flush()
                session.refresh(agent_skill)
                return agent_skill.to_dict()
            except Exception as e:
                raise e


agent_skill_service = Agent_skill_service()
