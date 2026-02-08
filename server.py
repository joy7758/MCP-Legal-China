"""
MCP-Legal-China Server
中国法律增强插件 MCP 服务器

功能:
- 提供中国法律风险初筛接口
- 支持合同审查和风险评估
- 对接外部 API (天眼查等)
"""

import os
import json
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    Resource,
    Prompt,
    PromptMessage,
    GetPromptResult,
)

from contract_logic import ContractLogic

# 加载环境变量
load_dotenv()


class LegalCNServer:
    """
    Claude Cowork 中国法律插件服务器
    
    提供三类 MCP 能力:
    1. Tools - 法律风险检查工具
    2. Resources - 法律条文和模板资源
    3. Prompts - 合同审查流程提示词
    """
    
    def __init__(self):
        self.name = os.getenv("MCP_SERVER_NAME", "Legal-CN-Server")
        self.version = os.getenv("MCP_SERVER_VERSION", "0.2.0")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # 初始化业务逻辑
        self.logic = ContractLogic()
        
        # 创建 MCP Server 实例
        self.app = Server(self.name)
        
        # 注册处理器
        self._register_handlers()
        
        if self.debug:
            print(f"[DEBUG] {self.name} v{self.version} 初始化完成")
    
    def _register_handlers(self):
        """注册 MCP 协议处理器"""
        
        # 注册 Tools 列表处理器
        @self.app.list_tools()
        async def list_tools() -> List[Tool]:
            """返回所有可用的工具列表"""
            return [
                Tool(
                    name="check_contract_risk",
                    description="检查合同文本中的法律风险,识别管辖权、违约金等关键条款",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "contract_text": {
                                "type": "string",
                                "description": "合同文本内容"
                            },
                            "check_types": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "检查类型,可选: jurisdiction(管辖权), penalty(违约金), liability(责任条款)",
                                "default": ["jurisdiction", "penalty"]
                            }
                        },
                        "required": ["contract_text"]
                    }
                ),
                Tool(
                    name="analyze_legal_clause",
                    description="分析特定法律条款的合规性,基于《民法典》进行评估",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "clause_text": {
                                "type": "string",
                                "description": "需要分析的条款文本"
                            },
                            "clause_type": {
                                "type": "string",
                                "enum": ["penalty", "liability", "termination", "jurisdiction"],
                                "description": "条款类型"
                            }
                        },
                        "required": ["clause_text", "clause_type"]
                    }
                ),
                Tool(
                    name="get_legal_suggestion",
                    description="根据风险类型获取法律建议和修改方案",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "risk_type": {
                                "type": "string",
                                "enum": ["jurisdiction", "penalty", "liability", "general"],
                                "description": "风险类型"
                            },
                            "context": {
                                "type": "string",
                                "description": "具体情况描述"
                            }
                        },
                        "required": ["risk_type"]
                    }
                )
            ]
        
        # 注册 Tools 调用处理器
        @self.app.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """处理工具调用请求"""
            
            if self.debug:
                print(f"[DEBUG] 调用工具: {name}, 参数: {arguments}")
            
            if name == "check_contract_risk":
                return await self._check_contract_risk(arguments)
            
            elif name == "analyze_legal_clause":
                return await self._analyze_legal_clause(arguments)
            
            elif name == "get_legal_suggestion":
                return await self._get_legal_suggestion(arguments)
            
            else:
                raise ValueError(f"未知工具: {name}")
        
        # 注册 Resources 列表处理器
        @self.app.list_resources()
        async def list_resources() -> List[Resource]:
            """返回所有可用的资源列表"""
            return [
                Resource(
                    uri="legal://civil-code/contract",
                    name="《民法典》合同编",
                    description="中国民法典合同编相关条文",
                    mimeType="text/markdown"
                ),
                Resource(
                    uri="legal://templates/contract-checklist",
                    name="合同审查清单",
                    description="标准合同审查要点清单",
                    mimeType="application/json"
                ),
                Resource(
                    uri="legal://rules/penalty-assessment",
                    name="违约金评估规则",
                    description="违约金过高判定标准和计算方法",
                    mimeType="application/json"
                )
            ]
        
        # 注册 Resources 读取处理器
        @self.app.read_resource()
        async def read_resource(uri: str) -> str:
            """读取指定资源的内容"""
            
            if self.debug:
                print(f"[DEBUG] 读取资源: {uri}")
            
            if uri == "legal://civil-code/contract":
                return self.logic.get_civil_code_contract()
            
            elif uri == "legal://templates/contract-checklist":
                return self.logic.get_contract_checklist()
            
            elif uri == "legal://rules/penalty-assessment":
                return self.logic.get_penalty_rules()
            
            else:
                raise ValueError(f"未知资源: {uri}")
        
        # 注册 Prompts 列表处理器
        @self.app.list_prompts()
        async def list_prompts() -> List[Prompt]:
            """返回所有可用的提示词模板"""
            return [
                Prompt(
                    name="contract_review_flow",
                    description="标准合同审查工作流程",
                    arguments=[
                        {
                            "name": "contract_type",
                            "description": "合同类型 (如: 买卖合同、服务合同等)",
                            "required": False
                        }
                    ]
                ),
                Prompt(
                    name="risk_assessment_template",
                    description="风险评估报告模板",
                    arguments=[
                        {
                            "name": "company_name",
                            "description": "公司名称",
                            "required": True
                        }
                    ]
                )
            ]
        
        # 注册 Prompts 获取处理器
        @self.app.get_prompt()
        async def get_prompt(name: str, arguments: Optional[Dict[str, str]] = None) -> GetPromptResult:
            """获取指定提示词的内容"""
            
            if self.debug:
                print(f"[DEBUG] 获取提示词: {name}, 参数: {arguments}")
            
            if name == "contract_review_flow":
                return self._get_contract_review_prompt(arguments or {})
            
            elif name == "risk_assessment_template":
                return self._get_risk_assessment_prompt(arguments or {})
            
            else:
                raise ValueError(f"未知提示词: {name}")
    
    # ==================== Tool 实现方法 (委托给 ContractLogic) ====================
    
    async def _check_contract_risk(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """检查合同风险"""
        contract_text = arguments.get("contract_text", "")
        check_types = arguments.get("check_types", ["jurisdiction", "penalty"])
        
        result = self.logic.check_contract_risk(contract_text, check_types)
        
        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]
    
    async def _analyze_legal_clause(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """分析法律条款的合规性"""
        clause_text = arguments.get("clause_text", "")
        clause_type = arguments.get("clause_type", "general")
        
        result = self.logic.analyze_legal_clause(clause_text, clause_type)
        
        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]
    
    async def _get_legal_suggestion(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """获取法律建议"""
        risk_type = arguments.get("risk_type", "general")
        context = arguments.get("context", "")
        
        result = self.logic.get_legal_suggestion(risk_type, context)
        
        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]
    
    # ==================== Prompt 实现方法 (委托给 ContractLogic) ====================
    
    def _get_contract_review_prompt(self, arguments: Dict[str, str]) -> GetPromptResult:
        """获取合同审查流程提示词"""
        contract_type = arguments.get("contract_type", "通用合同")
        
        prompt_text = self.logic.get_contract_review_prompt_content(contract_type)
        
        return GetPromptResult(
            description=f"{contract_type}审查流程",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=prompt_text)
                )
            ]
        )
    
    def _get_risk_assessment_prompt(self, arguments: Dict[str, str]) -> GetPromptResult:
        """获取风险评估提示词"""
        company_name = arguments.get("company_name", "")
        
        if not company_name:
            raise ValueError("company_name 参数是必需的")
        
        prompt_text = self.logic.get_risk_assessment_prompt_content(company_name)
        
        return GetPromptResult(
            description=f"{company_name} 风险评估",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=prompt_text)
                )
            ]
        )
    
    async def run(self):
        """启动 MCP 服务器"""
        print(f"🚀 {self.name} v{self.version} 正在启动...")
        print(f"📋 提供的能力:")
        print(f"   - Tools: 3 个法律工具")
        print(f"   - Resources: 3 个法律资源")
        print(f"   - Prompts: 2 个工作流模板")
        print(f"⚖️  等待 Claude Cowork 调用...\n")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.app.run(
                read_stream,
                write_stream,
                self.app.create_initialization_options()
            )


# ==================== 主程序入口 ====================

async def main():
    """主函数"""
    server = LegalCNServer()
    await server.run()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
