# 🤝 MCP-Legal-China 贡献者指南 (Contributing Guide)

欢迎！如果你正在阅读这份文档，说明你已经意识到了 2026 AI 法律元年的重要性。我们不只是在写插件，而是在定义中国 AI 法律代理人的行业标准。

为了保持项目的专业性与严谨性，请遵循以下流程加入我们。

---

## 🏗️ 我们的愿景
**“让 Claude 像中国大律师一样思考。”**
我们需要将《民法典》、司法解释及行业合规经验，转化为 AI 可调用的 MCP (Model Context Protocol) 资源。

---

## 🚀 第一步：申领你的“创始席位”

我们不需要漫无目的的代码，我们需要解决实际问题的开发者。

1. **查看 Issues：** 前往项目的 [Issues](https://github.com/joy7758/MCP-Legal-China/issues) 页面。
2. **认领任务：** 寻找标记为 `help wanted` 或 `good first issue` 的任务。
3. **留言占座：** 在该 Issue 下留言：“I would like to work on this.”（我会负责这个任务）。

---

## 🛠️ 贡献领域

### 1. 法律逻辑专家 (Legal Logic)
- **任务：** 将法律条文拆解为 IF-THEN 的逻辑树。
- **产出：** `/rules` 文件夹下的 JSON 或 Markdown 合规模版。

### 2. 协议架构师 (MCP Architect)
- **任务：** 完善 `server.py`，实现更复杂的 MCP 工具调用（Tools）和资源（Resources）。
- **产出：** 符合 MCP 协议规范的 Python 代码。

### 3. 数据对接官 (Data Integration)
- **任务：** 开发对接天眼查、企查查、裁判文书网的 API 适配器。

---

## 📝 提交规范 (PR Workflow)

1. **Fork** 本项目到你的账号。
2. **Create** 你的特性分支 (`git checkout -b feat/YourName-Feature`)。
3. **Commit** 你的更改，并附带清晰的说明。
4. **Push** 到你的分支。
5. **Open a Pull Request (PR)**。

**注意：** 一旦你的 PR 被 Merge（合并），请提醒 Founder (@joy7758) 将你的 ID 加入到 `CONTRIBUTORS.md` 的核心贡献者名单中。

---

## ⚖️ 行为准则
- **严谨：** 法律项目容不得半点逻辑错误。
- **开源：** 本项目遵循 MIT 开源协议，你的贡献将造福整个中文 AI 社区。

---
**现在就去 Issue 区看看有什么你可以做的吧！让我们一起定义未来。**
