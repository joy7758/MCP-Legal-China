#!/bin/bash

# MCP-Legal-China 开发环境设置脚本
# 用途: 快速配置开发环境和依赖

echo "🚀 开始设置 MCP-Legal-China 开发环境..."

# 检查 Python 版本
echo "📌 检查 Python 版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 版本过低! 需要 Python 3.10+, 当前版本: $python_version"
    exit 1
fi

echo "✅ Python 版本符合要求: $python_version"

# 创建虚拟环境
echo "📦 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
else
    echo "ℹ️  虚拟环境已存在,跳过创建"
fi

# 激活虚拟环境
echo "🔌 激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo "⬆️  升级 pip..."
pip install --upgrade pip

# 安装依赖
echo "📚 安装项目依赖..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt 不存在,手动安装核心依赖..."
    pip install mcp fastmcp requests python-dotenv pandas
fi

# 创建 .env 文件模板
echo "📝 创建环境变量配置文件..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# 天眼查 API 配置
TIANYANCHA_API_KEY=your_api_key_here

# MCP Server 配置
MCP_SERVER_NAME=Legal-CN-Server
MCP_SERVER_VERSION=0.1.0

# 调试模式
DEBUG=true
EOF
    echo "✅ .env 文件创建成功,请编辑并填入你的 API Key"
else
    echo "ℹ️  .env 文件已存在,跳过创建"
fi

# 创建项目目录结构
echo "📁 创建项目目录结构..."
mkdir -p tools
mkdir -p rules
mkdir -p tests
mkdir -p docs

echo "✅ 目录结构创建完成"

# 创建 .gitignore
echo "🔒 创建 .gitignore..."
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# 环境变量
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# 测试
.pytest_cache/
.coverage
htmlcov/

# 日志
*.log

# 临时文件
*.tmp
.DS_Store
EOF
    echo "✅ .gitignore 创建成功"
else
    echo "ℹ️  .gitignore 已存在,跳过创建"
fi

echo ""
echo "🎉 开发环境设置完成!"
echo ""
echo "📋 下一步操作:"
echo "1. 编辑 .env 文件,填入你的天眼查 API Key"
echo "2. 运行 'source venv/bin/activate' 激活虚拟环境"
echo "3. 开始开发!"
echo ""
echo "💡 提示: 使用 'deactivate' 命令退出虚拟环境"
