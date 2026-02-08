"""
Privacy and Security Logic for MCP-Legal-China
"""

import re
import json
from typing import Dict, Any, List, Optional

class PrivacyPreservingMAE:
    """
    Privacy Preserving Multi-Agent Execution Layer
    负责对输出数据进行脱敏处理，保护个人隐私信息 (PII)。
    符合 PIPL (Personal Information Protection Law) 要求。
    """

    def __init__(self):
        # 简单的正则匹配模式，用于演示脱敏
        self.patterns = {
            "id_card": r"\d{17}[\dXx]",
            "phone": r"1[3-9]\d{9}",
            "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "name": r"(?<=姓名[:：\s])[\u4e00-\u9fa5]{2,4}" # 简单的上下文匹配
        }

    def mask_data(self, data: Any) -> Any:
        """
        递归地对数据进行脱敏处理
        """
        if isinstance(data, str):
            return self._mask_string(data)
        elif isinstance(data, list):
            return [self.mask_data(item) for item in data]
        elif isinstance(data, dict):
            return {k: self.mask_data(v) for k, v in data.items()}
        else:
            return data

    def _mask_string(self, text: str) -> str:
        """
        对字符串进行正则匹配和脱敏
        """
        masked_text = text
        
        # 身份证号脱敏: 保留前6后4
        def mask_id(match):
            s = match.group()
            return s[:6] + "*" * 8 + s[-4:]
        masked_text = re.sub(self.patterns["id_card"], mask_id, masked_text)

        # 手机号脱敏: 保留前3后4
        def mask_phone(match):
            s = match.group()
            return s[:3] + "****" + s[-4:]
        masked_text = re.sub(self.patterns["phone"], mask_phone, masked_text)

        # 邮箱脱敏: 只保留 @ 后面的
        def mask_email(match):
            s = match.group()
            try:
                name, domain = s.split('@')
                return name[0] + "***" + "@" + domain
            except ValueError:
                return s
        masked_text = re.sub(self.patterns["email"], mask_email, masked_text)

        return masked_text


class Elicitation:
    """
    Elicitation Detection Layer
    负责检测输入中的恶意诱导或敏感信息请求。
    """

    def __init__(self):
        # 敏感关键词列表
        self.sensitive_keywords = [
            "规避法律", "逃避监管", "洗钱", "非法集资", 
            "漏洞利用", "攻击", "渗透", "social engineering",
            "绕过", "bypass"
        ]

    def check_input(self, arguments: Dict[str, Any]) -> List[str]:
        """
        检查输入参数是否包含敏感内容
        返回检测到的风险列表
        """
        risks = []
        input_str = json.dumps(arguments, ensure_ascii=False)
        
        for keyword in self.sensitive_keywords:
            if keyword in input_str:
                risks.append(f"检测到敏感关键词: {keyword}")
        
        return risks
