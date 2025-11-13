# Student Persona and Memory Bank 创建指南

## 📋 概述

创建一个包含学生Persona和Memory的数据库，用于知识追踪和个性化学习分析。

## 🗂️ 文件夹结构

```
/mnt/localssd/bank/
├── persona/
│   ├── assist2017/
│   │   ├── data/           # Persona数据(JSON)
│   │   ├── embeddings/     # BGE-M3 embeddings
│   │   └── last_interactions/  # 最后一次答题记录
│   ├── nips_task34/
│   ├── algebra2005/
│   └── bridge2006/
└── memory/
    ├── assist2017/
    │   ├── data/           # Memory数据(JSON)
    │   └── embeddings/     # BGE-M3 embeddings
    ├── nips_task34/
    ├── algebra2005/
    └── bridge2006/
```

## 📊 四个数据集

1. **ASSISTments2017** - 1,708学生, 102个skills，有skill名称
2. **NIPS Task 3&4** - 4,918学生, 57个concepts，层级结构
3. **Algebra2005** - 460学生, 112个concepts
4. **Bridge2Algebra2006** - 916学生, 488个concepts

## 🎯 Persona vs Memory

### Persona（长期掌握程度）
- **定义**: 学生对每个concept的长期掌握程度总结
- **粒度**: 每个concept一条记录
- **内容**: 基于历史答题的掌握程度摘要
- **格式**:
  ```json
  {
    "concept_id": 5,
    "concept_text": "Linear Equations",
    "description": "The student demonstrates excellent mastery of Linear Equations with an 85% accuracy rate over 20 attempts. Performance is consistent and shows strong understanding.",
    "keywords": "Linear Equations",
    "description_embedding": [0.123, -0.456, ...],  // 1024维向量
    "keywords_embedding": [0.789, -0.234, ...]
  }
  ```

### Memory（事件记录）
- **定义**: 每个具体答题事件的描述
- **粒度**: 每个答题一条记录
- **内容**: 具体事件描述（如"做对了xxx题"）
- **格式**:
  ```json
  {
    "concept_id": 5,
    "concept_text": "Linear Equations",
    "description": "Student correctly solved a Linear Equations problem on their third attempt.",
    "keywords": "Linear Equations",
    "description_embedding": [0.321, -0.654, ...],
    "keywords_embedding": [0.987, -0.432, ...]
  }
  ```

## 🔑 关键特性

### 1. 排除最后一次答题
- **Persona和Memory**: 不包含每个concept的最后一次答题
- **Last Interactions**: 单独保存最后一次答题，用于forgetting score计算

### 2. LLM生成描述
- **模型**: GPT-4o
- **System Prompt**: 教育数据分析专家
- **输出格式**: JSON

### 3. BGE-M3 Embeddings
- **模型**: BAAI/bge-m3
- **维度**: 1024
- **编码内容**: description和keywords分别编码

### 4. 并行处理
- **进程数**: 10个（可配置）
- **每个进程**: 处理一个学生

## 📝 Prompt设计

### Persona Prompt

**System Prompt**:
```
You are an educational data analyst. Your task is to summarize a student's long-term mastery level for each concept they have practiced, based on their historical performance data.

For each concept, analyze the student's answer history and create a concise summary that describes:
1. Their overall mastery level (e.g., "excellent mastery", "good understanding", "struggling", "needs improvement")
2. Their accuracy rate
3. Any notable patterns (e.g., "consistent performance", "improving over time", "declining performance")

Keep each summary to 2-3 sentences, focused and informative.
```

**User Prompt示例**:
```
Student ID: 12345
Dataset: assist2017

Below is the student's performance on each concept (excluding the most recent attempt on each concept):

Concept: Linear Equations
- Total attempts: 20
- Correct answers: 17
- Accuracy: 85.0%

Concept: Quadratic Equations
- Total attempts: 15
- Correct answers: 10
- Accuracy: 66.7%

...

Please provide a JSON response with the following format:
{
  "personas": [
    {
      "concept_id": <concept_id>,
      "concept_text": "<concept_text>",
      "description": "<2-3 sentence summary of mastery level>",
      "keywords": "<concept_text as keywords>"
    },
    ...
  ]
}
```

### Memory Prompt

**System Prompt**:
```
You are an educational data analyst. Your task is to create event-based memory records for a student's learning activities.

For each question-answering event, create a concise description that includes:
1. What concept was being practiced
2. Whether the answer was correct or incorrect
3. The context (e.g., "attempted", "successfully solved", "struggled with")

Each memory should be a single sentence describing a specific event.
```

**User Prompt示例**:
```
Student ID: 12345
Dataset: assist2017

Below is the student's question-answering history (excluding the most recent attempt on each concept):

1. Attempted Linear Equations, answered correctly
2. Attempted Quadratic Equations, answered incorrectly
3. Attempted Linear Equations, answered correctly
...

Please provide a JSON response with the following format:
{
  "memories": [
    {
      "concept_id": <concept_id>,
      "concept_text": "<concept_text>",
      "description": "<one sentence describing this specific event>",
      "keywords": "<concept_text as keywords>"
    },
    ...
  ]
}
```

## 🚀 使用方法

### 1. 测试模式（5个学生）
```bash
cd /mnt/localssd
source activate pykt
python create_student_bank.py
```

### 2. 完整运行（所有学生）
修改`create_student_bank.py`中的`TEST_MODE = False`，然后运行：
```bash
nohup python -u create_student_bank.py > bank_creation.log 2>&1 &
```

### 3. 监控进度
```bash
tail -f bank_creation.log
```

## 📊 输出文件

### Persona数据
```
/mnt/localssd/bank/persona/{dataset}/data/personas.json
```

### Memory数据
```
/mnt/localssd/bank/memory/{dataset}/data/memories.json
```

### 最后一次交互
```
/mnt/localssd/bank/persona/{dataset}/last_interactions/last_interactions.json
```

## ⚠️ 注意事项

1. **API限流**: GPT-4o有rate limit，大规模运行时注意重试机制
2. **内存使用**: BGE-M3模型需要~4GB GPU内存
3. **数据一致性**: 确保所有数据集已预处理完成
4. **Concept文本**: 
   - ASSISTments2017: 有完整skill名称
   - NIPS Task 3&4: 有层级subject名称
   - EdNet/Algebra/Bridge: 只有数字ID，使用"Concept X"格式

## 🔧 配置参数

```python
# LLM配置
ENDPOINT = "http://pluto-prod-hawang-llm-proxy-9qtfav-0:4000"
KEY = "sk-g-wO3D7N2V-VvcfhfqG9ww"
MODEL = "gpt-4o"

# 并行进程数
MAX_WORKERS = 10

# BGE-M3模型
BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
```

## 📈 预计运行时间

- **测试模式** (5学生/数据集): ~10-20分钟
- **完整运行** (所有学生):
  - ASSISTments2017: ~8-10小时
  - NIPS Task 3&4: ~10-15小时  
  - Algebra2005: ~2-3小时
  - Bridge2Algebra2006: ~4-6小时

## 🎯 后续使用

### 1. 检索相似Persona
```python
from FlagEmbedding import BGEM3FlagModel
import numpy as np

model = BGEM3FlagModel('BAAI/bge-m3')
query = "student struggling with linear equations"
query_emb = model.encode([query])['dense_vecs'][0]

# 计算相似度
similarities = np.dot(persona_embeddings, query_emb)
```

### 2. Forgetting Score计算
```python
# 使用last_interactions
with open('bank/persona/assist2017/last_interactions/last_interactions.json') as f:
    last_interactions = json.load(f)

# 结合模型预测
predicted_prob = model.predict(last_interaction)
forgetting_score = (1 - predicted_prob) * (delta_t / (delta_t + tau))
```

---

**创建时间**: 2025-10-19  
**状态**: 准备就绪，等待运行

