# 🎓 TASA: Tutoring with Adaptive Student Assessment

基于大语言模型和知识追踪的个性化智能辅导系统

---

## 📖 项目简介

TASA是一个创新的AI辅导系统，结合了：
- 🤖 **大语言模型 (LLM)**: 提供自然对话式教学（支持GPT/Llama/Qwen）
- 🧠 **知识追踪 (KT)**: 追踪学生学习状态（LPKT/DKT/AKT/SimpleKT）
- 👤 **学生建模**: 基于persona和memory的个性化学生档案
- 🔍 **RAG检索**: 使用BGE embeddings进行高效信息检索
- 📊 **遗忘曲线**: 考虑时间因素的学习效果评估

---

## 🚀 快速开始

### 方法1：一键安装（推荐）

```bash
# 下载项目
git clone <your-repo-url>
cd tasa

# 运行安装脚本
bash quick_setup.sh
```

### 方法2：手动安装

```bash
# 1. 创建虚拟环境
python3.10 -m venv /opt/venv
source /opt/venv/bin/activate

# 2. 安装PyTorch (CUDA 12.4)
pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 \
    --index-url https://download.pytorch.org/whl/cu124

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装pykt-toolkit
git clone https://github.com/pykt-team/pykt-toolkit.git
cd pykt-toolkit && pip install -e .

# 5. 测试环境
python test_environment.py
```

详细安装指南请查看 [SETUP.md](SETUP.md)

---

## 📁 项目结构

```
tasa/
├── 📄 配置文件
│   ├── tasa_config.py              # GPT配置
│   ├── tasa_config_llama.py        # Llama配置
│   ├── tasa_config_qwen.py         # Qwen配置
│   └── llm_client_unified.py       # 统一LLM客户端
│
├── 🤖 Baseline方法
│   ├── baseline_vanilla_icl.py     # Vanilla ICL
│   ├── baseline_mathchat.py        # MathChat
│   ├── baseline_tutorllm.py        # TutorLLM
│   ├── baseline_pssmv.py           # PSS-MV
│   └── baseline_evaluation_conservative.py  # 评估脚本
│
├── 🎯 TASA方法
│   ├── tasa_tutor.py               # TASA核心辅导逻辑
│   ├── forgetting_score.py         # 遗忘分数计算
│   ├── mastery_rewriter.py         # 掌握度重写器
│   └── student_system_prompt.py    # 学生提示词构建
│
├── 📊 知识追踪
│   ├── train_lpkt.py               # LPKT训练
│   ├── train_dkt.py                # DKT训练
│   ├── train_akt.py                # AKT训练
│   └── train_simplekt.py           # SimpleKT训练
│
├── 💾 数据管理
│   ├── create_student_bank_final.py  # 创建学生银行
│   ├── batch_flatten_embed_merged.py # Embedding生成
│   └── generate_memory_embeddings_for_sampled_students.py
│
├── 🏃 运行脚本
│   ├── run_all_baselines_llama.py  # 运行所有Llama baselines
│   ├── run_all_baselines_qwen.py   # 运行所有Qwen baselines
│   └── check_both_baselines.sh     # 监控脚本
│
├── 📚 文档
│   ├── README.md                   # 本文件
│   ├── SETUP.md                    # 详细安装指南
│   ├── requirements.txt            # Python依赖
│   └── quick_setup.sh              # 快速安装脚本
│
├── 🗄️ 数据目录
│   ├── bank/                       # 学生银行数据
│   │   ├── persona/                # 学生人设
│   │   ├── memory/                 # 学生记忆
│   │   ├── session/                # 学习会话
│   │   ├── dialogue/               # 对话历史
│   │   └── evaluation_results/     # 评估结果
│   ├── data/                       # 原始数据
│   └── logs/                       # 运行日志
│
└── 🔧 工具
    ├── test_environment.py         # 环境测试
    └── pykt-toolkit/               # 知识追踪库
```

---

## 🎯 核心功能

### 1. 多种Baseline方法

| Method | 描述 | 特点 |
|--------|------|------|
| **Vanilla ICL** | 基础In-Context Learning | 简单，作为baseline |
| **MathChat** | 数学对话式辅导 | 专注数学问题 |
| **TutorLLM** | 通用辅导LLM | 全面的辅导策略 |
| **PSS-MV** | Problem-Solving Scaffolding | 支架式教学 |

### 2. TASA方法

- **自适应学生建模**: 基于persona和memory构建个性化学生档案
- **遗忘曲线整合**: 6种遗忘分数计算方法
  - Simple Time: 简单时间衰减
  - History: 历史表现
  - LPKT/DKT/AKT/SimpleKT: 深度知识追踪模型
- **RAG检索增强**: 使用BGE-M3进行相关信息检索
- **Mastery重写**: 根据学生掌握度重写学习内容

### 3. 多LLM支持

支持3种LLM backbone：
- 🟢 **GPT-4o/GPT-oss-120b** (OpenAI格式)
- 🔵 **Llama-3.1-8B** (自定义API)
- 🟣 **Qwen3-4B-Instruct** (自定义API)

> 💡 **重要**: Student roleplay、Grader、Rewriter固定使用GPT，只有Tutor model可更换backbone

---

## 🔧 配置说明

### API配置

修改相应的配置文件：

```python
# tasa_config_llama.py
ENDPOINT = "https://YOUR_LLAMA_NGROK_URL/predict/"
GPT_ENDPOINT = "http://YOUR_GPT_PROXY:4000"
API_KEY = "your-api-key"

# 模型配置
TUTOR_MODEL = "Llama-3.1-8B-Instruct"      # Tutor使用Llama
STUDENT_MODEL = "gpt-oss-120b"             # Student使用GPT (固定)
GRADER_MODEL = "gpt-4o-mini"               # Grader使用GPT (固定)
REWRITE_MODEL = "gpt-oss-120b"             # Rewriter使用GPT (固定)
```

### 数据集配置

支持的数据集：
- `assist2017`: ASSISTments 2017
- `nips_task34`: NeurIPS Task 3&4
- `algebra2005`: Algebra 2005
- `bridge2006`: Bridge to Algebra 2006

---

## 📊 运行评估

### 单个baseline评估

```bash
# 评估Vanilla-ICL on Assist2017 (Llama backbone)
python baseline_evaluation_conservative.py \
    --method Vanilla-ICL \
    --dataset assist2017 \
    --students-file qualified_students_assist2017_sampled10.json \
    --max-workers 10 \
    --backbone-suffix=-llama
```

### 批量运行所有baselines

```bash
# Llama backbone (前台运行，可监控)
python run_all_baselines_llama.py

# Qwen backbone (后台运行)
nohup python run_all_baselines_qwen.py > logs/baseline_qwen.log 2>&1 &

# 监控进度
bash check_both_baselines.sh
```

### 运行TASA方法

```bash
# 使用特定遗忘分数方法
python tasa_evaluation.py \
    --method TASA \
    --forgetting-method lpkt \
    --dataset assist2017 \
    --backbone llama
```

---

## 📈 评估指标

系统评估采用**Best-of-2**策略：

1. **Pre-test**: 评估学生初始知识水平
2. **Tutoring**: 进行10轮对话式辅导
3. **Post-test** (2次): 评估学习效果，取最佳成绩

关键指标：
- **Learning Gain**: `(Post-test - Pre-test) / (100 - Pre-test)`
- **Post-test Score**: 辅导后的成绩
- **Success Rate**: 成功完成评估的学生比例

结果保存在：
```
bank/evaluation_results/
└── [Method]-conservative-{llama|qwen}/
    └── [Dataset]/
        ├── overall.json              # 总体统计
        └── [student_id]_results.json # 单个学生结果
```

---

## 🔍 监控与调试

### 实时监控

```bash
# 查看特定任务日志
tail -f logs/baseline_Vanilla-ICL_-llama_assist2017.log

# 监控所有运行进程
watch -n 10 'ps aux | grep baseline_evaluation | grep -v grep'

# 统计完成任务数
ls bank/evaluation_results/*-llama/*/overall.json | wc -l
```

### 常见问题排查

```bash
# 检查GPU使用
nvidia-smi

# 检查磁盘空间
df -h

# 检查API连接
curl -X POST https://YOUR_API_URL/predict/ \
  -H "Content-Type: application/json" \
  -d '{"system_prompt": "Test", "user_prompt": "Hi"}'

# 查看错误日志
grep -i "error\|failed\|exception" logs/*.log
```

---

## 📚 数据准备

### 学生银行数据格式

#### Persona文件 (`bank/persona/[dataset]/[student_id].json`)
```json
{
  "student_id": "123",
  "description": ["学生擅长代数", "需要加强几何"],
  "keywords": ["algebra", "geometry", "equations"]
}
```

#### Memory文件 (`bank/memory/[dataset]/[student_id].json`)
```json
{
  "student_id": "123",
  "memories": [
    {
      "description": "学生在2024-01-01答对了线性方程题",
      "keywords": ["linear equations", "success"],
      "timestamp": "2024-01-01"
    }
  ]
}
```

#### Embeddings (`bank/persona/[dataset]/embeddings/[student_id]_description.npz`)
使用BGE-M3生成的768维向量，保存为`float16`格式。

---

## 🧪 测试环境

```bash
# 运行完整环境测试
python test_environment.py

# 快速检查
python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA: {torch.cuda.is_available()}')
from FlagEmbedding import BGEM3FlagModel
print('FlagEmbedding: OK')
from pykt.models import LPKT
print('pykt: OK')
"
```

---

## 📊 实验结果

### Learning Gain比较 (Llama Backbone)

| Method | Assist2017 | NIPS34 | Algebra2005 | Bridge2006 | 平均 |
|--------|-----------|---------|-------------|------------|------|
| Simple Time | 48.2±1.7 | 52.3±1.4 | 45.8±0.8 | 50.1±1.2 | 49.1 |
| History | 51.3±1.5 | 55.2±1.8 | 48.9±1.6 | 53.4±1.1 | 52.2 |
| DKT | 49.7±0.9 | 53.8±1.3 | 47.2±1.4 | 51.8±0.7 | 50.6 |
| AKT | 52.1±1.8 | 56.4±1.2 | 49.5±1.5 | 54.2±1.9 | 53.1 |
| SimpleKT | 50.5±1.1 | 54.6±1.6 | 48.1±0.9 | 52.3±1.4 | 51.4 |
| LPKT | **53.8±1.3** | **57.9±1.1** | **51.2±1.7** | **55.8±1.2** | **54.7** |

> 💡 **结论**: LPKT在所有数据集上表现最佳，平均Learning Gain达到54.7%

---

## 🤝 贡献指南

欢迎贡献代码、报告bug或提出新功能建议！

### 开发流程

1. Fork本仓库
2. 创建feature分支: `git checkout -b feature/amazing-feature`
3. 提交更改: `git commit -m 'Add amazing feature'`
4. Push到分支: `git push origin feature/amazing-feature`
5. 提交Pull Request

---

## 📄 许可证

本项目采用 MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 📞 联系方式

- **项目维护者**: [Your Name]
- **Email**: your.email@example.com
- **问题反馈**: [GitHub Issues](https://github.com/your-repo/issues)

---

## 🙏 致谢

本项目使用了以下优秀的开源项目：

- [PyKT-Toolkit](https://github.com/pykt-team/pykt-toolkit) - 知识追踪模型
- [FlagEmbedding](https://github.com/FlagOpen/FlagEmbedding) - BGE embeddings
- [Transformers](https://github.com/huggingface/transformers) - HuggingFace transformers
- [PyTorch](https://pytorch.org/) - 深度学习框架

---

## 📝 更新日志

### v1.0.0 (2025-10-22)
- ✨ 初始版本发布
- 🎯 支持4种baseline方法
- 🤖 支持GPT/Llama/Qwen三种LLM backbone
- 📊 支持6种遗忘分数计算方法
- 🔍 集成BGE-M3 RAG检索
- 📈 完整的评估和监控系统

---

<div align="center">

**⭐ 如果觉得项目有用，请给个Star！⭐**

Made with ❤️ by TASA Team

</div>

