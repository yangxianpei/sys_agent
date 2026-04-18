import logging  
from app.config import Config
from pathlib import Path
# 用于日志文件轮转
from logging.handlers import RotatingFileHandler
class Logger:
    FORMAT_STRING = (
        "%(levelname)s：  %(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(message)s"
    )
    def __init__(self):
        self.log_level = Config.LOG_LEVEL
        self.enable_file=Config.LOG_ENABLE_FILE
        self.enable_console=Config.LOG_ENABLE_CONSOLE
        self.log_path = Path(Config.LOG_FILE)
        self.init_logger()
            
    def init_logger(self):
        root_logger= logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(self.log_level)
        if self.enable_file:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                self.log_path,
                maxBytes=Config.LOG_MAX_BYTES,  # 最大文件大小
                backupCount=Config.LOG_BACKUP_COUNT,  # 最多保留几份最新的日志文件
                encoding="utf-8",  # 编码
            )
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(logging.Formatter(self.FORMAT_STRING))
            root_logger.addHandler(file_handler)
        if self.enable_console:
            console_handler=logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(self.FORMAT_STRING))
            root_logger.addHandler(console_handler)
        # 捕获warning模块的警告作为文件日志
        logging.captureWarnings(True)



    def get_logger(self, name):
        if name is None:
            return logging.getLogger()
        # 返回指定的名称的日志处理器
        return logging.getLogger(name)


loggerManager = Logger()


def get_logger(name):
    return loggerManager.get_logger(name)
