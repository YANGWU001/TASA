# 🚀 TASA Environment Setup Guide

完整的环境配置指南，用于在新机器上部署TASA系统

---

## 📋 系统要求

### 硬件要求
- **GPU**: NVIDIA GPU with 16GB+ VRAM (推荐 A100/V100/RTX 4090)
- **内存**: 32GB+ RAM
- **存储**: 100GB+ 可用空间

### 软件要求
- **操作系统**: Linux (Ubuntu 20.04+ 或 CentOS 7+)
- **Python**: 3.10 或 3.11
- **CUDA**: 12.1 或 12.4 (与PyTorch版本匹配)
- **cuDNN**: 8.x+

---

## 📦 安装步骤

### 1️⃣ 创建Python虚拟环境

```bash
# 创建虚拟环境
python3.10 -m venv /opt/venv

# 激活虚拟环境
source /opt/venv/bin/activate

# 升级pip
pip install --upgrade pip setuptools wheel
```

### 2️⃣ 安装PyTorch (带CUDA支持)

```bash
# CUDA 12.4版本 (推荐)
pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 --index-url https://download.pytorch.org/whl/cu124

# 或者 CUDA 12.1版本
# pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 --index-url https://download.pytorch.org/whl/cu121
```

验证安装：
```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA Available: {torch.cuda.is_available()}')"
```

### 3️⃣ 安装主要依赖

```bash
# 安装requirements.txt中的所有包
pip install -r requirements.txt
```

### 4️⃣ 安装pykt-toolkit (知识追踪库)

```bash
# 克隆pykt-toolkit仓库
cd /mnt/localssd  # 或者你的项目根目录
git clone https://github.com/pykt-team/pykt-toolkit.git
cd pykt-toolkit

# 安装pykt-toolkit (开发模式)
pip install -e .

# 验证安装
python -c "from pykt.models import LPKT, DKT, AKT, SimpleKT; print('pykt-toolkit installed successfully')"
```

### 5️⃣ 下载BGE模型 (Embeddings & Reranker)

```bash
# 创建模型目录
mkdir -p /mnt/localssd/models

# 下载BGE-M3 (Embeddings)
cd /mnt/localssd/models
git clone https://huggingface.co/BAAI/bge-m3

# 下载BGE-Reranker-v2-M3
git clone https://huggingface.co/BAAI/bge-reranker-v2-m3

# 或者使用Python下载
python << EOF
from FlagEmbedding import BGEM3FlagModel, FlagReranker

# 自动下载到~/.cache/huggingface/
embedding_model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
reranker = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True)
print("Models downloaded successfully")
EOF
```

### 6️⃣ 配置环境变量

创建 `.env` 文件：
```bash
cat > /mnt/localssd/.env << 'EOF'
# API配置
API_KEY=YOUR_API_KEY_HERE

# GPT Proxy (Student/Grader/Rewriter固定使用)
GPT_ENDPOINT=YOUR_ENDPOINT_HERE

# Llama API (可以根据需要更新ngrok链接)
LLAMA_URL=https://2d96013eaaf0.ngrok-free.app/predict/

# Qwen API (可以根据需要更新ngrok链接)
QWEN_URL=https://5d80b2bc05ca.ngrok-free.app/predict/

# 模型路径 (如果需要本地模型)
BGE_M3_PATH=/mnt/localssd/models/bge-m3
BGE_RERANKER_PATH=/mnt/localssd/models/bge-reranker-v2-m3
EOF
```

### 7️⃣ 创建必要的目录结构

```bash
cd /mnt/localssd

# 创建数据和结果目录
mkdir -p bank/{persona,memory,session,dialogue,evaluation_results}
mkdir -p data/{raw,processed}
mkdir -p logs
mkdir -p models

# 验证目录结构
tree -L 2 bank/
```

### 8️⃣ 验证安装

运行验证脚本：
```bash
python << 'EOF'
import sys
print("=" * 80)
print("🔍 环境验证")
print("=" * 80)

# 1. Python版本
print(f"Python: {sys.version.split()[0]}")

# 2. PyTorch和CUDA
try:
    import torch
    print(f"✅ PyTorch: {torch.__version__}")
    print(f"✅ CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"   GPU: {torch.cuda.get_device_name(0)}")
        print(f"   CUDA Version: {torch.version.cuda}")
except Exception as e:
    print(f"❌ PyTorch: {e}")

# 3. Transformers
try:
    import transformers
    print(f"✅ Transformers: {transformers.__version__}")
except Exception as e:
    print(f"❌ Transformers: {e}")

# 4. FlagEmbedding
try:
    from FlagEmbedding import BGEM3FlagModel
    print(f"✅ FlagEmbedding: Available")
except Exception as e:
    print(f"❌ FlagEmbedding: {e}")

# 5. OpenAI
try:
    import openai
    print(f"✅ OpenAI: {openai.__version__}")
except Exception as e:
    print(f"❌ OpenAI: {e}")

# 6. httpx
try:
    import httpx
    print(f"✅ httpx: {httpx.__version__}")
except Exception as e:
    print(f"❌ httpx: {e}")

# 7. pykt-toolkit
try:
    from pykt.models import LPKT, DKT, AKT, SimpleKT
    print(f"✅ pykt-toolkit: Available")
except Exception as e:
    print(f"❌ pykt-toolkit: {e}")

# 8. NumPy & Pandas
try:
    import numpy as np
    import pandas as pd
    print(f"✅ NumPy: {np.__version__}")
    print(f"✅ Pandas: {pd.__version__}")
except Exception as e:
    print(f"❌ NumPy/Pandas: {e}")

print("=" * 80)
print("✅ 环境验证完成！")
print("=" * 80)
EOF
```

---

## 🔧 配置文件说明

### 主要配置文件

1. **tasa_config.py** - GPT Backbone配置
2. **tasa_config_llama.py** - Llama Backbone配置
3. **tasa_config_qwen.py** - Qwen Backbone配置
4. **llm_client_unified.py** - 统一LLM客户端

### 需要修改的配置

在新机器上，需要根据实际情况修改：

1. **API Endpoints**
   - 更新`tasa_config_*.py`中的`ENDPOINT`和`GPT_ENDPOINT`
   - 更新`llm_client_unified.py`中的`LLAMA_URL`和`QWEN_URL`

2. **文件路径**
   - 如果项目不在`/mnt/localssd`，需要更新所有配置文件中的路径
   - 搜索并替换：`/mnt/localssd` → `你的项目路径`

3. **API Keys**
   - 更新`API_KEY`变量

---

## 📊 数据准备

### 学生银行数据

需要准备以下数据文件：

```
bank/
├── persona/           # 学生人设数据
│   ├── [dataset]/
│   │   ├── [student_id].json
│   │   └── embeddings/[student_id]_description.npz
├── memory/            # 学生记忆数据
│   ├── [dataset]/
│   │   ├── [student_id].json
│   │   └── embeddings/[student_id]_description.npz
└── session/           # 学习会话数据
    └── [dataset]/
        └── [student_id]_learning_history.json
```

### 数据集

支持的数据集：
- Assist2017
- NIPS Task 3&4
- Algebra2005
- Bridge2006

---

## 🚀 运行测试

### 1. 测试BGE Embeddings

```bash
python << 'EOF'
from FlagEmbedding import BGEM3FlagModel

model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
texts = ["Hello world", "Test embedding"]
embeddings = model.encode(texts)

print(f"✅ BGE-M3 working")
print(f"   Embedding shape: {embeddings['dense_vecs'].shape}")
EOF
```

### 2. 测试LLM API调用

```bash
# 测试Llama
curl -X POST https://YOUR_LLAMA_NGROK_URL/predict/ \
  -H "Content-Type: application/json" \
  -d '{"system_prompt": "You are a helpful assistant.", "user_prompt": "Hello!"}'

# 测试Qwen
curl -X POST https://YOUR_QWEN_NGROK_URL/predict/ \
  -H "Content-Type: application/json" \
  -d '{"system_prompt": "You are a helpful assistant.", "user_prompt": "Hello!"}'
```

### 3. 运行单个学生评估

```bash
# 测试Vanilla-ICL baseline
python baseline_evaluation_conservative.py \
  --method Vanilla-ICL \
  --dataset assist2017 \
  --students-file qualified_students_assist2017_sampled10.json \
  --max-workers 2 \
  --backbone-suffix=-llama
```

### 4. 运行完整Baseline评估

```bash
# Llama Backbone
nohup python run_all_baselines_llama.py > logs/baseline_llama.log 2>&1 &

# Qwen Backbone
nohup python run_all_baselines_qwen.py > logs/baseline_qwen.log 2>&1 &

# 监控进度
bash check_both_baselines.sh
```

---

## 🐛 常见问题

### Q1: CUDA不可用
```bash
# 检查NVIDIA驱动
nvidia-smi

# 重新安装PyTorch (确保CUDA版本匹配)
pip uninstall torch torchvision torchaudio
pip install torch==2.5.0 --index-url https://download.pytorch.org/whl/cu124
```

### Q2: FlagEmbedding模型下载慢
```bash
# 设置HuggingFace镜像
export HF_ENDPOINT=https://hf-mirror.com
pip install -U huggingface_hub

# 或者手动下载模型后指定本地路径
```

### Q3: pykt-toolkit导入错误
```bash
# 确保在pykt-toolkit目录下安装
cd /path/to/pykt-toolkit
pip install -e .

# 验证PYTHONPATH
echo $PYTHONPATH
```

### Q4: API连接超时
```bash
# 增加httpx timeout
# 在llm_client_unified.py中修改：
# TIMEOUT = 300  # 增加到5分钟
```

### Q5: 内存不足 (OOM)
```bash
# 减少max_workers
# 在baseline脚本中修改：
# MAX_WORKERS = 5  # 从10减少到5

# 或者使用fp16精度
# use_fp16=True (BGE模型)
```

---

## 📚 其他资源

- **PyKT Documentation**: https://pykt-toolkit.readthedocs.io/
- **BGE Models**: https://huggingface.co/BAAI
- **Transformers**: https://huggingface.co/docs/transformers/

---

## 📞 技术支持

如遇到问题，请检查：
1. 日志文件：`logs/`目录
2. GPU状态：`nvidia-smi`
3. 进程状态：`ps aux | grep python`
4. 磁盘空间：`df -h`

---

**最后更新**: 2025-10-22  
**版本**: 1.0

