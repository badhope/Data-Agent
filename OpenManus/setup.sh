#!/bin/bash
# Data-Agent 一键安装脚本

set -e

echo "🚀 Data-Agent 安装脚本"
echo "======================"

# 检查 Python 版本
echo "📋 检查 Python 版本..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python 版本: $PYTHON_VERSION"

# 检查 Python 版本是否 >= 3.10
REQUIRED_VERSION="3.10"
CURRENT_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$CURRENT_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 版本过低，需要 3.10+，当前 $CURRENT_VERSION"
    exit 1
fi
echo "✅ Python 版本符合要求"

# 安装依赖
echo ""
echo "📦 安装依赖..."
pip install -r requirements.txt --quiet
echo "✅ 依赖安装完成"

# 复制配置文件
echo ""
echo "⚙️  配置检查..."
if [ ! -f "config/config.toml" ]; then
    cp config/config.example.toml config/config.toml
    echo "✅ 配置文件已创建 (config/config.toml)"
else
    echo "✅ 配置文件已存在"
fi

# 检查 API Key
echo ""
echo "🔑 检查 API Key..."
API_KEY=$(grep -E '^api_key\s*=' config/config.toml | head -1 | sed 's/.*=\s*"\(.*\)".*/\1/')
if [ "$API_KEY" = "YOUR_API_KEY" ] || [ -z "$API_KEY" ]; then
    echo "⚠️  请编辑 config/config.toml 填入你的 API Key"
    echo "   支持: OpenAI, Anthropic, Google, Ollama 等"
else
    echo "✅ API Key 已设置"
fi

# 可选：安装浏览器依赖
echo ""
echo "🌐 浏览器自动化（可选）"
read -p "是否安装浏览器依赖用于网页自动化? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 安装 Playwright..."
    pip install playwright --quiet
    playwright install chromium
    echo "✅ 浏览器依赖安装完成"
else
    echo "⏭️  跳过浏览器依赖安装"
fi

echo ""
echo "======================"
echo "✅ 安装完成！"
echo ""
echo "📝 启动命令:"
echo "   python web_app.py          # Web 模式"
echo "   python main.py             # CLI 模式"
echo ""
echo "🔧 配置文件: config/config.toml"
echo ""
echo "🌐 访问地址: http://localhost:8000"
echo "======================"
