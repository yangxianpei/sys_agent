from .baseService import BaseService
from app.models.work_session import Session


class Work_session(BaseService):
    def __init__(self):
        super().__init__()

    async def create_session(self, title, agent, contexts, user_id, session_id):
        with self.transession() as session:
            try:
                has_session = (
                    session.query(Session)
                    .filter(Session.session_id == session_id)
                    .first()
                )
                if not has_session:
                    ses = Session(
                        title=title,
                        agent=agent,
                        contexts=contexts,
                        user_id=user_id,
                    )
                    self.logger.info("添加会话成功")
                    session.add(ses)
                    session.flush()
                    return ses.to_dict()
                else:
                    dict_session = has_session.to_dict()
                    old_contexts = dict_session.get("contexts", [])
                    has_session.contexts = old_contexts + contexts
                    session.flush()
                    session.refresh(has_session)
            except Exception as e:
                raise e

    def get_session(self, session_id):
        with self.transession() as session:
            has_session = (
                session.query(Session).filter(Session.session_id == session_id).first()
            )
            if has_session:
                dict_has_session = has_session.to_dict()
                db_contexts = dict_has_session.get("contexts")
                if len(db_contexts) > 20:
                    latest_20 = db_contexts[-20:]
                    has_session.contexts = latest_20
                    session.flush()
                    session.refresh(has_session)
                return has_session.to_dict()
            else:
                return None

    def get_session_list(self, user_id):
        with self.session() as session:
            has_session_list = (
                session.query(Session).filter(Session.user_id == user_id).all()
            )
            if has_session_list:
                return [has_session.to_dict() for has_session in has_session_list]
            else:
                return []

    def del_llm(self, session_id):
        with self.transession() as session:
            has_session = (
                session.query(Session).filter(Session.session_id == session_id).first()
            )
            if has_session:
                session.delete(has_session)
                session.flush()
                return has_session.to_dict()
            return None

    # def modify_llm(self, llm_id, model, base_url, api_key):
    #     with self.transession() as session:
    #         try:
    #             llm = session.query(LLM).filter(LLM.llm_id == llm_id).first()
    #             if not llm:
    #                 return None
    #             llm.model = model
    #             llm.base_url = base_url
    #             llm.api_key = api_key
    #             session.flush()
    #             session.refresh(llm)
    #             return llm.to_dict()
    #         except Exception as e:
    #             raise e


work_session = Work_session()
