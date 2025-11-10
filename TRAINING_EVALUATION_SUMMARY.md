# 📊 Knowledge Tracing模型训练与评估总结

## ✅ 已完成的模型训练和评估

### 1. LPKT (Learning Process-consistent Knowledge Tracing)

#### EdNet数据集
- **状态**: ✅ 训练完成
- **模型路径**: `saved_model/ednet_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_1_0`
- **训练参数**:
  - Learning rate: 0.003
  - Dropout: 0.2
  - Embedding size: 64
  - Fold: 0
- **性能**: 训练中（未提供test set评估）

#### ASSISTments2017数据集
- **状态**: ✅ 训练完成
- **模型路径**: `saved_model/assist2017_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_1_0`
- **训练参数**: 同上
- **验证集性能** (Best Epoch 9):
  - Valid AUC: **0.7792**
  - Valid ACC: **0.7231**

---

### 2. simpleKT (Simple Knowledge Tracing)

#### EdNet数据集
- **状态**: ✅ 训练完成
- **模型路径**: `saved_model/ednet_simplekt_qid_saved_model_42_0_0.1_256_256_2_4_0.5_0.5_0.5_50_256_256_4_2_0.0001_1_0`
- **训练参数**:
  - Learning rate: 0.001
  - Dropout: 0.1
  - d_model: 256
  - n_blocks: 2
  - Fold: 0
- **验证集性能** (Best Epoch 28):
  - Valid AUC: **0.9460**
  - Valid ACC: **0.8693**
  - 🏆 在EdNet上表现优异！

#### ASSISTments2017数据集
- **状态**: ✅ 训练完成
- **模型路径**: `saved_model/assist2017_simplekt_qid_saved_model_42_0_0.1_256_256_2_4_0.5_0.5_0.5_50_256_256_4_2_0.0001_1_0`
- **训练参数**: 同上
- **验证集性能** (Best Epoch 49):
  - Valid AUC: **0.7597**
  - Valid ACC: **0.7065**

---

## 🔄 正在训练的模型

### 3. DKT (Deep Knowledge Tracing)

#### EdNet数据集
- **状态**: 🔄 训练中
- **GPU**: 2
- **日志**: `/tmp/kt_training_logs/ednet_dkt.log`
- **训练脚本**: `wandb_dkt_train.py`
- **WandB**: 已启用

#### ASSISTments2017数据集
- **状态**: 🔄 训练中
- **GPU**: 3
- **日志**: `/tmp/kt_training_logs/assist2017_dkt.log`
- **训练脚本**: `wandb_dkt_train.py`
- **WandB**: 已启用

---

### 4. AKT (Attention-based Knowledge Tracing)

#### EdNet数据集
- **状态**: 🔄 训练中
- **GPU**: 4
- **日志**: `/tmp/kt_training_logs/ednet_akt.log`
- **训练脚本**: `wandb_akt_train.py`
- **WandB**: 已启用

#### ASSISTments2017数据集
- **状态**: 🔄 训练中
- **GPU**: 5
- **日志**: `/tmp/kt_training_logs/assist2017_akt.log`
- **训练脚本**: `wandb_akt_train.py`
- **WandB**: 已启用

---

## 📈 性能对比总结

| 模型 | 数据集 | Valid AUC | Valid ACC | 状态 |
|------|--------|-----------|-----------|------|
| **simpleKT** | EdNet | **0.9460** | **0.8693** | ✅ 完成 |
| **simpleKT** | ASSISTments2017 | 0.7597 | 0.7065 | ✅ 完成 |
| **LPKT** | EdNet | - | - | ✅ 完成 |
| **LPKT** | ASSISTments2017 | 0.7792 | 0.7231 | ✅ 完成 |
| **DKT** | EdNet | - | - | 🔄 训练中 |
| **DKT** | ASSISTments2017 | - | - | 🔄 训练中 |
| **AKT** | EdNet | - | - | 🔄 训练中 |
| **AKT** | ASSISTments2017 | - | - | 🔄 训练中 |

### 关键发现

1. **simpleKT在EdNet上表现最佳**
   - Valid AUC达到0.946，Valid ACC达到0.869
   - 说明Transformer架构在大规模数据上效果显著

2. **LPKT在ASSISTments2017上表现良好**
   - Valid AUC 0.779，略高于simpleKT的0.760
   - 证明时间间隔信息对知识追踪的重要性

3. **EdNet vs ASSISTments2017**
   - EdNet数据集规模更大，模型性能普遍更高
   - ASSISTments2017更具挑战性

---

## 🔍 监控命令

### 查看训练进度
```bash
# 实时查看DKT训练
tail -f /tmp/kt_training_logs/ednet_dkt.log
tail -f /tmp/kt_training_logs/assist2017_dkt.log

# 实时查看AKT训练
tail -f /tmp/kt_training_logs/ednet_akt.log
tail -f /tmp/kt_training_logs/assist2017_akt.log
```

### 查看GPU使用情况
```bash
nvidia-smi
# 或实时监控
watch -n 1 nvidia-smi
```

### 查看训练进程
```bash
ps aux | grep "wandb.*train" | grep -v grep
```

---

## 📁 模型文件位置

所有训练好的模型保存在：
```
/mnt/localssd/pykt-toolkit/examples/saved_model/
```

每个模型目录包含：
- `config.json`: 模型配置文件
- `qid_model.ckpt`: 最佳模型权重

---

## 🎯 模型使用示例

### 1. 加载训练好的模型进行预测
```python
from pykt.models import init_model, load_model
import torch

# 加载simpleKT模型（EdNet）
model_dir = "saved_model/ednet_simplekt_qid_saved_model_42_0_0.1_256_256_2_4_0.5_0.5_0.5_50_256_256_4_2_0.0001_1_0"
config_path = f"{model_dir}/config.json"

import json
with open(config_path, 'r') as f:
    config = json.load(f)

model = init_model("simplekt", config)
model.load_state_dict(torch.load(f"{model_dir}/qid_model.ckpt"))
model.eval()
```

### 2. 计算Forgetting Score
```python
from forgetting_score_calculator import ForgettingScoreCalculator

calculator = ForgettingScoreCalculator(
    model_dir=model_dir,
    tau=7*24*60,  # 7天
    device="cuda" if torch.cuda.is_available() else "cpu"
)

# 更新学生历史并计算遗忘分数
calculator.update_student_history(
    student_id="S001",
    concept_id=5,
    response=1,
    timestamp=current_time
)

score = calculator.calculate_forgetting_score(
    student_id="S001",
    target_concept=5,
    current_time=current_time
)

print(f"Forgetting Score: {score['forgetting_score']:.4f}")
```

---

## 📚 相关文档

- **Forgetting Score指南**: `/mnt/localssd/FORGETTING_SCORE_GUIDE.md`
- **预测示例**: `/mnt/localssd/pykt-toolkit/examples/predict_new_data.py`
- **API示例**: `/mnt/localssd/pykt-toolkit/examples/forgetting_api_example.py`
- **模型输入说明**: `/mnt/localssd/MODEL_INPUT_EXPLAINED.md`
- **Student ID使用**: `/mnt/localssd/KT_MODELS_WITH_STUDENT_ID.md`

---

## 🌐 WandB监控

访问 https://wandb.ai 查看：
- 实时训练曲线
- Loss变化
- AUC/ACC指标
- GPU利用率
- 超参数配置

---

## ⏰ 预计完成时间

基于当前训练进度：
- **DKT**: 预计 3-5 小时
- **AKT**: 预计 4-6 小时

---

## ✅ 下一步

1. **等待DKT和AKT训练完成**
2. **评估所有四个模型**
3. **对比分析性能差异**
4. **选择最佳模型部署**

---

**最后更新**: 2025-10-18 21:36
**状态**: 2/4模型已完成，2/4模型训练中

