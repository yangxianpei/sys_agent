from app.models.user import User
from app.utils.database import get_logger
from .baseService import BaseService
from app.models.knowledge import Knowledge, Knowledge_Doc
from app.schema.agent import Knowledge_Schema
from fastapi import UploadFile, File
import uuid
from app.config import Config
from app.service.vectordb.milvus import milvus
import os
from fastapi import HTTPException
import asyncio


class Knowledge_service(BaseService):
    def __init__(self):
        super().__init__()

    def create_knowledge(self, user_id, knowledge: Knowledge_Schema):
        with self.transession() as session:
            try:
                new_knowledge = Knowledge(
                    name=knowledge.name,
                    description=knowledge.description,
                    user_id=user_id,
                )
                session.add(new_knowledge)
                session.flush()
                return new_knowledge.to_dict()
            except Exception as e:
                raise e

    def modify_knowledge(self, knowledge: Knowledge_Schema):
        with self.transession() as session:
            try:
                has_knowledge = (
                    session.query(Knowledge)
                    .filter(Knowledge.id == knowledge.id)
                    .first()
                )
                has_knowledge.name = knowledge.name
                has_knowledge.description = knowledge.description
                session.flush()
                session.refresh(has_knowledge)
                return has_knowledge.to_dict()
            except Exception as e:
                raise e

    def knowledge_list(self, user_id):
        with self.session() as session:
            try:
                knowledge_list = (
                    session.query(Knowledge).filter(Knowledge.user_id == user_id).all()
                )

                result = []

                for knowledge in knowledge_list:
                    docs = (
                        session.query(Knowledge_Doc)
                        .filter(Knowledge_Doc.knowledge_id == knowledge.id)
                        .all()
                    )
                    knowledge_size = 0
                    for doc in docs:
                        # doc.file_path 存的是 "/uploads/..."，左侧带 / 时 pathlib 会当成绝对路径，
                        # 在 Windows 上会丢掉 BASE_DIR，拼成 D:\uploads\... 导致文件“不存在”
                        rel = str(doc.file_path).lstrip("/\\")
                        file_path = Config.BASE_DIR / rel
                        if os.path.exists(str(file_path)):
                            # 上传文件多为 PDF/Office 等二进制，用文本 UTF-8 读会解码失败；用字节大小即可
                            knowledge_size += os.path.getsize(str(file_path))
                    result.append(
                        {
                            "knowledge_size": f"{round(knowledge_size / (1024 * 1024), 2)} MB",
                            "doc_count": len(docs),
                            **knowledge.to_dict(),
                        }
                    )
                return result
            except Exception as e:
                raise e

    async def knowledge_upload_doc(self, file: File, knowledge_id):
        with self.transession() as session:
            try:
                file_dir = Config.BASE_DIR / "uploads" / f"{knowledge_id}"
                file_dir.mkdir(parents=True, exist_ok=True)
                filename = f"{knowledge_id}_{uuid.uuid4().hex[:9]}_{file.filename}"
                content = await file.read()
                file_path = file_dir / filename
                size = 0
                with open(file_path, "wb") as f:
                    f.write(content)
                    self.logger.info(
                        f"文档添加成功/uploads/{knowledge_id}/{str(filename)}"
                    )
                # return {"url": f"/uploads/docs/{str(filename)}"}
                size = len(content)
                knowledge_doc = Knowledge_Doc(
                    file_path=f"/uploads/{knowledge_id}/{str(filename)}",
                    knowledge_id=knowledge_id,
                    name=filename,
                    file_size=f"{round(size / (1024 * 1024), 2)} MB",
                )
                self.logger.info("文档已经添加到数据库")
                session.add(knowledge_doc)
                session.flush()

                milvus.async_process(knowledge_id, filename, knowledge_doc.id)
                return knowledge_doc.to_dict()
            except Exception as e:
                raise e

    def remove_file(self, filename):
        safe_filename = str(filename).lstrip("/\\")
        file_path = Config.BASE_DIR / safe_filename
        if os.path.exists(str(file_path)):
            print(str(file_path))
            os.remove(str(file_path))
            self.logger.info("删除成功")
        else:
            self.logger.info("文件不存在")

    def knowledge_doc_list(self, knowledge_id):
        with self.session() as session:
            try:
                knowledge_doc_list = (
                    session.query(Knowledge_Doc)
                    .filter(Knowledge_Doc.knowledge_id == knowledge_id)
                    .all()
                )

                return [doc.to_dict() for doc in knowledge_doc_list]
            except Exception as e:
                raise e

    def knowledge_doc_del(self, doc_id):
        with self.transession() as session:
            try:
                doc = (
                    session.query(Knowledge_Doc)
                    .filter(Knowledge_Doc.id == doc_id)
                    .first()
                )
                if not doc:
                    raise HTTPException(status_code=404, detail="文档不存在或已删除")

                # 先删向量，避免数据库已删但向量残留
                milvus.milvus_del(doc_id)
                self.remove_file(doc.file_path)
                session.delete(doc)
                session.flush()
                return doc.to_dict()
            except Exception as e:
                raise e

    async def del_link_resource(self, knowledge_id, docs):
        for doc in docs:
            self.logger.info(f"删除{knowledge_id}的图片资源")
            self.remove_file(doc.get("file_path", ""))
            self.logger.info(f"删除{knowledge_id}的图片资源完毕")
            self.logger.info(f"删除{knowledge_id}的milvus")
            milvus.milvus_del(doc.get("id", ""))
            self.logger.info(f"删除{knowledge_id}的milvus完毕")

    def knowledge_del(self, knowledge_id):
        with self.transession() as session:
            try:
                knowledge = (
                    session.query(Knowledge)
                    .filter(Knowledge.id == knowledge_id)
                    .first()
                )
                docs = (
                    session.query(Knowledge_Doc)
                    .filter(Knowledge_Doc.knowledge_id == knowledge_id)
                    .all()
                )
                # if not knowledge:
                # raise HTTPException(status_code=404, detail="知识库不存在或已删除")
                self.logger.info(f"开启异步去删除{knowledge_id}的资源")
                asyncio.create_task(
                    self.del_link_resource(
                        knowledge_id, [doc.to_dict() for doc in docs]
                    )
                )

                session.delete(knowledge)
                session.flush()
                return knowledge.to_dict()
            except Exception as e:
                raise e


knowledge_service = Knowledge_service()
