# Student Role-Play 评估系统使用说明

## 📋 系统概述

这是一个基于LLM的学生role-play评估系统，可以模拟不同水平的学生回答问题，用于测试tutoring方法的效果。

## 📁 目录结构

```
bank/evaluation_results/
├── {method_name}/              # 例如: pre-test, few-shot, chain-of-thought
│   └── {dataset_name}/         # 例如: assist2017, algebra2005
│       ├── overall.json        # 该method在该dataset上的整体统计 ⭐
│       ├── batch_summary.json  # 批次测试的详细信息
│       └── student_{id}_concept_{cid}.json  # 每个学生的详细结果
```

## 🎯 Quick Start

### 1. 评估单个学生

```python
from student_roleplay_evaluation import evaluate_single_student

result = evaluate_single_student(
    student_id=1,
    dataset="assist2017", 
    method="pre-test"
)
```

### 2. 批量评估多个学生

```python
from batch_test_students import batch_evaluate_students

student_ids = [1, 2, 3, 4, 5]

batch_evaluate_students(
    student_ids=student_ids,
    dataset="assist2017",
    method="pre-test",  # ⭐ 指定你的tutoring method名称
    max_workers=5       # 多线程并行数量
)
```

### 3. 测试新的Tutoring Method

当你有新的tutoring方法时，只需更改method参数：

```python
# Method 1: Pre-test baseline
batch_evaluate_students(
    student_ids=[1,2,3],
    method="pre-test",
    dataset="assist2017"
)

# Method 2: Few-shot learning
batch_evaluate_students(
    student_ids=[1,2,3],
    method="few-shot-learning",
    dataset="assist2017"
)

# Method 3: Chain-of-thought
batch_evaluate_students(
    student_ids=[1,2,3],
    method="chain-of-thought",
    dataset="assist2017"
)
```

每个method会生成独立的文件夹和统计数据。

## 📊 Overall.json 结构

每个method下的overall.json包含：

```json
{
  "method": "pre-test",
  "dataset": "assist2017",
  "num_students_evaluated": 5,
  "average_original_accuracy": 0.493,
  "average_roleplay_accuracy": 0.720,
  "average_absolute_deviation": 0.227,
  "performance_by_level": {
    "struggling": {
      "range": "<40%",
      "num_students": 2,
      "avg_deviation": 0.274
    },
    "developing": {
      "range": "40-60%",
      "num_students": 1,
      "avg_deviation": 0.144
    },
    "competent": {
      "range": "60-80%",
      "num_students": 1,
      "avg_deviation": 0.300
    },
    "strong": {
      "range": "≥80%",
      "num_students": 1,
      "avg_deviation": 0.143
    }
  }
}
```

## 🔧 配置说明

### Prompt配置

在 `student_roleplay_evaluation.py` 中调整prompt策略：
- 修改 `build_student_system_prompt()` 函数
- 针对不同水平学生使用不同的prompt策略

### API配置

在 `roleplay_config.py` 中配置：
- `ENDPOINT`: LLM API地址
- `API_KEY`: API密钥
- `STUDENT_MODEL`: Role-play学生的模型（如 gpt-oss-120b）
- `GRADER_MODEL`: 批改作业的模型（如 gpt-4o-mini）
- `STUDENT_TEMPERATURE`: 学生回答的温度参数

## 📈 评估指标

### 关键指标

1. **Original Accuracy**: 学生的历史真实准确率
2. **Roleplay Accuracy**: Role-play模拟的准确率
3. **Deviation**: 两者之间的偏差
4. **Average Absolute Deviation**: 平均绝对偏差（越小越好）

### 水平分级

- **STRUGGLING** (<40%): 低水平学生
- **DEVELOPING** (40-60%): 发展中学生
- **COMPETENT** (60-80%): 胜任学生
- **STRONG** (≥80%): 高水平学生

## 💡 使用建议

### 1. 选择测试学生

建议选择覆盖不同准确率区间的学生：
```python
# 找不同水平的学生
low_accuracy_students = [1264, 793]      # 0-40%
mid_accuracy_students = [565]            # 40-60%
high_accuracy_students = [398, 1355]     # 60-100%

all_students = low_accuracy_students + mid_accuracy_students + high_accuracy_students
```

### 2. 比较不同Method

```python
# 运行多个methods
for method in ['pre-test', 'few-shot', 'chain-of-thought']:
    batch_evaluate_students(
        student_ids=all_students,
        method=method,
        dataset="assist2017"
    )

# 然后比较各method的overall.json
```

### 3. 查看结果

```python
import json

# 读取overall统计
with open('bank/evaluation_results/pre-test/assist2017/overall.json') as f:
    pre_test_stats = json.load(f)

print(f"Pre-test平均偏差: {pre_test_stats['average_absolute_deviation']*100:.1f}%")
```

## 🚀 高级功能

### 多线程并行

系统支持多线程并行评估，大幅提升速度：
```python
batch_evaluate_students(
    student_ids=list(range(1, 101)),  # 评估100个学生
    max_workers=10,                   # 10个线程并行
    method="pre-test"
)
```

### 自定义题目

题目存储在 `bank/test_data/{dataset}/concept_questions.json`，每个concept有10道题。

## 📝 文件说明

- `student_roleplay_evaluation.py`: 核心评估逻辑
- `batch_test_students.py`: 批量评估脚本
- `roleplay_config.py`: 配置文件
- `FLEXIBLE_PROMPT_TEST_REPORT.md`: Prompt测试报告

## 🐛 常见问题

### Q: 如何添加新dataset？
A: 在 `bank/session/{new_dataset}/` 和 `bank/test_data/{new_dataset}/` 添加数据即可。

### Q: 如何调整学生回答的准确率？
A: 修改 `student_roleplay_evaluation.py` 中的 `build_student_system_prompt()` 函数，或调整 `STUDENT_TEMPERATURE`。

### Q: Overall.json什么时候更新？
A: 每次运行 `batch_evaluate_students()` 都会更新该method的overall.json。

## 📧 Support

有问题请查看日志文件：`logs/batch_test_*.log`

