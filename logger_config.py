import logging
import json
import time
import uuid
import os
from typing import Optional

class JSONFormatter(logging.Formatter):
    """
    简易的 JSON 日志格式化器，不依赖外部库
    """
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 合并 extra 字段
        if hasattr(record, "trace_id"):
            log_record["trace_id"] = record.trace_id
            
        # 处理异常信息
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record, ensure_ascii=False)

def setup_logger(name: str = "LegalCNServer", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 清除现有的 handlers
    if logger.hasHandlers():
        logger.handlers.clear()
        
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    
    return logger

def get_trace_id() -> str:
    return str(uuid.uuid4())
