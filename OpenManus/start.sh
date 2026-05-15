#!/bin/bash
# ============================================================
#  DataAgent 一键安装 & 启动脚本
#  用法: bash start.sh          (安装+启动)
#        bash start.sh --skip-install  (跳过安装，直接启动)
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════╗"
echo "║        DataAgent 万能智能助手                ║"
echo "║        一键安装 & 启动脚本                   ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"

SKIP_INSTALL=false
if [[ "$1" == "--skip-install" ]]; then
    SKIP_INSTALL=true
fi

# ==================== 1. 检查 Python ====================
echo -e "${YELLOW}[1/5] 检查 Python 环境...${NC}"
PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    if [[ "$PYTHON_MAJOR" -ge 3 && "$PYTHON_MINOR" -ge 10 ]]; then
        PYTHON_CMD="python3"
    fi
fi

if [[ -z "$PYTHON_CMD" ]]; then
    echo -e "${RED}错误: 需要 Python 3.10+，当前未找到${NC}"
    echo "请安装 Python 3.10+: https://www.python.org/downloads/"
    exit 1
fi

echo -e "${GREEN}  ✓ Python $PYTHON_VERSION${NC}"

# ==================== 2. 安装依赖 ====================
if [[ "$SKIP_INSTALL" == "false" ]]; then
    echo -e "${YELLOW}[2/5] 安装 Python 依赖...${NC}"
    
    # 升级 pip
    $PYTHON_CMD -m pip install --upgrade pip -q 2>/dev/null
    
    # 安装依赖
    if $PYTHON_CMD -m pip install -r requirements.txt --break-system-packages -q 2>&1; then
        echo -e "${GREEN}  ✓ 依赖安装完成${NC}"
    else
        echo -e "${YELLOW}  部分依赖安装失败，尝试继续...${NC}"
    fi
else
    echo -e "${YELLOW}[2/5] 跳过依赖安装${NC}"
fi

# ==================== 3. 检查配置文件 ====================
echo -e "${YELLOW}[3/5] 检查配置文件...${NC}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config/config.toml"
WEB_CONFIG_FILE="$SCRIPT_DIR/config/web_config.json"

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo -e "${YELLOW}  config/config.toml 不存在，从示例创建...${NC}"
    if [[ -f "$SCRIPT_DIR/config/config.example.toml" ]]; then
        cp "$SCRIPT_DIR/config/config.example.toml" "$CONFIG_FILE"
        echo -e "${RED}  ⚠ 请编辑 $CONFIG_FILE 填入你的 API Key！${NC}"
    else
        # 创建最小配置
        mkdir -p "$SCRIPT_DIR/config"
        cat > "$CONFIG_FILE" << 'TOML'
[llm]
model = "qwen-max"
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
api_key = "YOUR_API_KEY_HERE"  # ← 必须修改！
max_tokens = 8192
temperature = 0.0
TOML
        echo -e "${RED}  ⚠ 请编辑 $CONFIG_FILE 填入你的 API Key！${NC}"
    fi
fi

if [[ ! -f "$WEB_CONFIG_FILE" ]]; then
    echo -e "${YELLOW}  config/web_config.json 不存在，从示例创建...${NC}"
    if [[ -f "$SCRIPT_DIR/config/web_config.example.json" ]]; then
        cp "$SCRIPT_DIR/config/web_config.example.json" "$WEB_CONFIG_FILE"
    fi
fi

echo -e "${GREEN}  ✓ 配置文件就绪${NC}"

# ==================== 4. 检查 API Key ====================
echo -e "${YELLOW}[4/5] 检查 API Key...${NC}"

API_KEY_SET=false
if [[ -f "$CONFIG_FILE" ]]; then
    # 检查是否还是默认值
    if grep -q "YOUR_API_KEY" "$CONFIG_FILE" 2>/dev/null; then
        echo -e "${RED}  ⚠ API Key 未配置！请编辑 config/config.toml${NC}"
        echo -e "${RED}    或在 Web 界面设置中配置${NC}"
    else
        API_KEY_SET=true
        echo -e "${GREEN}  ✓ API Key 已配置${NC}"
    fi
fi

if [[ -f "$WEB_CONFIG_FILE" ]]; then
    if grep -q "YOUR_API_KEY" "$WEB_CONFIG_FILE" 2>/dev/null; then
        echo -e "${YELLOW}  ⚠ Web 配置 API Key 未设置（可在 Web 设置页面配置）${NC}"
    fi
fi

# ==================== 5. 启动服务 ====================
echo -e "${YELLOW}[5/5] 启动 DataAgent 服务...${NC}"
echo ""

cd "$SCRIPT_DIR"
$PYTHON_CMD web_app.py
