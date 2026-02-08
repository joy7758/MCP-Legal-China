"""
MCP-Legal-China Contract Logic
法律业务逻辑模块

功能:
- 合同风险检查逻辑
- 法律条款分析逻辑
- 法律建议生成逻辑
- 法律资源读取
- 提示词生成
"""

import json
import os
from typing import Dict, Any, List, Optional


class ContractLogic:
    """法律业务逻辑处理类"""

    def __init__(self):
        # 法律规则库路径 (如果有需要的话)
        self.rules_path = os.path.join(os.path.dirname(__file__), "rules")

    # ==================== Tools Logic ====================

    def check_contract_risk(self, contract_text: str, check_types: List[str]) -> Dict[str, Any]:
        """
        检查合同风险
        """
        risks = []

        # 检查管辖权
        if "jurisdiction" in check_types:
            if "纽约" in contract_text or "New York" in contract_text:
                risks.append({
                    "type": "jurisdiction",
                    "level": "高风险",
                    "description": "检测到非中国境内管辖权条款",
                    "suggestion": "建议修改为: 北京仲裁委员会或上海仲裁委员会"
                })
            elif "香港" in contract_text or "Hong Kong" in contract_text:
                risks.append({
                    "type": "jurisdiction",
                    "level": "中风险",
                    "description": "检测到香港管辖权条款",
                    "suggestion": "如涉及内地业务,建议使用内地仲裁机构"
                })

        # 检查违约金
        if "penalty" in check_types:
            if "违约金" not in contract_text and "赔偿" not in contract_text:
                risks.append({
                    "type": "penalty",
                    "level": "中风险",
                    "description": "未检测到违约金或赔偿条款",
                    "suggestion": "建议根据《民法典》第585条增加违约金约定"
                })

            # 检查违约金比例
            if "100%" in contract_text or "全额" in contract_text:
                risks.append({
                    "type": "penalty",
                    "level": "高风险",
                    "description": "违约金比例可能过高",
                    "suggestion": "根据司法实践,违约金一般不超过合同金额的30%"
                })

        # 检查责任条款
        if "liability" in check_types:
            if "不承担任何责任" in contract_text or "免除全部责任" in contract_text:
                risks.append({
                    "type": "liability",
                    "level": "高风险",
                    "description": "检测到可能无效的免责条款",
                    "suggestion": "根据《民法典》第506条,免除故意或重大过失责任的条款无效"
                })

        # 生成报告
        if not risks:
            result = {
                "status": "通过",
                "message": "初步检查未发现明显法律风险",
                "recommendation": "建议结合具体业务场景进行深度审计"
            }
        else:
            result = {
                "status": "发现风险",
                "risk_count": len(risks),
                "risks": risks,
                "recommendation": "建议咨询专业律师进行详细审查"
            }

        return result

    def analyze_legal_clause(self, clause_text: str, clause_type: str) -> Dict[str, Any]:
        """分析法律条款的合规性"""
        analysis = {
            "clause_type": clause_type,
            "clause_text": clause_text,
            "compliance_status": "需要审查",
            "legal_basis": [],
            "suggestions": []
        }

        # 根据条款类型进行分析
        if clause_type == "penalty":
            analysis["legal_basis"].append("《民法典》第585条 - 违约金条款")
            analysis["legal_basis"].append("最高人民法院关于适用《民法典》合同编的解释")

            if "%" in clause_text or "倍" in clause_text:
                analysis["suggestions"].append("注意违约金比例,避免被认定为过高")

            analysis["compliance_status"] = "基本合规"

        elif clause_type == "jurisdiction":
            analysis["legal_basis"].append("《民事诉讼法》第34条 - 协议管辖")

            if any(place in clause_text for place in ["北京", "上海", "深圳", "广州"]):
                analysis["compliance_status"] = "合规"
            else:
                analysis["suggestions"].append("建议选择与合同有实际联系的地点")

        return analysis

    def get_legal_suggestion(self, risk_type: str, context: str) -> Dict[str, Any]:
        """获取法律建议"""
        suggestions = {
            "jurisdiction": {
                "title": "管辖权条款建议",
                "recommendations": [
                    "优先选择仲裁方式解决争议,效率更高",
                    "建议选择: 北京仲裁委员会、上海仲裁委员会、深圳国际仲裁院",
                    "如选择诉讼,应选择与合同履行地或被告住所地有关的法院"
                ],
                "template": "因本合同引起的或与本合同有关的任何争议,均应提交[北京仲裁委员会]按照其仲裁规则进行仲裁。仲裁裁决是终局的,对双方均有约束力。"
            },
            "penalty": {
                "title": "违约金条款建议",
                "recommendations": [
                    "违约金数额应当合理,一般不超过实际损失的30%",
                    "可以约定违约金的计算方法,如按日计算",
                    "建议同时约定损害赔偿的计算方法"
                ],
                "template": "一方违约的,应向守约方支付违约金,违约金金额为合同总价款的[10%-30%]。违约金不足以弥补实际损失的,守约方有权要求赔偿实际损失。"
            },
            "liability": {
                "title": "责任条款建议",
                "recommendations": [
                    "不得免除故意或重大过失造成的责任",
                    "责任限制应当公平合理",
                    "建议明确不可抗力的处理方式"
                ],
                "template": "除因故意或重大过失造成的损失外,任何一方对本合同项下的间接损失、预期利润损失不承担赔偿责任。"
            },
            "general": {
                "title": "通用法律建议",
                "recommendations": [
                    "确保合同各方主体资格合法",
                    "明确合同标的、数量、质量、价款等主要条款",
                    "约定明确的履行期限和履行方式",
                    "建议聘请专业律师进行合同审查"
                ]
            }
        }

        result = suggestions.get(risk_type, suggestions["general"])
        if context:
            result["context"] = context

        return result

    # ==================== Resources Logic ====================

    def get_civil_code_contract(self) -> str:
        """获取民法典合同编相关内容"""
        return """# 《中华人民共和国民法典》合同编 (摘要)

## 第585条 违约金

当事人可以约定一方违约时应当根据违约情况向对方支付一定数额的违约金,也可以约定因违约产生的损失赔偿额的计算方法。

约定的违约金低于造成的损失的,人民法院或者仲裁机构可以根据当事人的请求予以增加;约定的违约金过分高于造成的损失的,人民法院或者仲裁机构可以根据当事人的请求予以适当减少。

## 第506条 免责条款的效力

合同中的下列免责条款无效:
(一) 造成对方人身损害的;
(二) 因故意或者重大过失造成对方财产损失的。

## 第577条 违约责任

当事人一方不履行合同义务或者履行合同义务不符合约定的,应当承担继续履行、采取补救措施或者赔偿损失等违约责任。
"""

    def get_contract_checklist(self) -> str:
        """获取合同审查清单"""
        checklist = {
            "基本信息审查": [
                "合同各方主体资格是否合法",
                "合同名称是否准确反映合同性质",
                "合同签订日期和生效日期是否明确"
            ],
            "主要条款审查": [
                "合同标的是否明确",
                "数量、质量标准是否清晰",
                "价款或报酬及支付方式是否约定",
                "履行期限、地点和方式是否明确"
            ],
            "风险条款审查": [
                "违约责任是否约定",
                "争议解决方式是否明确",
                "保密条款是否完善",
                "知识产权归属是否清晰"
            ],
            "合规性审查": [
                "是否违反法律强制性规定",
                "免责条款是否有效",
                "管辖权约定是否合法",
                "是否需要政府审批或备案"
            ]
        }
        return json.dumps(checklist, ensure_ascii=False, indent=2)

    def get_penalty_rules(self) -> str:
        """获取违约金评估规则"""
        rules = {
            "法律依据": "《民法典》第585条",
            "基本原则": "违约金应当与实际损失相当,不得过分高于实际损失",
            "司法实践标准": {
                "一般标准": "违约金不超过实际损失的30%",
                "特殊情况": "在某些商事合同中,可能允许更高比例",
                "调整机制": "当事人可以请求法院或仲裁机构调整过高或过低的违约金"
            },
            "计算方法": [
                "按合同总价款的百分比计算",
                "按日计算 (如每日万分之五)",
                "按实际损失的倍数计算"
            ],
            "注意事项": [
                "违约金与损害赔偿不能同时主张",
                "违约金过高的举证责任在违约方",
                "可以约定违约金的上限"
            ]
        }
        return json.dumps(rules, ensure_ascii=False, indent=2)

    # ==================== Prompts Logic ====================

    def get_contract_review_prompt_content(self, contract_type: str) -> str:
        """获取合同审查流程提示词内容"""
        return f"""# 合同审查工作流程

## 审查对象
合同类型: {contract_type}

## 审查步骤

### 第一步: 形式审查
1. 检查合同各方的主体资格
2. 确认合同签字盖章是否完整
3. 核对合同文本是否有涂改

### 第二步: 内容审查
1. 使用 `check_contract_risk` 工具进行初步风险扫描
2. 逐条审查主要条款的完整性和合理性
3. 特别关注: 价款、履行期限、违约责任、争议解决

### 第三步: 合规性审查
1. 检查是否违反法律强制性规定
2. 使用 `analyze_legal_clause` 工具分析关键条款
3. 参考 `legal://civil-code/contract` 资源

### 第四步: 风险评估
1. 识别潜在法律风险
2. 使用 `get_legal_suggestion` 获取修改建议
3. 出具风险评估报告

### 第五步: 修改建议
1. 针对发现的问题提出具体修改方案
2. 提供标准条款模板
3. 建议是否需要进一步法律咨询

## 输出格式
请按照以上步骤,生成详细的合同审查报告。
"""

    def get_risk_assessment_prompt_content(self, company_name: str) -> str:
        """获取风险评估提示词内容"""
        return f"""# 企业风险评估报告

## 评估对象
企业名称: {company_name}

## 评估维度

### 1. 主体资格审查
- 企业是否依法设立
- 营业执照是否有效
- 经营范围是否符合

### 2. 信用状况评估
- 是否存在失信记录
- 是否有重大诉讼
- 是否有经营异常

### 3. 合同履约能力
- 注册资本是否充足
- 经营状况是否良好
- 是否有履约保障措施

### 4. 法律风险提示
- 识别潜在法律风险
- 提出风险防范建议
- 建议合同条款设置

## 数据来源
- 国家企业信用信息公示系统
- 中国裁判文书网
- 天眼查等第三方平台 (如已集成)

## 输出要求
请生成一份完整的企业风险评估报告,包含以上所有维度的分析。
"""
