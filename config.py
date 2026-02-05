"""
MCP-Legal-China 配置管理模块

用于管理服务器配置、环境变量和规则库路径
"""

import os
from typing import Dict, Any
from pathlib import Path


class Config:
    """配置管理类"""
    
    # 服务器基本信息
    SERVER_NAME = os.getenv("MCP_SERVER_NAME", "Legal-CN-Server")
    SERVER_VERSION = os.getenv("MCP_SERVER_VERSION", "0.2.0")
    
    # 调试模式
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # 项目路径
    BASE_DIR = Path(__file__).parent
    RULES_DIR = BASE_DIR / "rules"
    TOOLS_DIR = BASE_DIR / "tools"
    TESTS_DIR = BASE_DIR / "tests"
    DOCS_DIR = BASE_DIR / "docs"
    
    # 外部 API 配置
    TIANYANCHA_API_KEY = os.getenv("TIANYANCHA_API_KEY", "")
    TIANYANCHA_BASE_URL = "https://open.tianyancha.com/services/open"
    
    # 法律数据库路径
    CHINA_LAW_DB_PATH = os.getenv("CHINA_LAW_DB_PATH", "./db/regulations_2026")
    
    # API 限流配置
    API_RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", "10"))  # 每分钟最大调用次数
    API_RATE_PERIOD = int(os.getenv("API_RATE_PERIOD", "60"))  # 时间窗口(秒)
    
    # 风险评估阈值
    PENALTY_THRESHOLD = float(os.getenv("PENALTY_THRESHOLD", "0.3"))  # 违约金阈值 30%
    
    @classmethod
    def ensure_directories(cls):
        """确保所有必要的目录存在"""
        for directory in [cls.RULES_DIR, cls.TOOLS_DIR, cls.TESTS_DIR, cls.DOCS_DIR]:
            directory.mkdir(exist_ok=True)
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """获取配置字典"""
        return {
            "server_name": cls.SERVER_NAME,
            "server_version": cls.SERVER_VERSION,
            "debug": cls.DEBUG,
            "base_dir": str(cls.BASE_DIR),
            "rules_dir": str(cls.RULES_DIR),
            "api_configured": bool(cls.TIANYANCHA_API_KEY),
        }
    
    @classmethod
    def validate(cls) -> bool:
        """验证配置是否有效"""
        # 检查必要的目录
        cls.ensure_directories()
        
        # 如果配置了 API Key,验证其格式
        if cls.TIANYANCHA_API_KEY and len(cls.TIANYANCHA_API_KEY) < 10:
            print("⚠️  警告: TIANYANCHA_API_KEY 格式可能不正确")
            return False
        
        return True


# 在模块加载时验证配置
if __name__ != "__main__":
    Config.validate()
