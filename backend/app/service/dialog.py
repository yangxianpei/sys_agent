from .baseService import BaseService
from app.models.dialog import Dialog
from app.models.agent import Agent

from app.schema.agent import DialogSchema


class Dialog_service(BaseService):
    def __init__(self):
        super().__init__()

    def create_dialog(self, user_id, dialog: DialogSchema):
        with self.transession() as session:
            try:
                agent_id = dialog.agent_id
                dio = Dialog(
                    name=dialog.name,
                    agent_id=agent_id,
                    user_id=user_id,
                    agent_type=dialog.agent_type,
                )
                session.add(dio)
                session.flush()
                return dio.to_dict()
            except Exception as e:
                raise e

    def dialog_list(self, user_id):
        with self.session() as session:
            try:
                dialog = session.query(Dialog).filter(Dialog.user_id == user_id).all()
                result = []
                for dio in dialog:
                    agent_id = dio.agent_id
                    agent = session.query(Agent).filter(Agent.id == agent_id).first()
                    result.append({**(dio.to_dict() or {}), **(agent.to_dict() or {})})
                return result
            except Exception as e:
                raise e

    def delete_one(self, dialog_id):
        with self.transession() as session:
            try:
                dialog = (
                    session.query(Dialog).filter(Dialog.dialog_id == dialog_id).first()
                )
                session.delete(dialog)
                session.flush()
                return dialog.to_dict()
            except Exception as e:
                raise e


dialog_service = Dialog_service()
