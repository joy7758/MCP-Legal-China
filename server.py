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
from datetime import datetime
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

try:
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
except ImportError:
    # Fallback for testing environment without mcp installed
    from mock_mcp import (
        Server,
        stdio_server,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
        Resource,
        Prompt,
        PromptMessage,
        GetPromptResult,
    )

from privacy_middleware import PrivacyPreservingMAE

# 引入自定义模块
from errors import AppError, ErrorCode, ElicitationRequiredError, InvalidParamsError
from logger_config import setup_logger, get_trace_id

# 引入 Logic 模块
from Logic import calculate_liquidated_damages, InvalidParamsError as LogicInvalidParamsError, InternalError as LogicInternalError

# 引入 Contract Logic 模块
from contract_logic import ContractLogic, evaluate_judicial_discretion

# 引入 Legal Resources 模块
from legal_resources import LegalResourceProvider


# 加载环境变量
load_dotenv()

# 初始化日志
logger = setup_logger()


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
        
        # 初始化隐私增强组件
        self.privacy_middleware = PrivacyPreservingMAE()

        # 初始化法律资源提供者
        self.legal_resource_provider = LegalResourceProvider()
        
        # 注册处理器
        self._register_handlers()
        
        if self.debug:
            print(f"[DEBUG] {self.name} v{self.version} 初始化完成")
        
        logger.info("Server initialized", extra={"trace_id": get_trace_id(), "version": self.version, "debug": self.debug})
    
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
                ),
                Tool(
                    name="calculate_damages",
                    description="计算违约金，包含法律红线检查 (民间借贷利率封顶、劳动合同违约金上限)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "scenario": {
                                "type": "string",
                                "enum": ["general_contract", "private_lending", "labor_contract"],
                                "description": "场景类型"
                            },
                            "actual_loss": {"type": "number", "description": "实际损失"},
                            "rate": {"type": "number", "description": "利率 (民间借贷场景)"},
                            "training_cost": {"type": "number", "description": "培训费用 (劳动合同场景)"},
                            "total_months": {"type": "integer", "description": "服务期总月数 (劳动合同场景)"},
                            "remaining_months": {"type": "integer", "description": "剩余月数 (劳动合同场景)"},
                            "simulate_db_failure": {"type": "boolean", "description": "是否模拟数据库同步失败 (测试用)"}
                        },
                        "required": ["scenario"]
                    }
                ),
                Tool(
                    name="evaluate_judicial_discretion",
                    description="基于《九民纪要》与司法解释的裁量权行使标准评估违约金",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "loss": {
                                "description": "实际损失金额或 PID (Resolves to {amount: float})",
                                "anyOf": [{"type": "number"}, {"type": "string"}]
                            },
                            "performance": {
                                "description": "合同履行比例 (0.0-1.0) 或 PID (Resolves to {ratio: float})",
                                "anyOf": [{"type": "number"}, {"type": "string"}]
                            },
                            "fault": {
                                "description": "过错程度评分 (1.0-2.0, 2.0为恶意) 或 PID (Resolves to {score: float})",
                                "anyOf": [{"type": "number"}, {"type": "string"}]
                            },
                            "contract_pid": {
                                "type": "string",
                                "description": "关联的合同 PID (可选)"
                            }
                        },
                        "required": ["loss", "performance", "fault"]
                    }
                ),
                Tool(
                    name="health_check",
                    description="服务器健康检查探针",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    }
                )
            ]
        
        # 注册 Tools 调用处理器
        @self.app.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            return await self._handle_call_tool(name, arguments)
    
    async def _handle_call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """处理工具调用请求 (提取为方法以便测试)"""
        trace_id = get_trace_id()
        logger.info(f"Tool called: {name}", extra={"trace_id": trace_id, "arguments": arguments})
        
        try:
            # 1. 实现 Elicitation 动态授权钩子
            elicitation_msg = self.privacy_middleware.check_elicitation_requirement(arguments)
            if elicitation_msg:
                logger.warning("Elicitation required", extra={"trace_id": trace_id, "reason": elicitation_msg})
                raise ElicitationRequiredError(f"[Elicitation Required] {elicitation_msg}")

            # 2. 执行工具逻辑
            result_contents: List[TextContent] = []
            
            if name == "check_contract_risk":
                # Inject trace_id into kwargs if supported by _check_contract_risk or underlying logic
                # For this specific refactor, we are focusing on Logic.py integration
                # Let's see if check_contract_risk uses Logic.py. It seems it uses basic string matching currently.
                # But let's add causal_trace_id to arguments for logging purpose if needed down the line.
                result_contents = await self._check_contract_risk(arguments)
            elif name == "analyze_legal_clause":
                # analyze_legal_clause mostly returns static analysis, but let's check if we can enhance it.
                result_contents = await self._analyze_legal_clause(arguments)
            elif name == "get_legal_suggestion":
                result_contents = await self._get_legal_suggestion(arguments)
            elif name == "calculate_damages":
                # New tool exposing the Logic.py calculation
                result_contents = await self._calculate_damages(arguments, trace_id)
            elif name == "evaluate_judicial_discretion":
                # New tool exposing the contract_logic.py calculation
                result_contents = await self._evaluate_judicial_discretion(arguments, trace_id)
            elif name == "health_check":
                # Health check implementation with maturity and consistency check
                maturity_check = self._check_transcription_maturity()
                consistency_check = self._check_legal_db_consistency()
        
                health_status = {
                    "status": "healthy" if maturity_check["status"] == "ok" and consistency_check["status"] == "ok" else "unhealthy",
                    "version": self.version,
                    "timestamp": os.popen("date -u +%Y-%m-%dT%H:%M:%SZ").read().strip(),
                    "checks": {
                        "transcription_maturity": maturity_check,
                        "legal_db_consistency": consistency_check
                    }
                }
                
                result_contents = [TextContent(type="text", text=json.dumps(health_status, ensure_ascii=False))]
            else:
                logger.error(f"Unknown tool: {name}", extra={"trace_id": trace_id})
                raise InvalidParamsError(f"未知工具: {name}")
                
        except AppError as e:
            logger.error(f"AppError in tool execution: {e.message}", extra={"trace_id": trace_id, "error_code": e.code.value})
            # 将结构化错误返回给 Client (实际协议中可能需要特定格式，这里转为 TextContent)
            return [TextContent(type="text", text=json.dumps(e.to_dict(), ensure_ascii=False))]
            
        except Exception as e:
            logger.exception("Unexpected error during tool execution", extra={"trace_id": trace_id})
            return [TextContent(type="text", text=json.dumps({
                "code": ErrorCode.INTERNAL_ERROR.value,
                "error": "Internal Error",
                "message": str(e)
            }, ensure_ascii=False))]

        # 3. Privacy Preserving (输出脱敏) & Metadata Injection
        processed_contents = []
        for content in result_contents:
            if content.type == "text":
                try:
                    # 尝试解析 JSON 进行结构化处理
                    data = json.loads(content.text)
                    
                    # 注入合规元数据 (gb_45438_compliance)
                    data = self.privacy_middleware.inject_compliance_metadata(data)
                    
                    # 序列化后进行脱敏
                    text_str = json.dumps(data, ensure_ascii=False, indent=2)
                    masked_text = self.privacy_middleware.mask_sensitive_data(text_str)
                    
                    processed_contents.append(TextContent(
                        type="text",
                        text=masked_text
                    ))
                except json.JSONDecodeError:
                    # 如果不是 JSON，直接对文本进行脱敏
                    masked_text = self.privacy_middleware.mask_sensitive_data(content.text)
                    processed_contents.append(TextContent(
                        type="text",
                        text=masked_text
                    ))
            else:
                processed_contents.append(content)
        
        return processed_contents
        
    # 注册 Resources 列表处理器
    @self.app.list_resources()
    async def list_resources() -> List[Resource]:
        """返回所有可用的资源列表"""
        resources = []
        for uri, meta in self.legal_resource_provider.resources.items():
            resources.append(Resource(
                uri=uri,
                name=meta.get("name", "Unknown Resource"),
                description=meta.get("description", f"Legal resource: {meta.get('name')}"),
                mimeType="application/json+ld"  # Updated MIME type for JSON-LD wrapped content
            ))
        return resources
    
    # 注册 Resources 读取处理器
    @self.app.read_resource()
    async def read_resource(uri: str) -> str:
        """读取指定资源的内容 (返回 FDO 兼容的 JSON-LD)"""
        trace_id = get_trace_id()
        logger.info(f"Reading resource: {uri}", extra={"trace_id": trace_id})
        
        try:
            content = self.legal_resource_provider.get_resource_content(uri)
            return content
        except ValueError as e:
            logger.warning(f"Resource not found: {uri}", extra={"trace_id": trace_id})
            raise InvalidParamsError(f"未知资源: {uri}")
        except Exception as e:
            logger.exception("Error reading resource", extra={"trace_id": trace_id})
            raise
    
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

    async def _check_contract_risk(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """检查合同风险"""
        contract_text = arguments.get("contract_text", "")
        check_types = arguments.get("check_types", ["jurisdiction", "penalty"])
        
        result = self.logic.check_contract_risk(contract_text, check_types)
        
        # Generate a PID for this report
        # In a real scenario, we might want to link this to a parent document PID if provided in arguments
        # For now, we treat this report as a new root or child if 'parent_pid' is in arguments
        parent_pid = arguments.get("parent_pid")
        metadata = {
            "type": "RiskAssessmentReport",
            "generated_by": "check_contract_risk",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        report_pid = self.legal_resource_provider.generate_pid(result, metadata, parent_pid)
        
        # Inject PID into the result
        result["report_pid"] = report_pid
        if parent_pid:
            result["related_to"] = parent_pid

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

    async def _calculate_damages(self, arguments: Dict[str, Any], trace_id: str) -> List[TextContent]:
        """调用 Logic.py 进行违约金计算，包含红线检查"""
        try:
            result = calculate_liquidated_damages(
                scenario=arguments.get("scenario"),
                actual_loss=arguments.get("actual_loss", 0.0),
                rate=arguments.get("rate", 0.0),
                training_cost=arguments.get("training_cost", 0.0),
                total_months=arguments.get("total_months", 0),
                remaining_months=arguments.get("remaining_months", 0),
                simulate_db_failure=arguments.get("simulate_db_failure", False),
                causal_trace_id=trace_id
            )
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        
        # 捕获 Logic.py 抛出的自定义异常，并在 Server 层转译为 AppError
        # 虽然 server.py 里已经捕获了 AppError，但这里我们可以做更细致的日志或者转换
        except LogicInvalidParamsError as e:
            # Logic 层抛出的 InvalidParamsError 已经是 AppError 的子类
            logger.warning(f"Logic invalid params: {e.message}", extra={"trace_id": trace_id, "details": e.details})
            raise e
        except LogicInternalError as e:
            # Logic 层抛出的 InternalError 已经是 AppError 的子类
            logger.error(f"Logic internal error: {e.message}", extra={"trace_id": trace_id})
            raise e
        except Exception as e:
            logger.exception("Unexpected error in calculation", extra={"trace_id": trace_id})
            raise InternalError(f"Calculation failed: {str(e)}")

    async def _evaluate_judicial_discretion(self, arguments: Dict[str, Any], trace_id: str) -> List[TextContent]:
        """调用 contract_logic.py 进行司法裁量权评估"""
        try:
            result = evaluate_judicial_discretion(
                loss_param=arguments.get("loss"),
                performance_param=arguments.get("performance"),
                fault_param=arguments.get("fault"),
                contract_pid=arguments.get("contract_pid"),
                resource_provider=self.legal_resource_provider
            )
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        except Exception as e:
            logger.exception("Unexpected error in judicial discretion evaluation", extra={"trace_id": trace_id})
            raise InternalError(f"Evaluation failed: {str(e)}")

    # ==================== Health Check Helpers ====================

    def _check_transcription_maturity(self) -> Dict[str, Any]:
        """监控逻辑核的“转录成熟度”"""
        # 模拟逻辑核成熟度检查
        # 实际场景可能涉及检查模型训练步数、评估指标等
        return {
            "status": "ok",
            "score": 0.98,
            "message": "Logic core transcription maturity is sufficient."
        }

    def _check_legal_db_consistency(self) -> Dict[str, Any]:
        """定期校验本地法条索引与最高法公报的一致性"""
        # 模拟一致性校验
        # 实际场景会比对本地数据库哈希与远程最高法公报哈希
        try:
            # 模拟偶尔的校验失败（仅用于测试，此处默认成功）
            is_consistent = True
            if is_consistent:
                return {
                    "status": "ok",
                    "last_sync": "2024-05-20T10:00:00Z",
                    "source": "Supreme People's Court Gazette"
                }
            else:
                 return {
                    "status": "error",
                    "message": "Local index inconsistent with SPC Gazette"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
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
        # 使用 logger 替代 print
        # 注意: stdio 模式下，print 到 stdout 会干扰 MCP 协议通信
        # logging 默认输出到 stderr，这是安全的
        logger.info(f"{self.name} v{self.version} starting...", extra={"trace_id": "startup"})
        
        async with stdio_server() as (read_stream, write_stream):
            logger.info("MCP Server running on stdio", extra={"trace_id": "startup"})
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
