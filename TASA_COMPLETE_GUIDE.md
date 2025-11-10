# TASA完整使用指南

## 🎯 系统概述

TASA (Tutoring with Adaptive Student Assessment) 是一个基于RAG和遗忘曲线的个性化教学系统。

### 核心特性

1. **个性化检索** - 根据学生query从persona/memory中检索最相关信息
2. **遗忘曲线调整** - 基于时间间隔重写知识描述
3. **10轮对话教学** - 每轮先讲解再提问
4. **Learning Gain评估** - 计算教学带来的实际提升

---

## 📁 文件结构

### 核心模块
```
tasa_config.py          - 配置管理
tasa_rag.py             - RAG检索+重排
tasa_rewrite.py         - Mastery重写
tasa_tutoring.py        - 对话管理
tasa_evaluation.py      - Post-test评估
```

### 测试脚本
```
test_tasa_single_student.py  - 单个学生测试
check_tasa_progress.sh       - 进度监控
```

---

## 🔄 完整流程

### Phase 1: Tutoring (10轮对话)

```
Round 1:
  Student: "I want to learn [concept]"
     ↓
  [RAG检索] → Top-10 persona/memory
     ↓
  [Reranker精排] → Top-3
     ↓
  [Mastery重写] → Forgetting-adjusted
     ↓
  Tutor: [生成问题1]

Round 2-10:
  Student: [回答上一轮问题]
     ↓
  [RAG检索当前query] → Top-3
     ↓
  [Mastery重写]
     ↓
  Tutor: [讲解上轮答案] + [生成新问题]
```

### Phase 2: Post-test评估

```
Load dialogue → 作为learning context
     ↓
Student回答10道题（基于dialogue context）
     ↓
批改 → Post-test accuracy
     ↓
Learning Gain = (Post - Pre) / (1 - Pre)
```

---

## 🚀 使用方法

### 1. 测试单个学生

```bash
python test_tasa_single_student.py --student-id 1 --dataset assist2017
```

**输出**:
- `bank/dialogue/TASA/assist2017/1-transformations-rotations.json` - 对话记录
- `bank/evaluation_results/TASA/assist2017/student_1_transformations-rotations.json` - 评估结果

### 2. 监控进度

```bash
./check_tasa_progress.sh
```

### 3. 查看结果

```bash
# 查看对话
cat bank/dialogue/TASA/assist2017/1-transformations-rotations.json

# 查看评估结果
cat bank/evaluation_results/TASA/assist2017/student_1_transformations-rotations.json
```

---

## 📊 输出文件格式

### Dialogue文件

```json
{
  "student_id": 1,
  "dataset": "assist2017",
  "concept_text": "transformations-rotations",
  "num_rounds": 10,
  "dialogue": [
    {
      "role": "user",
      "round": 0,
      "content": "I want to learn about transformations-rotations"
    },
    {
      "role": "assistant",
      "round": 1,
      "content": "Let's start with...",
      "retrieved_persona": [...],
      "retrieved_memory": [...],
      "rewritten_persona": [...],
      "rewritten_memory": [...]
    },
    ...
  ]
}
```

### Evaluation结果

```json
{
  "student_id": 1,
  "dataset": "assist2017",
  "concept_text": "transformations-rotations",
  "pre_test_accuracy": 0.273,
  "post_test_accuracy": 0.450,
  "learning_gain": 0.244,
  "improvement": 0.177,
  "answers": [...]
}
```

---

## 🔧 配置说明

### RAG配置 (`tasa_config.py`)

```python
LAMBDA_WEIGHT = 0.5          # description vs keywords权重
TOP_K_RETRIEVE = 10          # 初始检索数量
TOP_K_RERANK = 3             # 精排后保留数量
```

### 对话配置

```python
NUM_TUTORING_ROUNDS = 10     # 教学轮数
TUTOR_TEMPERATURE = 0.7      # Tutor生成温度
STUDENT_TEMPERATURE = 1.0    # Student温度
```

---

## 📈 评估指标

### Learning Gain公式

```
Learning Gain = (Post-test - Pre-test) / (1 - Pre-test)
```

**示例**:
- Pre-test: 30%
- Post-test: 50%
- Learning Gain = (0.5 - 0.3) / (1 - 0.3) = **0.286** (28.6%的相对提升)

### 解读

- **Learning Gain > 0**: 教学有效，学生有提升
- **Learning Gain = 0**: 教学无效果
- **Learning Gain < 0**: 学生退步（罕见）
- **Learning Gain = 1**: 完美提升（从pre-test到100%）

---

## 🎯 对比Pre-test

| Method | 流程 | 评估指标 | 用途 |
|--------|------|---------|------|
| **Pre-test** | 直接role-play | Accuracy | Baseline |
| **TASA** | 10轮教学 + Post-test | Learning Gain | 教学效果 |

**关键对比**:
```
Pre-test Accuracy:  学生当前能力水平
Post-test Accuracy: 教学后的能力水平
Learning Gain:      教学带来的相对提升
```

---

## 🧪 当前测试状态

### TASA测试（学生1）
- ✅ 正在运行
- 📍 Round 1进行中
- ⏱️ 预计5-10分钟完成

### Pre-test Baseline
- ✅ 正在运行
- 📊 636/1708 (37.2%)
- ⏱️ 预计25分钟完成

---

## 🔜 下一步计划

1. ⏳ **等待TASA单学生测试完成**
2. ✅ **验证结果** - 检查dialogue和learning gain
3. 📝 **创建批量脚本** - `run_tasa_all_students.py`
4. 🚀 **批量运行** - 评估所有1708个学生
5. 📊 **生成Overall统计** - 对比Pre-test和TASA效果

---

## 💡 技术亮点

1. **加权相似度**: `λ * sim(desc) + (1-λ) * sim(keywords)`
2. **两阶段检索**: Top-10初筛 → Reranker精排 → Top-3
3. **时间衰减**: 基于forgetting curve动态调整知识状态
4. **Chain-of-Thought**: 每轮先讲解再提问
5. **Context-aware**: Post-test使用dialogue作为learning context

---

## 📞 监控命令

```bash
# 查看TASA进度
./check_tasa_progress.sh

# 实时查看日志
tail -f logs/test_tasa_student1.log

# 查看Pre-test进度
./check_progress.sh

# 检查进程
ps -p $(cat logs/test_tasa_student1.pid)
```

---

**更新时间**: 2025-10-20
**版本**: v1.0
**状态**: 单学生测试中

