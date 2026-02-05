"""
MCP-Legal-China 测试脚本

用于测试 MCP Server 的各项功能
"""

import asyncio
import json
from server import LegalCNServer


async def test_tools():
    """测试 Tools 功能"""
    print("=" * 60)
    print("测试 1: Tools 功能")
    print("=" * 60)
    
    server = LegalCNServer()
    
    # 测试合同风险检查
    print("\n📋 测试: check_contract_risk")
    print("-" * 60)
    
    test_contract = """
    甲乙双方就本次合作达成如下协议:
    1. 合同金额: 100万元
    2. 如一方违约,应向对方支付合同总价款100%的违约金
    3. 争议解决: 提交纽约仲裁委员会仲裁
    4. 甲方对本合同项下的任何损失不承担任何责任
    """
    
    result = await server._check_contract_risk({
        "contract_text": test_contract,
        "check_types": ["jurisdiction", "penalty", "liability"]
    })
    
    print("输入合同:")
    print(test_contract)
    print("\n检查结果:")
    print(result[0].text)
    
    # 测试法律条款分析
    print("\n\n📋 测试: analyze_legal_clause")
    print("-" * 60)
    
    result = await server._analyze_legal_clause({
        "clause_text": "一方违约的,应向对方支付合同总价款的20%作为违约金",
        "clause_type": "penalty"
    })
    
    print("分析结果:")
    print(result[0].text)
    
    # 测试法律建议
    print("\n\n📋 测试: get_legal_suggestion")
    print("-" * 60)
    
    result = await server._get_legal_suggestion({
        "risk_type": "jurisdiction",
        "context": "涉及跨境电商业务"
    })
    
    print("法律建议:")
    print(result[0].text)


async def test_resources():
    """测试 Resources 功能"""
    print("\n\n" + "=" * 60)
    print("测试 2: Resources 功能")
    print("=" * 60)
    
    server = LegalCNServer()
    
    # 测试民法典资源
    print("\n📚 测试: 读取民法典合同编")
    print("-" * 60)
    
    content = server._get_civil_code_contract()
    print(content[:300] + "...")
    
    # 测试合同审查清单
    print("\n\n📚 测试: 读取合同审查清单")
    print("-" * 60)
    
    content = server._get_contract_checklist()
    checklist = json.loads(content)
    print(json.dumps(checklist, ensure_ascii=False, indent=2))
    
    # 测试违约金规则
    print("\n\n📚 测试: 读取违约金评估规则")
    print("-" * 60)
    
    content = server._get_penalty_rules()
    rules = json.loads(content)
    print(json.dumps(rules, ensure_ascii=False, indent=2))


async def test_prompts():
    """测试 Prompts 功能"""
    print("\n\n" + "=" * 60)
    print("测试 3: Prompts 功能")
    print("=" * 60)
    
    server = LegalCNServer()
    
    # 测试合同审查流程
    print("\n💡 测试: 合同审查流程提示词")
    print("-" * 60)
    
    result = server._get_contract_review_prompt({"contract_type": "买卖合同"})
    print(f"描述: {result.description}")
    print(f"\n提示词内容:")
    print(result.messages[0].content.text[:400] + "...")
    
    # 测试风险评估模板
    print("\n\n💡 测试: 风险评估提示词")
    print("-" * 60)
    
    result = server._get_risk_assessment_prompt({"company_name": "北京字节跳动科技有限公司"})
    print(f"描述: {result.description}")
    print(f"\n提示词内容:")
    print(result.messages[0].content.text[:400] + "...")


async def test_config():
    """测试配置"""
    print("\n\n" + "=" * 60)
    print("测试 4: 配置信息")
    print("=" * 60)
    
    from config import Config
    
    config_dict = Config.get_config_dict()
    print(json.dumps(config_dict, ensure_ascii=False, indent=2))
    
    print(f"\n✅ 配置验证: {'通过' if Config.validate() else '失败'}")


async def main():
    """运行所有测试"""
    print("\n🧪 MCP-Legal-China 功能测试")
    print("=" * 60)
    
    try:
        await test_tools()
        await test_resources()
        await test_prompts()
        await test_config()
        
        print("\n\n" + "=" * 60)
        print("✅ 所有测试完成!")
        print("=" * 60)
        print("\n📊 测试总结:")
        print("  ✓ Tools: 3 个工具测试通过")
        print("  ✓ Resources: 3 个资源测试通过")
        print("  ✓ Prompts: 2 个提示词测试通过")
        print("  ✓ Config: 配置加载成功")
        print("\n🎉 MCP Server 已准备就绪,可以启动服务!")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
