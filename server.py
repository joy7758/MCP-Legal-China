import mcp_sdk  # 假设已安装 2026 版 MCP SDK

class LegalCNServer:
    """
    Claude Cowork 中国法律插件基础服务器
    功能：提供中国法律风险初筛接口
    """
    def __init__(self):
        self.name = "Legal-CN-Adapter"
        self.version = "0.1.0"

    def check_contract_risk(self, text):
        # 这是一个简单的演示逻辑：识别中国合同中的争议管辖权
        if "纽约" in text or "New York" in text:
            return "【风险提示】检测到非中国境内管辖权，建议修改为：北京或上海仲裁委员会。"
        if "违约金" not in text:
            return "【缺失提示】未检测到违约金条款，建议根据《民法典》增加相应补偿约定。"
        return "【初步检查】未发现明显冲突，建议结合具体业务场景深度审计。"

# 注册 MCP 资源和工具
server = LegalCNServer()
print(f"{server.name} v{server.version} 已启动，等待 Claude Cowork 调用...")
