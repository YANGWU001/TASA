# 🎯 LPKT模型预测使用指南

## 📖 模型用途

LPKT（Learning Process-consistent Knowledge Tracing）模型可以：

1. **预测答题概率**：根据学生历史答题记录，预测其答对下一题的概率
2. **评估知识掌握**：了解学生对各知识点的掌握程度
3. **个性化推荐**：基于预测概率推荐合适难度的题目
4. **学习路径规划**：设计最优学习序列

## 🔧 模型工作原理

```
输入：学生的答题历史
┌─────────────────────────────────────┐
│ 问题序列: [Q1, Q2, Q3, Q4, Q5]     │
│ 答题结果: [1,  0,  1,  1,  ?]      │
│           (1=对, 0=错, ?=待预测)   │
└─────────────────────────────────────┘
            ↓
      【LPKT模型】
            ↓
输出：每道题答对的概率
┌─────────────────────────────────────┐
│ Q1: 0.85 (85%)                      │
│ Q2: 0.62 (62%) ← 实际答错了         │
│ Q3: 0.78 (78%)                      │
│ Q4: 0.82 (82%)                      │
│ Q5: 0.75 (75%) ← 预测下一题概率    │
└─────────────────────────────────────┘
```

## 🚀 快速开始

### 方法1: 演示模式（推荐新手）

```bash
cd /mnt/localssd/pykt-toolkit/examples
source activate pykt
python predict_new_data.py --mode demo
```

**这会展示**：
- 如何加载模型
- 示例数据格式
- 预测结果解读

### 方法2: 交互式模式

```bash
python predict_new_data.py --mode interactive
```

**交互式输入**：
1. 选择要使用的模型
2. 输入问题ID序列
3. 输入答题结果
4. 查看预测结果

## 📊 输入数据格式

### 最简单的格式：

```python
student_data = {
    'question_ids': [10, 25, 30, 10, 40],  # 问题ID
    'responses': [1, 0, 1, 1, 0],          # 答题结果 (1=对, 0=错)
}
```

### 完整格式（包含时间）：

```python
student_data = {
    'student_id': 'S001',                  # 学生ID（可选）
    'question_ids': [10, 25, 30, 10, 40],  # 问题ID
    'responses': [1, 0, 1, 1, 0],          # 答题结果
    'it_times': [0, 120, 60, 180, 90]      # 答题间隔时间（秒，可选）
}
```

### 数据说明：

- **question_ids**: 学生做过的题目ID列表（整数）
- **responses**: 对应每道题的答题结果（1=答对，0=答错）
- **it_times**: 答题间隔时间（秒），可选，默认为0

**注意**：
- 列表长度必须一致
- 问题ID需要在训练数据的范围内
- 可以包含同一题目的多次作答记录

## 💻 Python API使用示例

### 示例1: 单个学生预测

```python
import torch
from predict_new_data import load_model, predict_single_student

# 1. 加载模型
model_dir = "saved_model/ednet_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_1_0"
device = "cuda" if torch.cuda.is_available() else "cpu"
model, config = load_model(model_dir, device=device)

# 2. 准备学生数据
question_ids = [10, 25, 30, 10, 40]
responses = [1, 0, 1, 1, 0]

# 3. 预测
predictions = predict_single_student(
    model, 
    question_ids, 
    responses,
    device=device
)

# 4. 查看结果
for i, (qid, pred) in enumerate(zip(question_ids, predictions)):
    print(f"题目{i+1} (ID:{qid}): 答对概率 = {pred:.4f} ({pred*100:.2f}%)")
```

### 示例2: 批量预测

```python
from predict_new_data import predict_batch

# 多个学生的数据
students_data = [
    {
        'student_id': 'S001',
        'question_ids': [10, 25, 30],
        'responses': [1, 0, 1]
    },
    {
        'student_id': 'S002',
        'question_ids': [15, 20, 25],
        'responses': [0, 1, 1]
    }
]

# 批量预测
results = predict_batch(model, students_data, device=device)

# 查看结果
for result in results:
    print(f"\n学生: {result['student_id']}")
    print(f"预测概率: {result['predictions']}")
```

### 示例3: 在线实时预测

```python
# 场景：学生每做一题，就预测下一题的概率

# 初始状态
history_questions = []
history_responses = []

# 学生做题过程
for question_id, answer in [(10, 1), (25, 0), (30, 1)]:
    # 添加到历史
    history_questions.append(question_id)
    history_responses.append(answer)
    
    # 预测当前状态
    preds = predict_single_student(
        model, 
        history_questions, 
        history_responses,
        device=device
    )
    
    # 最后一个预测值是下一题的预测概率
    next_prob = preds[-1]
    print(f"做完题目{question_id}后，下一题答对概率: {next_prob:.4f}")
```

## 🎮 实际应用场景

### 场景1: 智能题目推荐

```python
def recommend_question(model, student_history, question_pool, target_prob=0.7):
    """
    推荐合适难度的题目
    target_prob: 目标正确率（0.7表示推荐70%正确率的题）
    """
    best_question = None
    min_diff = float('inf')
    
    for question_id in question_pool:
        # 尝试添加这道题，预测答对概率
        test_questions = student_history['question_ids'] + [question_id]
        test_responses = student_history['responses'] + [1]  # 假设答对
        
        preds = predict_single_student(model, test_questions, test_responses)
        pred_prob = preds[-1]
        
        # 找到最接近目标概率的题目
        diff = abs(pred_prob - target_prob)
        if diff < min_diff:
            min_diff = diff
            best_question = question_id
    
    return best_question
```

### 场景2: 知识点评估

```python
def assess_knowledge_level(model, student_history):
    """
    评估学生的知识掌握水平
    """
    predictions = predict_single_student(
        model,
        student_history['question_ids'],
        student_history['responses']
    )
    
    avg_prob = predictions.mean()
    
    if avg_prob >= 0.8:
        level = "优秀"
    elif avg_prob >= 0.6:
        level = "良好"
    elif avg_prob >= 0.4:
        level = "及格"
    else:
        level = "需要加强"
    
    return {
        'level': level,
        'avg_probability': avg_prob,
        'predictions': predictions
    }
```

### 场景3: 学习效果分析

```python
def analyze_learning_progress(model, student_history):
    """
    分析学生的学习进度趋势
    """
    predictions = predict_single_student(
        model,
        student_history['question_ids'],
        student_history['responses']
    )
    
    # 计算趋势
    if len(predictions) >= 3:
        recent_avg = predictions[-3:].mean()
        early_avg = predictions[:3].mean()
        improvement = recent_avg - early_avg
        
        if improvement > 0.1:
            trend = "进步明显 📈"
        elif improvement > 0:
            trend = "稳步提升 ↗️"
        elif improvement > -0.1:
            trend = "保持稳定 ➡️"
        else:
            trend = "需要关注 📉"
    else:
        trend = "数据不足"
    
    return {
        'trend': trend,
        'current_level': predictions[-1] if len(predictions) > 0 else 0,
        'improvement': improvement if len(predictions) >= 3 else 0
    }
```

## 📈 结果解读

### 预测概率含义：

| 概率范围 | 含义 | 建议 |
|---------|------|------|
| 0.8 - 1.0 | 很可能答对 | 可以尝试更难的题目 |
| 0.6 - 0.8 | 较可能答对 | 合适的练习难度 |
| 0.4 - 0.6 | 答对答错各半 | 需要更多练习 |
| 0.2 - 0.4 | 较可能答错 | 需要复习基础知识 |
| 0.0 - 0.2 | 很可能答错 | 需要重新学习该知识点 |

### 注意事项：

1. **预测是概率性的**：概率0.7不代表一定答对，而是有70%的可能性
2. **需要足够的历史数据**：至少3-5道题的历史记录才能获得较准确的预测
3. **模型有适用范围**：只能预测训练数据中包含的知识点和题目类型
4. **考虑时间因素**：学生的知识会随时间变化，定期重新训练模型

## 🔧 高级用法

### 1. 批量处理CSV文件

```python
import pandas as pd

# 读取学生答题数据
df = pd.read_csv('student_answers.csv')

results = []
for student_id in df['student_id'].unique():
    student_data = df[df['student_id'] == student_id]
    
    question_ids = student_data['question_id'].tolist()
    responses = student_data['correct'].tolist()
    
    predictions = predict_single_student(model, question_ids, responses)
    
    results.append({
        'student_id': student_id,
        'predictions': predictions
    })

# 保存结果
pd.DataFrame(results).to_csv('predictions.csv', index=False)
```

### 2. REST API服务

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

# 加载模型（启动时）
model, config = load_model("saved_model/ednet_lpkt_...", device="cuda")

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    
    predictions = predict_single_student(
        model,
        data['question_ids'],
        data['responses'],
        device="cuda"
    )
    
    return jsonify({
        'predictions': predictions.tolist()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

## 📚 可用的模型

训练完成后，您可以使用以下模型：

```bash
# 查看所有可用模型
ls -l /mnt/localssd/pykt-toolkit/examples/saved_model/

# EdNet模型
saved_model/ednet_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_1_0/

# ASSISTments2017模型
saved_model/assist2017_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_1_0/
```

## 🆘 常见问题

**Q: 模型预测的概率不准确？**
A: 可能原因：
- 训练数据不足
- 测试数据与训练数据分布差异大
- 学生历史记录太少

**Q: 可以预测任意题目吗？**
A: 只能预测训练数据中出现过的题目类型和知识点

**Q: 如何处理新学生（没有历史记录）？**
A: 可以使用平均预测概率，或让学生先做几道诊断题

**Q: 预测需要多少历史记录？**
A: 建议至少3-5道题，越多越准确

## 🎓 总结

LPKT模型的使用流程：

```
1. 加载训练好的模型
   ↓
2. 准备学生答题历史数据
   ↓
3. 调用预测函数
   ↓
4. 获得答对概率
   ↓
5. 基于概率做决策（推荐题目、评估等）
```

**立即尝试**：
```bash
cd /mnt/localssd/pykt-toolkit/examples
source activate pykt
python predict_new_data.py --mode demo
```

---
更新时间: $(date)

