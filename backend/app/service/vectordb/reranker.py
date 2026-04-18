from sentence_transformers import CrossEncoder
from app.config import Config
from app.utils.logger import get_logger

logger = get_logger(__name__)


class Reranker:
    def __init__(self):
        self.reranker = None

    def init_Reranker(self):
        if not self.reranker:
            self.reranker = CrossEncoder(Config.RERANK_MODEL_NAME)

    def rerank(self, query, texts, top_k=3):
        self.init_Reranker()
        if not texts:
            return []
        try:
            # 用cross-encoder这个模型计算每个对的相关性分数
            pairs = [[query, doc] for doc in texts]
            scores = self.reranker.predict(pairs)
            # 把分数转成列表
            scores = list(scores)
            scores_float = [float(score) for score in scores]
            # 计算分数是最小值
            min_score = min(scores_float) if scores_float else 0.0
            # 计算分数中的最大值
            max_score = max(scores_float) if scores_float else 1.0
            # 对分数进行归一化
            normalized_scores = [
                (
                    (score - min_score) / (max_score - min_score)
                    if max_score > min_score
                    else 0.0
                )
                for score in scores_float
            ]
            doc_scores = [doc for doc, score in zip(texts, normalized_scores)]
            doc_scores.sort(key=lambda x: x[1], reverse=True)
            logger.info(f"CrossEncoder重排序：已经重排序了{len(doc_scores)}个文档")
            return doc_scores[:top_k]
        except Exception as e:
            logger.error(f"CrossEncoder重排序出错:{str(e)}")
            raise e
