from app.config import Config
import os
from app.utils.logger import get_logger
import re

logger = get_logger(__file__)


class Image_control:
    def __init__(self):
        self.IMAGE_STORE = Config.IMAGE_STORE

    def del_image(self, imge_path):
        if self.IMAGE_STORE == "local":
            self.del_local_image(imge_path)

    def del_local_image(self, imge_path):
        imge_path = get_upload_path(imge_path)
        real_path = str(Config.BASE_DIR / imge_path)
        if not os.path.exists(real_path):
            logger.error(f"删除{real_path}图片失败")
            return False
        else:
            logger.info(f"删除{real_path}图片成功")
            os.remove(real_path)
            return True


def get_upload_path(url: str) -> str:
    if not url:
        return ""

    # 正则匹配：去掉 http(s) 开头，只保留 uploads 开始的路径
    match = re.search(r"https?://[^/]+/(.*)", url)

    if match:
        return match.group(1)  # 返回后半段：uploads/xxx.jpg
    return url


image_control = Image_control()
