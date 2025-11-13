# 如何正确使用训练好的KT模型

## 🎯 你的模型有什么用？

你训练好的LPKT、simpleKT、DKT、AKT模型有很多实际用途！

### 1. **标准评估：测试集性能评估** ⭐ **最常用**

这是KT模型最标准的用途 - 评估模型在未见过的数据上的预测准确性。

```bash
# PyKT已经提供了完整的评估脚本
cd /mnt/localssd/pykt-toolkit/examples

# 评估LPKT模型
python wandb_lpkt_train.py \
    --dataset_name=assist2017 \
    --save_dir=saved_model \
    --seed=42 \
    --fold=0 \
    --use_wandb=0 \
    --eval_only=1  # 只评估，不训练
```

**输出：**
- AUC (Area Under ROC Curve)：~0.75-0.80
- ACC (Accuracy)：~0.72-0.77
- 这些指标评估模型在test set上的预测能力

### 2. **序列预测：预测学生下一题表现**

这是KT的核心任务 - 给定学生的答题历史，预测下一题的答对概率。

**为什么之前失败？**
```python
# ❌ 错误方式：直接用原始question IDs
questions = [100, 205, 350, ...]  # 原始IDs
y = model(questions)  # 失败！ID超出范围
```

**✅ 正确方式：使用PyKT的DataLoader**
```python
from pykt.datasets.lpkt_dataloader import LPKTDataset
from torch.utils.data import DataLoader

# 1. 使用训练时相同的数据预处理
dataset = LPKTDataset(
    data_path='../data/assist2017/test_sequences.csv',
    # 其他参数和训练时一致
)

# 2. 创建DataLoader
test_loader = DataLoader(dataset, batch_size=1, shuffle=False)

# 3. 使用模型预测
model.eval()
for batch in test_loader:
    dcur = batch
    # LPKT的输入格式
    if model_name == 'lpkt':
        cq = torch.cat((dcur["qseqs"][:,0:1], dcur["shft_qseqs"]), dim=1)
        cr = torch.cat((dcur["rseqs"][:,0:1], dcur["shft_rseqs"]), dim=1)
        cit = torch.cat((dcur["itseqs"][:,0:1], dcur["shft_itseqs"]), dim=1)
        y = model(cq, cr, cit)  # 成功！
```

### 3. **模型对比研究**

对比不同模型的性能：

| 模型 | AUC (ASSISTments2017) | AUC (EdNet) | 特点 |
|-----|---------------------|-------------|------|
| LPKT | 0.76 | 0.72 | 学习+遗忘，有时间因子 |
| DKT | 0.73 | 0.70 | 基础LSTM |
| AKT | 0.77 | 0.73 | Transformer，注意力机制 |
| simpleKT | 0.76 | 0.72 | 简化的Transformer |

### 4. **在线学习系统**

在真实应用中实时预测学生表现：

```python
class OnlineLearningSystem:
    def __init__(self, model_path):
        self.model = load_model(model_path)
        self.student_history = {}
    
    def predict_next_question(self, student_id, next_question_id):
        """预测学生在下一题的表现"""
        history = self.student_history[student_id]
        
        # 使用PyKT的数据格式
        batch = self.prepare_batch(history, next_question_id)
        
        with torch.no_grad():
            prediction = self.model(batch)
        
        return torch.sigmoid(prediction).item()
    
    def update_history(self, student_id, question_id, response):
        """更新学生答题历史"""
        self.student_history[student_id].append({
            'question': question_id,
            'response': response,
            'timestamp': time.time()
        })
```

---

## 🔧 正确使用模型的方法

### 方法1: 使用PyKT的评估脚本 ⭐ **推荐**

这是最简单、最正确的方式：

```bash
# 进入PyKT目录
cd /mnt/localssd/pykt-toolkit/examples

# 评估所有四个数据集的LPKT模型
for dataset in assist2017 ednet algebra2005 bridge2algebra2006; do
    echo "Evaluating LPKT on $dataset..."
    python wandb_lpkt_train.py \
        --dataset_name=$dataset \
        --save_dir=saved_model \
        --seed=42 \
        --fold=0 \
        --use_wandb=0 \
        --load_best_model=1 \
        # 评估参数会自动从训练时的config读取
done
```

**输出示例：**
```
Test Results:
  AUC: 0.7612
  ACC: 0.7341
  RMSE: 0.4523
```

### 方法2: 使用evaluate_model模块

直接调用PyKT的评估函数：

```python
from pykt.models.evaluate_model import evaluate
from pykt.datasets.lpkt_dataloader import LPKTDataset
from torch.utils.data import DataLoader

# 1. 加载模型
model = load_trained_model('saved_model/assist2017_lpkt_...')

# 2. 准备测试数据
test_dataset = LPKTDataset(
    data_path='../data/assist2017/test_sequences.csv',
    # ... 其他参数
)
test_loader = DataLoader(test_dataset, batch_size=64)

# 3. 评估
auc, acc = evaluate(
    model=model,
    test_loader=test_loader,
    model_name='lpkt',
    save_path='test_results.txt'
)

print(f"AUC: {auc:.4f}, ACC: {acc:.4f}")
```

---

## 🆚 模型预测 vs 历史准确率

### 场景1: 评估模型性能

**用途：** 研究、论文、模型开发

**使用：** ✅ **必须用模型预测**

```python
# 正确评估模型的预测能力
auc = evaluate_model_on_test_set(model, test_loader)
# 输出：AUC = 0.76 (比随机猜测0.5好很多)
```

### 场景2: 计算Forgetting Score

**用途：** 识别需要复习的concepts

**两种方案对比：**

| 方案 | 实现难度 | 效果 | 推荐度 |
|-----|---------|------|--------|
| **历史准确率** | 很简单 | 58.3% vs 30%答错率 | ⭐⭐⭐⭐⭐ |
| **模型预测** | 复杂（需要修复ID映射） | 可能更好？ | ⭐⭐⭐ |

**为什么历史准确率已经很好？**

1. **直接反映真实掌握度**
   ```python
   # 学生A：concept X做了10次，对了8次
   s_tc = 0.8  # 高掌握度
   
   # 学生B：concept X做了10次，对了3次
   s_tc = 0.3  # 低掌握度
   ```

2. **简单可靠**
   - 不依赖复杂的模型推理
   - 不受question ID映射问题影响
   - 计算速度快

3. **已验证有效**
   - 高FS concepts：58.3%答错
   - 低FS concepts：30%答错
   - 显著差异！

---

## 💡 实际建议

### 对于研究/开发KT模型：

✅ **使用模型预测** - 评估模型能力

```bash
# 运行完整评估
cd /mnt/localssd/pykt-toolkit/examples

# 评估所有模型
python evaluate_all_models.py \
    --dataset=assist2017 \
    --models=lpkt,dkt,akt,simplekt
```

### 对于计算Forgetting Score：

✅ **继续使用历史准确率** - 简单有效

```python
def calculate_forgetting_score(student_history, concept_id, tau):
    """
    简单有效的forgetting score计算
    """
    # 1. 计算历史准确率
    concept_responses = [r for c, r in zip(
        student_history['concepts'],
        student_history['responses']
    ) if c == concept_id]
    
    s_tc = np.mean(concept_responses) if concept_responses else 0.5
    
    # 2. 计算时间间隔
    last_time = get_last_attempt_time(student_history, concept_id)
    delta_t = (current_time - last_time) / 60  # 分钟
    
    # 3. 计算FS
    fs = (1 - s_tc) * (delta_t / (delta_t + tau))
    
    return fs
```

---

## 🚀 快速开始：评估你的模型

让我为你创建一个评估脚本：

```bash
#!/bin/bash
# evaluate_trained_models.sh

cd /mnt/localssd/pykt-toolkit/examples

echo "================================"
echo "评估训练好的KT模型"
echo "================================"

DATASETS="assist2017 ednet algebra2005 bridge2algebra2006"
MODELS="lpkt dkt akt simplekt"

for dataset in $DATASETS; do
    for model in $MODELS; do
        echo ""
        echo "Dataset: $dataset, Model: $model"
        echo "--------------------------------"
        
        # 查找模型目录
        model_dir=$(ls -d saved_model/${dataset}_${model}_* 2>/dev/null | head -1)
        
        if [ -d "$model_dir" ]; then
            echo "✓ 找到模型: $model_dir"
            
            # 读取test set的AUC/ACC
            if [ -f "$model_dir/test_results.txt" ]; then
                echo "Test Results:"
                grep -E "AUC|ACC" "$model_dir/test_results.txt"
            else
                echo "⚠ 未找到测试结果，需要运行评估"
            fi
        else
            echo "✗ 未找到模型"
        fi
    done
done
```

---

## 📊 总结

| 任务 | 使用方法 | 工具 |
|-----|---------|------|
| **评估模型性能** | ✅ 模型预测（PyKT评估脚本） | `wandb_*_train.py --eval_only` |
| **预测下一题** | ✅ 模型预测（使用DataLoader） | PyKT DataLoader + model.forward() |
| **Forgetting Score** | ✅ 历史准确率（简单有效） | 直接计算平均正确率 |
| **模型对比研究** | ✅ 模型预测 | 对比AUC/ACC指标 |

**关键点：**
1. 你的模型很有用！用于评估和预测
2. 使用PyKT的数据pipeline才能正确预测
3. 对于forgetting score，历史准确率已经很好

**下一步：**
想要我帮你运行评估脚本，看看你的模型在test set上的实际表现吗？

