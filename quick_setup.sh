#!/bin/bash
# ============================================================================
# TASA 快速安装脚本
# ============================================================================
# 使用方法: bash quick_setup.sh
# ============================================================================

set -e  # 遇到错误立即退出

echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                   🚀 TASA Environment Quick Setup                             ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📂 项目路径: $PROJECT_ROOT"
echo ""

# ============================================================================
# 1. 检查Python版本
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  检查Python版本..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PYTHON_CMD=""
for cmd in python3.11 python3.10 python3; do
    if command -v $cmd &> /dev/null; then
        version=$($cmd -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        if [[ "$version" == "3.10" ]] || [[ "$version" == "3.11" ]]; then
            PYTHON_CMD=$cmd
            echo -e "${GREEN}✅ 找到Python $version: $cmd${NC}"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo -e "${RED}❌ 未找到Python 3.10或3.11，请先安装${NC}"
    exit 1
fi
echo ""

# ============================================================================
# 2. 创建虚拟环境
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  创建虚拟环境..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

VENV_PATH="/opt/venv"
if [ -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}⚠️  虚拟环境已存在: $VENV_PATH${NC}"
    read -p "是否重新创建? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf $VENV_PATH
        $PYTHON_CMD -m venv $VENV_PATH
        echo -e "${GREEN}✅ 虚拟环境已重新创建${NC}"
    else
        echo -e "${YELLOW}⏭️  跳过虚拟环境创建${NC}"
    fi
else
    $PYTHON_CMD -m venv $VENV_PATH
    echo -e "${GREEN}✅ 虚拟环境已创建: $VENV_PATH${NC}"
fi

# 激活虚拟环境
source $VENV_PATH/bin/activate
echo -e "${GREEN}✅ 虚拟环境已激活${NC}"
echo ""

# 升级pip
echo "📦 升级pip..."
pip install --upgrade pip setuptools wheel -q
echo ""

# ============================================================================
# 3. 检查CUDA
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  检查CUDA..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v nvidia-smi &> /dev/null; then
    CUDA_VERSION=$(nvidia-smi | grep -oP "CUDA Version: \K[0-9.]+")
    echo -e "${GREEN}✅ CUDA Version: $CUDA_VERSION${NC}"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    
    # 根据CUDA版本选择PyTorch
    if [[ "$CUDA_VERSION" == 12.4* ]]; then
        TORCH_INDEX="cu124"
    elif [[ "$CUDA_VERSION" == 12.1* ]]; then
        TORCH_INDEX="cu121"
    else
        TORCH_INDEX="cu121"  # 默认
    fi
else
    echo -e "${YELLOW}⚠️  未检测到CUDA，将安装CPU版本PyTorch${NC}"
    TORCH_INDEX="cpu"
fi
echo ""

# ============================================================================
# 4. 安装PyTorch
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  安装PyTorch (可能需要几分钟)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if python -c "import torch" 2>/dev/null; then
    TORCH_VERSION=$(python -c "import torch; print(torch.__version__)")
    echo -e "${YELLOW}⚠️  PyTorch已安装: $TORCH_VERSION${NC}"
    read -p "是否重新安装? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}⏭️  跳过PyTorch安装${NC}"
        echo ""
    else
        pip uninstall -y torch torchvision torchaudio
        pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 \
            --index-url https://download.pytorch.org/whl/${TORCH_INDEX}
        echo -e "${GREEN}✅ PyTorch已重新安装${NC}"
        echo ""
    fi
else
    echo "📦 安装PyTorch for CUDA $TORCH_INDEX..."
    pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 \
        --index-url https://download.pytorch.org/whl/${TORCH_INDEX}
    echo -e "${GREEN}✅ PyTorch已安装${NC}"
    echo ""
fi

# 验证PyTorch
python << 'PYEOF'
import torch
print(f"PyTorch版本: {torch.__version__}")
print(f"CUDA可用: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
PYEOF
echo ""

# ============================================================================
# 5. 安装requirements.txt
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  安装依赖包 (可能需要5-10分钟)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    pip install -r "$PROJECT_ROOT/requirements.txt"
    echo -e "${GREEN}✅ 依赖包已安装${NC}"
else
    echo -e "${RED}❌ 未找到requirements.txt${NC}"
    exit 1
fi
echo ""

# ============================================================================
# 6. 安装pykt-toolkit
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  安装pykt-toolkit (知识追踪库)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PYKT_PATH="$PROJECT_ROOT/pykt-toolkit"
if [ -d "$PYKT_PATH" ]; then
    echo -e "${YELLOW}⚠️  pykt-toolkit目录已存在${NC}"
    cd $PYKT_PATH
    pip install -e .
    echo -e "${GREEN}✅ pykt-toolkit已安装${NC}"
else
    echo "📥 克隆pykt-toolkit仓库..."
    cd $PROJECT_ROOT
    git clone https://github.com/pykt-team/pykt-toolkit.git
    cd pykt-toolkit
    pip install -e .
    echo -e "${GREEN}✅ pykt-toolkit已克隆并安装${NC}"
fi

# 验证pykt
python << 'PYEOF'
try:
    from pykt.models import LPKT, DKT, AKT, SimpleKT
    print("✅ pykt-toolkit验证成功")
except Exception as e:
    print(f"❌ pykt-toolkit验证失败: {e}")
PYEOF
echo ""

# ============================================================================
# 7. 创建目录结构
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7️⃣  创建目录结构..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd $PROJECT_ROOT

# 创建必要的目录
mkdir -p bank/{persona,memory,session,dialogue,evaluation_results}
mkdir -p data/{raw,processed}
mkdir -p logs
mkdir -p models

echo -e "${GREEN}✅ 目录结构已创建${NC}"
tree -L 2 bank/ 2>/dev/null || ls -la bank/
echo ""

# ============================================================================
# 8. 下载BGE模型 (可选)
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "8️⃣  下载BGE模型 (可选)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

read -p "是否现在下载BGE模型? (需要约10GB空间) (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📥 下载BGE-M3和Reranker模型 (可能需要10-20分钟)..."
    python << 'PYEOF'
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'  # 使用镜像加速

from FlagEmbedding import BGEM3FlagModel, FlagReranker

print("📥 下载BGE-M3...")
embedding_model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
print("✅ BGE-M3下载完成")

print("📥 下载BGE-Reranker-v2-M3...")
reranker = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True)
print("✅ Reranker下载完成")
PYEOF
    echo -e "${GREEN}✅ BGE模型已下载${NC}"
else
    echo -e "${YELLOW}⏭️  跳过BGE模型下载 (首次运行时会自动下载)${NC}"
fi
echo ""

# ============================================================================
# 9. 创建环境变量文件
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "9️⃣  配置环境变量..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -f "$PROJECT_ROOT/.env" ]; then
    cat > "$PROJECT_ROOT/.env" << 'ENVEOF'
# TASA Environment Variables
# 请根据实际情况修改以下配置

# API Keys
API_KEY=sk-g-wO3D7N2V-VvcfhfqG9ww

# GPT Proxy (Student/Grader/Rewriter)
GPT_ENDPOINT=http://pluto-prod-hawang-llm-proxy-9qtfav-0:4000

# Llama API
LLAMA_URL=https://YOUR_LLAMA_NGROK_URL/predict/

# Qwen API
QWEN_URL=https://YOUR_QWEN_NGROK_URL/predict/

# HuggingFace镜像 (可选，加速模型下载)
HF_ENDPOINT=https://hf-mirror.com
ENVEOF
    echo -e "${GREEN}✅ 已创建.env文件，请修改其中的API配置${NC}"
else
    echo -e "${YELLOW}⚠️  .env文件已存在，跳过创建${NC}"
fi
echo ""

# ============================================================================
# 10. 验证安装
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔟 验证安装..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python << 'PYEOF'
import sys
print("=" * 80)
print("🔍 环境验证")
print("=" * 80)

checks = []

# Python
print(f"Python: {sys.version.split()[0]}")
checks.append(("Python", True))

# PyTorch
try:
    import torch
    print(f"✅ PyTorch: {torch.__version__}")
    print(f"   CUDA: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"   GPU: {torch.cuda.get_device_name(0)}")
    checks.append(("PyTorch", True))
except Exception as e:
    print(f"❌ PyTorch: {e}")
    checks.append(("PyTorch", False))

# Transformers
try:
    import transformers
    print(f"✅ Transformers: {transformers.__version__}")
    checks.append(("Transformers", True))
except Exception as e:
    print(f"❌ Transformers: {e}")
    checks.append(("Transformers", False))

# FlagEmbedding
try:
    from FlagEmbedding import BGEM3FlagModel
    print(f"✅ FlagEmbedding: Available")
    checks.append(("FlagEmbedding", True))
except Exception as e:
    print(f"❌ FlagEmbedding: {e}")
    checks.append(("FlagEmbedding", False))

# OpenAI
try:
    import openai
    print(f"✅ OpenAI: {openai.__version__}")
    checks.append(("OpenAI", True))
except Exception as e:
    print(f"❌ OpenAI: {e}")
    checks.append(("OpenAI", False))

# httpx
try:
    import httpx
    print(f"✅ httpx: {httpx.__version__}")
    checks.append(("httpx", True))
except Exception as e:
    print(f"❌ httpx: {e}")
    checks.append(("httpx", False))

# pykt
try:
    from pykt.models import LPKT
    print(f"✅ pykt-toolkit: Available")
    checks.append(("pykt", True))
except Exception as e:
    print(f"❌ pykt-toolkit: {e}")
    checks.append(("pykt", False))

# NumPy & Pandas
try:
    import numpy as np
    import pandas as pd
    print(f"✅ NumPy: {np.__version__}")
    print(f"✅ Pandas: {pd.__version__}")
    checks.append(("NumPy/Pandas", True))
except Exception as e:
    print(f"❌ NumPy/Pandas: {e}")
    checks.append(("NumPy/Pandas", False))

print("=" * 80)

# 汇总
passed = sum(1 for _, status in checks if status)
total = len(checks)
if passed == total:
    print(f"✅ 所有检查通过 ({passed}/{total})")
else:
    print(f"⚠️  部分检查失败 ({passed}/{total})")
    
print("=" * 80)
PYEOF

echo ""

# ============================================================================
# 完成
# ============================================================================
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                        ✅ 安装完成！                                          ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📝 后续步骤:"
echo ""
echo "1️⃣  激活虚拟环境:"
echo "   source /opt/venv/bin/activate"
echo ""
echo "2️⃣  修改配置文件 (根据你的API endpoints):"
echo "   vim $PROJECT_ROOT/.env"
echo "   vim $PROJECT_ROOT/tasa_config_llama.py"
echo "   vim $PROJECT_ROOT/tasa_config_qwen.py"
echo ""
echo "3️⃣  准备数据:"
echo "   将学生银行数据复制到 $PROJECT_ROOT/bank/"
echo ""
echo "4️⃣  运行测试:"
echo "   python baseline_evaluation_conservative.py --help"
echo ""
echo "5️⃣  运行完整评估:"
echo "   bash run_all_baselines_llama.py"
echo "   bash run_all_baselines_qwen.py"
echo ""
echo "📚 详细文档: $PROJECT_ROOT/SETUP.md"
echo ""
echo "🎉 祝你使用愉快！"
echo ""

