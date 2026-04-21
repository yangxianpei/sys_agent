from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer
from app.config import Config
from app.utils.logger import get_logger
from .text_splitter import TextSplitter
from .document_loader import DocumentLoader
import os
from langchain_core.documents import Document
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import Future
from pymilvus import (
    FieldSchema,
    CollectionSchema,
    DataType,
)
from app.models.knowledge import Knowledge, Knowledge_Doc
from ..baseService import BaseService
from functools import partial
from .reranker import Reranker

logger = get_logger(__name__)


class Milvus(BaseService):
    def __init__(self):
        self.client = None
        self.MILVUS_COLLECTION_NAME = Config.MILVUS_COLLECTION_NAME
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.model = None
        self.inited = False

    def init_embed(self):
        self.model = SentenceTransformer(Config.all_MiniLM_L6)

    def embed_process(self, text):
        return self.model.encode(text).tolist()

    def milvus_del(self, doc_id):
        self.init_milvus()
        if not self.client.has_collection(self.MILVUS_COLLECTION_NAME):
            logger.info(f"集合不存在，无需删除: {self.MILVUS_COLLECTION_NAME}")
            return

        try:
            # idx 在 schema 中是 VARCHAR，表达式需要字符串字面量
            expr = f'idx == "{doc_id}"'
            res = self.client.query(
                collection_name=self.MILVUS_COLLECTION_NAME, filter=expr
            )

            if len(res) > 0:
                self.client.delete(
                    collection_name=self.MILVUS_COLLECTION_NAME, filter=expr
                )
                self.client.flush(self.MILVUS_COLLECTION_NAME)
                self.client.load_collection(self.MILVUS_COLLECTION_NAME)
        except Exception as e:
            raise e

    def embed(self, documents):
        embeded = []
        for idx, doc in enumerate(documents):
            text = doc.page_content
            doc_id = doc.metadata.get("doc_id")
            embeded.append(
                {"vector": self.embed_process(text), "text": text, "idx": doc_id}
            )
            # data.append({"id": i, "vector": embed(text), "text": text})
        return embeded

    def create_milvus_db(self):
        if not self.client.has_collection(self.MILVUS_COLLECTION_NAME):
            fields = [
                # ✅ 主键：自动ID，你完全不用传
                FieldSchema(
                    name="id", dtype=DataType.INT64, is_primary=True, auto_id=True
                ),
                # 向量字段 384 维
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=384),
                # 文本字段
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                # 你自己的业务ID（VARCHAR 必须显式声明 max_length）
                FieldSchema(name="idx", dtype=DataType.VARCHAR, max_length=128),
            ]

            schema = CollectionSchema(fields=fields)
            logger.info("创建milvus 表")
            self.client.create_collection(
                collection_name=self.MILVUS_COLLECTION_NAME,
                schema=schema,
            )

            # 3. 创建索引（MilvusClient 需要 IndexParams 对象）
            index_params = self.client.prepare_index_params()
            index_params.add_index(
                field_name="vector",
                index_type="FLAT",
                metric_type="COSINE",
            )
            self.client.create_index(
                collection_name=self.MILVUS_COLLECTION_NAME,
                index_params=index_params,
            )
            logger.info("创建milvus表成功")
            self._load_collection_with_index_guard()

    def _create_vector_index(self):
        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            index_type="FLAT",
            metric_type="COSINE",
        )
        self.client.create_index(
            collection_name=self.MILVUS_COLLECTION_NAME,
            index_params=index_params,
        )

    def _load_collection_with_index_guard(self):
        index_list = self.client.list_indexes(
            collection_name=self.MILVUS_COLLECTION_NAME, field_name="vector"
        )
        if not index_list:
            logger.warning("集合缺少索引，开始自动补建索引后再加载")
            self._create_vector_index()
        self.client.load_collection(self.MILVUS_COLLECTION_NAME)

    def insert(self, embeded_data):
        logger.info("开始往milvus插入")
        self.client.insert(self.MILVUS_COLLECTION_NAME, embeded_data)
        self.client.flush(self.MILVUS_COLLECTION_NAME)
        logger.info("开始load_collection")
        self._load_collection_with_index_guard()
        logger.info("开始load_collection结束")

    @staticmethod
    def _idx_filter_expr(ids) -> str:
        """idx 为 VARCHAR，与 embed 写入的 doc_id 一致；支持单/多 id。"""
        parts = [str(x) for x in ids if x is not None]
        if not parts:
            return ""
        if len(parts) == 1:
            return f'idx == "{parts[0]}"'
        inner = ", ".join(f'"{p}"' for p in parts)
        return f"idx in [{inner}]"

    def search(self, query, ids):
        if not self.client:
            self.init_milvus()
        if not ids:
            return []
        query_vec = self.embed_process(query)
        flt = self._idx_filter_expr(ids)
        results = self.client.search(
            collection_name=self.MILVUS_COLLECTION_NAME,
            data=[query_vec],
            limit=5,
            filter=flt,
            output_fields=["text"],
        )
        res = [r["entity"]["text"] for r in results[0]]
        docs = Reranker().rerank(
            query,
            res,
        )
        return docs

    def async_process(self, knowledge_id, filename, knowledge_doc_id):
        future = self.executor.submit(
            self.prcoess, knowledge_id, filename, knowledge_doc_id
        )
        future.add_done_callback(
            partial(
                self._on_async_done,
                knowledge_id=knowledge_id,
                filename=filename,
                knowledge_doc_id=knowledge_doc_id,
            )
        )

    def _on_async_done(self, future: Future, knowledge_id, filename, knowledge_doc_id):
        exc = future.exception()
        if exc:
            logger.exception(
                f"向量化后台任务失败，已保留原文件便于排查: knowledge_id={knowledge_id}, filename={filename}, doc_id={knowledge_doc_id}, err={exc}"
            )

    def prcoess(self, knowledge_id, filename, knowledge_doc_id):
        try:
            logger.info("开始执行")
            self.init_milvus()
            logger.info("下载文件")
            file_data = self.download_file(knowledge_id, filename)
            logger.info("处理文件后缀")
            file_ext = os.path.splitext(filename)[1]
            if not file_ext:
                raise ValueError("文件缺少后缀，无法判断文件类型")
            file_type = file_ext[1:].lower()
            logger.info("开始根据类型处理文件 返回langchain_docs")
            langchain_docs = self.file_parse(file_data, file_type)
            logger.info("开始分割文件")
            chunks = self.splitter(langchain_docs, knowledge_doc_id)
            # 初始化一个列表用于存放默认换后的langchain document对象
            documents = []
            for chunk in chunks:
                # 创建一个langchain document对象
                doc_obj = Document(
                    page_content=chunk["text"],
                    metadata={
                        "doc_id": knowledge_doc_id,  # 文档ID
                        "doc_name": filename,  # 文档名称
                        "chunk_index": chunk["chunk_index"],  # 分块索引
                        "id": chunk["id"],  # 分块ID
                        "chunk_id": chunk["id"],  # 分块ID
                    },
                )
                documents.append(doc_obj)

            if not documents:
                raise ValueError("文档分块为空，无法向量化")

            logger.info("分割内容向量化")
            embeded_data = self.embed(documents)
            logger.info("插入向量数据库")
            self.create_milvus_db()
            self.insert(embeded_data)

            self.modfiy_status(knowledge_doc_id, 1)
        except Exception as e:
            logger.exception(f"流程出错: {e}")
            self.modfiy_status(knowledge_doc_id, 2)
            raise e

    def modfiy_status(self, knowledge_doc_id, status):
        with self.transession() as session:
            doc = (
                session.query(Knowledge_Doc)
                .filter(Knowledge_Doc.id == knowledge_doc_id)
                .first()
            )
            if doc:
                doc.status = status
                session.flush()
                session.refresh(doc)
                logger.info(f"修改文件数据状态为:{knowledge_doc_id}={status}")

    def remove_file(self, knowledge_id, filename):
        file_path = Config.BASE_DIR / "uploads" / f"{knowledge_id}" / filename
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info("删除成功")
        else:
            logger.info("文件不存在")

    def download_file(self, knowledge_id, filename):
        file_path = Config.BASE_DIR / "uploads" / f"{knowledge_id}" / filename
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            return data
        except Exception as e:
            logger.error(f"文件下载出错:{e}")
            raise

    def init_milvus(self):
        if not self.inited:
            try:
                logger.info("初始化MILVUS")
                self.client = MilvusClient(uri=Config.MILVUS)
                logger.info("初始化MILVUS成功")
                self.init_embed()
                self.inited = True
            except Exception as e:
                logger.info(f"{e}")

    def file_parse(self, file, file_type):
        return DocumentLoader.load(file, file_type)

    def splitter(self, documents, doc_id):
        return TextSplitter().split_documents(documents, doc_id)


milvus = Milvus()
