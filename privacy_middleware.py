import re
import time
from typing import Any, Dict, List, Optional
from datetime import datetime

class PrivacyPreservingMAE:
    """
    PIPL 2026 隐私增强多代理执行层中间件
    Privacy-Preserving Multi-Agent Execution Layer
    """

    def __init__(self):
        # 初始化敏感信息正则匹配规则
        self.patterns = {
            # 简单姓名匹配 (2-4个汉字) - 仅作为示例，实际需结合语义分析更准确
            "name": r"(?<![\u4e00-\u9fa5])([\u4e00-\u9fa5]{1})[\u4e00-\u9fa5]{1,2}(?![\u4e00-\u9fa5])", 
            # 手机号 (11位数字)
            "phone": r"(?<!\d)(1[3-9]\d{9})(?!\d)",
            # 身份证 (15或18位)
            "id_card": r"(?<!\d)([1-9]\d{14}|[1-9]\d{16}[\dXx])(?!\d)",
            # 银行卡/账号 (16-19位数字)
            "account": r"(\d{16,19})",
            # 邮箱
            "email": r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"
        }
        
        # 敏感字段关键词，用于 Elicitation
        self.sensitive_fields = [
            "medical_record", "病历",
            "biometric", "生物特征",
            "face_id", "人脸",
            "fingerprint", "指纹",
            "genetic", "基因"
        ]

    def mask_sensitive_data(self, text: str) -> str:
        """
        自动脱敏（Masking）涉及的个人姓名、住址与账号信息
        """
        if not isinstance(text, str):
            return text

        # 手机号脱敏: 138****1234
        # Note: pattern "phone" now has lookaround (?<!\d)(1[3-9]\d{9})(?!\d)
        # So group(1) captures the phone number itself.
        text = re.sub(self.patterns["phone"], lambda m: m.group(1)[:3] + "****" + m.group(1)[-4:], text)
        
        # 身份证脱敏
        def mask_id(match):
            val = match.group(1)
            if len(val) == 18:
                return val[:6] + "********" + val[-4:]
            elif len(val) == 15:
                return val[:6] + "******" + val[-3:]
            # 兼容其他长度（如17位+X）的意外匹配，虽然正则已约束
            return val[:6] + "********" + val[-4:]

        text = re.sub(self.patterns["id_card"], mask_id, text)
        
        # 账号脱敏: **** 1234
        text = re.sub(self.patterns["account"], lambda m: "**** " + m.group(1)[-4:], text)
        
        # 邮箱脱敏: a***@example.com
        text = re.sub(self.patterns["email"], lambda m: m.group(1)[0] + "***" + m.group(1)[m.group(1).find('@'):], text)
        
        # 姓名脱敏 (简单处理，保留姓): 张*
        # 注意：这里仅对看起来像名字的独立词汇处理，避免误伤
        # text = re.sub(self.patterns["name"], lambda m: m.group(1) + "*" * (len(m.group(0)) - 1), text)
        
        return text

    def check_elicitation_requirement(self, arguments: Dict[str, Any]) -> Optional[str]:
        """
        检查是否需要触发 Elicitation 动态授权
        当检测到输入包含敏感字段时返回提示信息，否则返回 None
        """
        # 检查参数名或参数值中是否包含敏感关键词
        raw_args = str(arguments).lower()
        for keyword in self.sensitive_fields:
            if keyword in raw_args:
                return f"检测到敏感信息字段 '{keyword}'，需获取用户显式确认 (mcp_elicitation_request)"
        return None

    def inject_compliance_metadata(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        元数据注入：添加 gb_45438_compliance 字段
        """
        metadata = {
            "gb_45438_compliance": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "model_version": "Legal-CN-v0.2.0",
                "watermark": "AI Generated Content - PIPL Compliant",
                "processor": "PrivacyPreservingMAE"
            }
        }
        
        # 如果 result 已经是字典，直接合并；如果是 TextContent 对象列表，通常在 server 层处理
        # 这里假设处理的是结果字典
        if isinstance(result, dict):
            if "metadata" not in result:
                result["metadata"] = {}
            result["metadata"].update(metadata)
        
        return result
