from langchain_text_splitters import RecursiveCharacterTextSplitter
import re


class TextSplitter:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""],
        )

    def _clean_redundant_punctuation(self, text: str) -> str:
        # 匹配连续的中文句号
        text = re.sub(r"\。", "", text)
        # 匹配连续的英文句号
        text = re.sub(r"\.", "", text)
        # 匹配连续感叹号/问号
        text = re.sub(r"！", "", text)
        text = re.sub(r"？", "", text)
        text = re.sub(r"[0-9]", "", text)
        # 去掉多余空行
        text = re.sub(r"\n\s*\n", "\n\n", text)
        return text.strip()

    def split_documents(self, documents, doc_id):
        if not documents:
            return []
        # 使用分割器分割文档
        chunks = self.splitter.split_documents(documents)
        results = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_{i}"  # 这是真正的分块的ID,就是文档ID_分块索引
            page_content = self._clean_redundant_punctuation(chunk.page_content)
            if page_content:
                results.append(
                    {
                        "id": chunk_id,
                        "text": self._clean_redundant_punctuation(chunk.page_content),
                        "chunk_index": i,
                        "metadata": chunk.metadata,  # 把
                    }
                )

        return results
