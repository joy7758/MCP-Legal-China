# 重构计划：分离 MCP Server 与 业务逻辑

## 目标
将 `MCP-Legal-China/server.py` 中的法律业务逻辑提取到独立的模块 `MCP-Legal-China/contract_logic.py` 中，使 `server.py` 专注于 MCP 协议的处理。

## 1. 创建 `MCP-Legal-China/contract_logic.py`

该文件将包含 `ContractLogic` 类，封装所有的法律分析和资源获取逻辑。

**计划迁移的方法：**
*   **工具逻辑 (Tools Logic):**
    *   `check_contract_risk(contract_text, check_types)`: 对应原 `_check_contract_risk`
    *   `analyze_legal_clause(clause_text, clause_type)`: 对应原 `_analyze_legal_clause`
    *   `get_legal_suggestion(risk_type, context)`: 对应原 `_get_legal_suggestion`
*   **资源逻辑 (Resources Logic):**
    *   `get_civil_code_contract()`: 对应原 `_get_civil_code_contract`
    *   `get_contract_checklist()`: 对应原 `_get_contract_checklist`
    *   `get_penalty_rules()`: 对应原 `_get_penalty_rules`
*   **提示词逻辑 (Prompts Logic):**
    *   `get_contract_review_prompt(contract_type)`: 对应原 `_get_contract_review_prompt` 的逻辑部分
    *   `get_risk_assessment_prompt(company_name)`: 对应原 `_get_risk_assessment_prompt` 的逻辑部分

**依赖项：**
*   需要导入 `json`
*   需要导入 `typing` (Dict, List, Any, Optional)

## 2. 重构 `MCP-Legal-China/server.py`

**主要变更：**
*   导入 `ContractLogic` 类：`from contract_logic import ContractLogic`
*   在 `LegalCNServer.__init__` 中初始化 `self.logic = ContractLogic()`
*   **修改工具调用 (`call_tool`):**
    *   调用 `self.logic.check_contract_risk(...)` 等方法，并将返回的字典/字符串包装为 `TextContent`。
*   **修改资源读取 (`read_resource`):**
    *   直接调用 `self.logic.get_civil_code_contract()` 等方法。
*   **修改提示词获取 (`get_prompt`):**
    *   调用 `self.logic.get_contract_review_prompt(...)` 获取内容，然后构建 `GetPromptResult` 对象。

## 3. 文件结构预览

```
MCP-Legal-China/
├── server.py          # MCP 协议层 (Controller)
├── contract_logic.py  # 业务逻辑层 (Service/Logic)
├── config.py          # 配置
└── ...
```

## 4. 执行步骤

1.  **创建 `contract_logic.py`**: 复制相关方法并调整为独立函数或类方法，移除 MCP 特定的类型依赖 (如 `TextContent`, `GetPromptResult`)，只返回纯数据 (dict, str)。
2.  **修改 `server.py`**:
    *   删除已迁移的逻辑代码。
    *   引入 `contract_logic.py`。
    *   对接新的逻辑调用接口，处理返回值格式转换。
3.  **验证**: 运行 `test_server.py` 确保功能未受损。

请确认是否按照此计划执行？
