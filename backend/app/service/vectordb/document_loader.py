from app.utils.logger import get_logger
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_core.documents import Document
from pypdf import PdfReader
from tempfile import NamedTemporaryFile
import os
import fitz
import io
from PIL import Image
import pytesseract


logger = get_logger(__name__)


class DocumentLoader:
    _ocr_engine = None
    _ocr_unavailable = False

    @staticmethod
    def _get_ocr_engine():
        if DocumentLoader._ocr_unavailable:
            return None
        if DocumentLoader._ocr_engine is None:
            try:
                # 懒加载，避免 cv2 环境问题在服务启动阶段直接导致 import 失败
                from rapidocr_onnxruntime import RapidOCR

                DocumentLoader._ocr_engine = RapidOCR()
            except Exception as e:
                DocumentLoader._ocr_unavailable = True
                logger.warning(f"OCR引擎不可用，跳过OCR兜底: {e}")
                return None
        return DocumentLoader._ocr_engine

    @staticmethod
    def _has_text(documents):
        return any((doc.page_content or "").strip() for doc in documents)

    @staticmethod
    def _ocr_pdf(tmp_path):
        ocr_docs = []
        engine = None
        engine_checked = False
        with fitz.open(tmp_path) as pdf:
            for page_index in range(pdf.page_count):
                page = pdf[page_index]
                img_bytes = page.get_pixmap(dpi=300, alpha=False).tobytes("png")
                text = ""

                try:
                    text = (
                        pytesseract.image_to_string(
                            Image.open(io.BytesIO(img_bytes)),
                            lang="chi_sim+eng",
                            config="--oem 3 --psm 6",
                        )
                        or ""
                    ).strip()
                except Exception as e:
                    logger.warning(f"pytesseract OCR 失败，尝试RapidOCR兜底: {e}")

                if not text:
                    if not engine_checked:
                        engine = DocumentLoader._get_ocr_engine()
                        engine_checked = True
                    if engine is not None:
                        try:
                            ocr_result, _ = engine(img_bytes)
                            if ocr_result:
                                text = "\n".join(
                                    line[1] for line in ocr_result if line[1].strip()
                                ).strip()
                        except Exception as e:
                            logger.warning(f"RapidOCR 兜底失败: {e}")

                if text:
                    ocr_docs.append(
                        Document(
                            page_content=text,
                            metadata={
                                "source": tmp_path,
                                "page": page_index,
                                "via": "ocr",
                            },
                        )
                    )
        return ocr_docs

    @staticmethod
    def _fitz_extract_text(tmp_path):
        docs = []
        pdf = fitz.open(tmp_path)
        try:
            for page_index in range(pdf.page_count):
                page = pdf[page_index]
                text = (page.get_text("text") or "").strip()
                if text:
                    docs.append(
                        Document(
                            page_content=text,
                            metadata={
                                "source": tmp_path,
                                "page": page_index,
                                "via": "fitz",
                            },
                        )
                    )
        finally:
            pdf.close()
        return docs

    @staticmethod
    def load_pdf(file_data):
        try:
            with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(file_data)
                tmp_path = tmp_file.name
            try:  # 其实在内部会根据页面进行分割，一个页面对应一个Document
                loader = PyPDFLoader(tmp_path)
                # documents会在加载的时候自动设置metadata
                documents = loader.load()
                if DocumentLoader._has_text(documents):
                    return documents

                # PyPDFLoader 解析为空时，使用 pypdf 做兜底解析
                reader = PdfReader(tmp_path)
                if reader.is_encrypted:
                    # 尝试空密码解密，常见于“已加密但无口令”的文件
                    decrypt_ok = reader.decrypt("")
                    if not decrypt_ok:
                        raise ValueError("PDF已加密，当前无法提取文本，请先解密后重试")
                fallback_docs = []
                for page_index, page in enumerate(reader.pages):
                    text = (page.extract_text() or "").strip()
                    if text:
                        fallback_docs.append(
                            Document(
                                page_content=text,
                                metadata={"source": tmp_path, "page": page_index},
                            )
                        )
                if fallback_docs:
                    logger.warning("PyPDFLoader未提取到文本，已使用PdfReader兜底解析")
                    return fallback_docs
                logger.warning(
                    "PyPDFLoader和PdfReader均未提取到文本，尝试fitz文本提取兜底"
                )
                fitz_docs = DocumentLoader._fitz_extract_text(tmp_path)
                if fitz_docs:
                    logger.warning("已使用fitz兜底提取PDF文本")
                    return fitz_docs

                logger.warning(
                    "PyPDFLoader、PdfReader、fitz均未提取到文本，尝试OCR兜底"
                )
                ocr_docs = DocumentLoader._ocr_pdf(tmp_path)
                if ocr_docs:
                    logger.warning("已使用OCR兜底提取PDF文本")
                    return ocr_docs

                raise ValueError(
                    "PDF未提取到可读文本（已尝试OCR），可能是加密文件或图像质量过低"
                )
            finally:
                # 最后手动删除临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            logger.error(f"加载PDF时出错:{e}")
            raise ValueError(f"加载PDF时出错:{e}")

    @staticmethod
    def load_docx(file_data):
        try:
            with NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
                tmp_file.write(file_data)
                tmp_path = tmp_file.name
            try:
                loader = Docx2txtLoader(tmp_path)
                documents = loader.load()
                return documents
            finally:
                # 最后手动删除临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            logger.error(f"加载PDF时出错:{e}")
            raise ValueError(f"加载PDF时出错:{e}")

    @staticmethod
    def load_text(file_data):
        text = file_data.decode("utf-8")
        try:
            with NamedTemporaryFile(
                delete=False, suffix=".txt", mode="w", encoding="utf-8"
            ) as tmp_file:
                tmp_file.write(text)
                tmp_path = tmp_file.name
            try:
                loader = TextLoader(tmp_path, encoding="utf-8")
                documents = loader.load()
                return documents
            finally:
                # 最后手动删除临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            logger.error(f"加载PDF时出错:{e}")
            raise ValueError(f"加载PDF时出错:{e}")

    @staticmethod
    def load_md(file_data):
        try:
            with NamedTemporaryFile(delete=False, suffix=".md", mode="wb") as tmp_file:
                tmp_file.write(file_data)
                tmp_path = tmp_file.name
            try:
                loader = TextLoader(tmp_path)
                documents = loader.load()
                return documents
            finally:
                # 最后手动删除临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            logger.error(f"加载PDF时出错:{e}")
            raise ValueError(f"加载PDF时出错:{e}")

    @staticmethod
    def load(file_data, file_type):
        file_type = file_type.lower()
        if file_type == "pdf":
            return DocumentLoader.load_pdf(file_data)
        if file_type == "docx":
            return DocumentLoader.load_docx(file_data)
        if file_type in [
            "txt",
        ]:
            return DocumentLoader.load_text(file_data)
        if file_type == "md":
            return DocumentLoader.load_md(file_data)
        raise ValueError(f"不支持的文件类型:{file_type}")
