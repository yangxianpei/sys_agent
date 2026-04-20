from datetime import datetime, timedelta

from app.models.user import User
from app.utils.database import db_session, db_transession, get_logger
from .baseService import BaseService
from app.utils.jwt import create_token
from app.models.llm import LLM
from app.models.agent import Agent
from app.schema.agent import UsageStatsRequest
from app.models.usage_stats import Usage_stats as Usage


class Usage_stats(BaseService):
    def __init__(self):
        super().__init__()

    def get_model(self, user_id):
        with self.session() as session:
            llms = (
                session.query(LLM)
                .filter(LLM.user_id == user_id or LLM.user_id.is_(None))
                .all()
            )
            return [llm.to_dict() for llm in llms]

    def get_agent(self, user_id):
        with self.session() as session:
            agents = session.query(Agent).filter(Agent.user_id == user_id).all()
            return [agent.to_dict() for agent in agents]

    def get_count(self, user_id, usageStatsRequest: UsageStatsRequest):

        with self.session() as session:
            query = session.query(Usage).filter(Usage.user_id == user_id)

            if usageStatsRequest.model:
                model_value = usageStatsRequest.model.strip()
                if model_value:
                    query = query.filter(Usage.model == model_value)

            if usageStatsRequest.agent:
                agent_value = usageStatsRequest.agent.strip()
                if agent_value:
                    target_agent = (
                        session.query(Agent)
                        .filter(Agent.user_id == user_id, Agent.name == agent_value)
                        .first()
                    )
                    if target_agent:
                        query = query.filter(Usage.agent_id == target_agent.id)
                    else:
                        query = query.filter(Usage.agent_id == agent_value)

            if usageStatsRequest.delta_days and usageStatsRequest.delta_days > 0:
                start_time = datetime.utcnow() - timedelta(
                    days=usageStatsRequest.delta_days
                )
                query = query.filter(Usage.created_at >= start_time)

            usage_rows = query.all()
            agent_map = {
                agent.id: agent.name
                for agent in session.query(Agent).filter(Agent.user_id == user_id).all()
            }

            result = {}
            for row in usage_rows:
                date_key = row.created_at.strftime("%Y-%m-%d")
                if date_key not in result:
                    result[date_key] = {"agent": {}, "model": {}}

                model_key = row.model or "unknown"
                result[date_key]["model"][model_key] = (
                    result[date_key]["model"].get(model_key, 0) + 1
                )

                if not row.agent_id:
                    agent_name = "Simple-Agent"
                else:
                    agent_name = agent_map.get(row.agent_id, "已删除Agent")
                result[date_key]["agent"][agent_name] = (
                    result[date_key]["agent"].get(agent_name, 0) + 1
                )

            return result

    def get_count_use(self, user_id, usageStatsRequest: UsageStatsRequest):
        with self.session() as session:
            query = session.query(Usage).filter(Usage.user_id == user_id)

            if usageStatsRequest.model:
                model_value = usageStatsRequest.model.strip()
                if model_value:
                    query = query.filter(Usage.model == model_value)

            if usageStatsRequest.agent:
                agent_value = usageStatsRequest.agent.strip()
                if agent_value:
                    target_agent = (
                        session.query(Agent)
                        .filter(Agent.user_id == user_id, Agent.name == agent_value)
                        .first()
                    )
                    if target_agent:
                        query = query.filter(Usage.agent_id == target_agent.id)
                    else:
                        query = query.filter(Usage.agent_id == agent_value)

            if usageStatsRequest.delta_days and usageStatsRequest.delta_days > 0:
                start_time = datetime.utcnow() - timedelta(
                    days=usageStatsRequest.delta_days
                )
                query = query.filter(Usage.created_at >= start_time)

            usage_rows = query.all()
            agent_map = {
                agent.id: agent.name
                for agent in session.query(Agent).filter(Agent.user_id == user_id).all()
            }

            result = {}
            for row in usage_rows:
                date_key = row.created_at.strftime("%Y-%m-%d")
                if date_key not in result:
                    result[date_key] = {"agent": {}, "model": {}}

                model_key = row.model or "unknown"
                if model_key not in result[date_key]["model"]:
                    result[date_key]["model"][model_key] = {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0,
                    }

                if not row.agent_id:
                    agent_name = "Simple-Agent"
                else:
                    agent_name = agent_map.get(row.agent_id, "已删除Agent")
                if agent_name not in result[date_key]["agent"]:
                    result[date_key]["agent"][agent_name] = {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0,
                    }

                input_tokens = int(row.input_tokens or 0)
                output_tokens = int(row.output_tokens or 0)
                total_tokens = input_tokens + output_tokens

                result[date_key]["model"][model_key]["input_tokens"] += input_tokens
                result[date_key]["model"][model_key]["output_tokens"] += output_tokens
                result[date_key]["model"][model_key]["total_tokens"] += total_tokens

                result[date_key]["agent"][agent_name]["input_tokens"] += input_tokens
                result[date_key]["agent"][agent_name]["output_tokens"] += output_tokens
                result[date_key]["agent"][agent_name]["total_tokens"] += total_tokens

            return result


usage_stats = Usage_stats()
