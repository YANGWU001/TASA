# Student Persona & Memory Bank - 完整指南

> 为4个数据集创建学生Persona和Memory数据库  
> 生成时间: 2025-10-19

---

## ✅ 测试完成

### 测试结果
已成功为4个数据集各处理3个学生：

| 数据集 | 状态 | Persona | Memory | Last Interactions |
|--------|------|---------|--------|-------------------|
| **ASSISTments2017** | ✅ 成功 | 3学生 | 3学生 | 1学生 |
| **NIPS Task 3&4** | ✅ 成功 | 3学生 | 3学生 | 1学生 |
| **Algebra2005** | ✅ 成功 | 3学生 | 3学生 | 1学生 |
| **Bridge2Algebra2006** | ✅ 成功 | 3学生 | 3学生 | 1学生 |

### 生成的文件
```
/mnt/localssd/bank/
├── persona/
│   ├── assist2017/
│   │   ├── data/personas.json (2.8MB)
│   │   └── last_interactions/last_interactions.json
│   ├── nips_task34/
│   │   ├── data/personas.json (2.7MB)
│   │   └── last_interactions/last_interactions.json
│   ├── algebra2005/
│   │   ├── data/personas.json (3.8MB)
│   │   └── last_interactions/last_interactions.json
│   └── bridge2006/
│       ├── data/personas.json (2.3MB)
│       └── last_interactions/last_interactions.json
└── memory/
    ├── assist2017/data/memories.json
    ├── nips_task34/data/memories.json
    ├── algebra2005/data/memories.json
    └── bridge2006/data/memories.json
```

---

## 📊 数据结构

### Persona示例
```json
{
  "uid": 1365,
  "personas": [
    {
      "concept_id": 7,
      "concept_text": "Concept 7",
      "description": "Student shows good understanding of Concept 7 with 67% accuracy over 12 attempts.",
      "keywords": "Concept 7",
      "stats": {
        "correct": 8,
        "total": 12
      },
      "description_embedding": [0.00324, 0.00599, ...],  // 1024维
      "keywords_embedding": [0.01142, -0.00826, ...]     // 1024维
    }
  ]
}
```

### Memory示例
```json
{
  "uid": 1365,
  "memories": [
    {
      "concept_id": 7,
      "concept_text": "Concept 7",
      "description": "Student answered question 1234 on Concept 7 correctly.",
      "keywords": "Concept 7",
      "question_id": 1234,
      "response": 1,
      "timestamp": 1567891234000,
      "description_embedding": [0.00324, ...],
      "keywords_embedding": [0.01142, ...]
    }
  ]
}
```

### Last Interactions示例
```json
{
  "1365": {
    "7": {
      "question_id": 1234,
      "response": 1,
      "timestamp": 1567891234000
    }
  }
}
```

---

## 🚀 运行完整版本

### 方式1: 自动脚本（推荐）
```bash
cd /mnt/localssd
chmod +x run_full_bank_creation.sh
bash run_full_bank_creation.sh
```

### 方式2: 手动运行
```bash
cd /mnt/localssd
source activate pykt

# 修改为完整模式
sed -i 's/TEST_MODE = True/TEST_MODE = False/' create_student_bank_v2.py

# 后台运行
nohup python -u create_student_bank_v2.py > bank_creation_full.log 2>&1 &
```

### 监控进度
```bash
# 查看日志
tail -f /mnt/localssd/bank_creation_full.log

# 查看进程
ps aux | grep create_student_bank

# 查看GPU使用
nvidia-smi

# 查看生成的文件大小
du -sh /mnt/localssd/bank/persona/*/data/
```

---

## ⏱️ 预计运行时间

基于测试性能（每个学生~4秒）：

| 数据集 | 学生数 | 预计时间 |
|--------|--------|----------|
| **ASSISTments2017** | 4,487 | ~5小时 |
| **NIPS Task 3&4** | 7,795 | ~8.5小时 |
| **Algebra2005** | 3,980 | ~4.5小时 |
| **Bridge2Algebra2006** | 7,795 | ~8.5小时 |
| **总计** | 24,057 | **~27小时** |

**建议**: 过夜运行

---

## 🔍 关键特性

### 1. 排除最后一次答题 ✅
- **Persona和Memory**: 不包含每个concept的最后一次答题
- **Last Interactions**: 单独保存每个concept的最后一次答题
- **用途**: 最后一次答题用于forgetting score计算的输入

### 2. LLM生成描述 ✅
- **模型**: GPT-4o
- **Persona**: 基于历史表现的掌握程度总结
- **Memory**: 目前使用简化版本（未调用LLM以节省成本）

### 3. BGE-M3 Embeddings ✅
- **模型**: BAAI/bge-m3
- **维度**: 1024
- **编码**: Description和Keywords分别编码

### 4. 自动保存 ✅
- 每处理10个学生自动保存一次
- 防止中断导致数据丢失

---

## 📊 数据统计

### 预期输出规模

#### Persona
- **每个学生**: ~5-15个concepts的persona
- **每个persona**: ~150 bytes (不含embedding) + 8KB (embeddings)
- **预计总大小**: 
  - ASSISTments2017: ~300-500MB
  - NIPS Task 3&4: ~500-800MB  
  - Algebra2005: ~250-400MB
  - Bridge2Algebra2006: ~500-800MB

#### Memory  
- **每个学生**: 最多50个事件memory
- **预计总大小**: 类似Persona

#### Last Interactions
- **每个学生**: ~5-15个concept的最后一次
- **预计总大小**: ~10-20MB per dataset

---

## 🎯 使用场景

### 1. 检索相似学生
```python
# 找到在某个concept上表现相似的学生
import json
import numpy as np

with open('/mnt/localssd/bank/persona/assist2017/data/personas.json') as f:
    data = json.load(f)

# 提取某个concept的所有persona embeddings
concept_7_embeddings = []
for student in data:
    for p in student['personas']:
        if p['concept_id'] == 7:
            concept_7_embeddings.append(p['description_embedding'])

# 计算相似度
query_emb = concept_7_embeddings[0]
similarities = np.dot(concept_7_embeddings, query_emb)
```

### 2. Forgetting Score计算
```python
# 使用last_interactions作为输入
with open('/mnt/localssd/bank/persona/assist2017/last_interactions/last_interactions.json') as f:
    last_interactions = json.load(f)

# 对每个学生的每个concept
for uid, concepts in last_interactions.items():
    for concept_id, interaction in concepts.items():
        # 使用模型预测这次答题的概率
        predicted_prob = model.predict(interaction)
        
        # 计算forgetting score
        delta_t = calculate_time_since_prev(uid, concept_id)
        forgetting_score = (1 - predicted_prob) * (delta_t / (delta_t + tau))
```

### 3. 个性化推荐
```python
# 基于persona找到学生的弱项
weak_concepts = []
for p in student['personas']:
    if p['stats']['correct'] / p['stats']['total'] < 0.6:
        weak_concepts.append(p['concept_id'])

# 推荐练习
recommended_questions = get_questions_for_concepts(weak_concepts)
```

---

## 🔧 配置说明

### 可调整参数

```python
# create_student_bank_v2.py

# LLM配置
MODEL = "gpt-4o"  # 可选: gpt-4o-mini (更便宜但质量略低)

# BGE配置
devices='cuda:0'  # 使用的GPU
use_fp16=True     # 半精度加速

# Memory数量限制
history[:50]      # 每个学生最多50个memory事件

# Persona Prompt
stats.items()[:20]  # 每次LLM调用最多20个concepts
```

### GPU使用
- **当前**: GPU 0
- **如果需要多GPU**: 可以修改为不同数据集使用不同GPU
  ```python
  devices='cuda:0'  # assist2017
  devices='cuda:1'  # nips_task34
  # ...
  ```

---

## ⚠️ 注意事项

### 1. API限流
- GPT-4o有rate limit
- 目前已实现重试机制（最多3次，指数退避）
- 如遇到频繁限流，可降低速度或使用gpt-4o-mini

### 2. 内存使用
- BGE-M3模型: ~4GB GPU内存
- 数据处理: ~2-4GB系统内存
- 确保有足够的磁盘空间（预计总计~5-10GB）

### 3. 数据一致性
- 每10个学生保存一次
- 如中断，重启会从头开始（但已保存的数据不会丢失）
- 建议完成后验证数据完整性

---

## 📁 完整文件清单

### 脚本文件
```
/mnt/localssd/
├── create_student_bank_v2.py       # 主脚本（工作版本）
├── run_full_bank_creation.sh       # 启动脚本
├── test_simple.py                  # 测试LLM和BGE
├── STUDENT_BANK_COMPLETE_GUIDE.md  # 本文档
└── BANK_CREATION_GUIDE.md          # 详细设计文档
```

### 数据文件
```
/mnt/localssd/bank/
├── persona/{dataset}/
│   ├── data/personas.json
│   └── last_interactions/last_interactions.json
└── memory/{dataset}/
    └── data/memories.json
```

### 日志文件
```
/mnt/localssd/
├── bank_creation_test.log          # 测试日志
└── bank_creation_full.log          # 完整运行日志（运行后生成）
```

---

## 🎯 下一步

### 立即运行
```bash
cd /mnt/localssd
bash run_full_bank_creation.sh
```

### 等待完成（~27小时）
监控进度：
```bash
tail -f /mnt/localssd/bank_creation_full.log
```

### 验证结果
```bash
# 检查文件大小
ls -lh /mnt/localssd/bank/persona/*/data/personas.json

# 统计学生数
python -c "import json; data=json.load(open('/mnt/localssd/bank/persona/assist2017/data/personas.json')); print(f'ASSISTments2017: {len(data)} students')"
```

---

## 📊 完成后的数据
格式
### 数据集对比

| 数据集 | 总学生 | Persona学生 | Memory学生 | Last Interactions |
|--------|--------|-------------|------------|-------------------|
| **ASSISTments2017** | 4,487 | ~4,400 | ~4,400 | ~4,400 |
| **NIPS Task 3&4** | 7,795 | ~7,700 | ~7,700 | ~7,700 |
| **Algebra2005** | 3,980 | ~3,900 | ~3,900 | ~3,900 |
| **Bridge2Algebra2006** | 7,795 | ~7,700 | ~7,700 | ~7,700 |

*(部分学生可能因数据不足被跳过)*

---

## 💡 技术亮点

1. ✅ **完全自动化**: 一键运行，无需人工干预
2. ✅ **排除最后一次**: 严格遵循用户要求
3. ✅ **LLM增强**: 使用GPT-4o生成高质量描述
4. ✅ **向量化**: BGE-M3生成1024维embedding
5. ✅ **鲁棒性**: 自动保存、重试机制、错误处理
6. ✅ **可扩展**: 易于添加新数据集或修改逻辑

---

**创建时间**: 2025-10-19  
**状态**: ✅ 测试完成，准备运行完整版本  
**预计完成时间**: ~27小时后

