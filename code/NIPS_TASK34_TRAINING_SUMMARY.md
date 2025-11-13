# NIPS Task 3&4 训练总结

> 生成时间: 2025-10-19  
> 数据集: NIPS Task 3&4 (NeurIPS 2020 Education Challenge)  
> 状态: ✅ 下载完成，预处理完成，训练进行中

---

## 📊 数据集统计

### 基本信息
- **来源**: NeurIPS 2020 Education Challenge
- **平台**: Eedi (英国在线教育平台)
- **下载地址**: https://dqanonymousdata.blob.core.windows.net/neurips-public/data.zip
- **数据大小**: 656 MB (压缩), ~1.1 GB (解压)

### 数据规模
| 指标 | 数值 |
|------|------|
| **总学生数** | 4,918 |
| **总交互数** | 1,382,727 |
| **题目数** | 948 |
| **Concept数** | **57** (Level 3 subjects) |
| **Train/Valid学生** | 3,935 (80%) |
| **Test学生** | 983 (20%) |
| **Train/Valid交互** | 1,123,343 |
| **Test交互** | 276,127 |

### 特点
- ✅ **有concept文字描述** (Subject names)
- ✅ **3层知识层级结构** (Level 1, 2, 3)
- ✅ **支持多concept题目**
- ✅ **有时间戳**
- ✅ **丰富的metadata**

---

## 🚀 训练配置

### 模型列表
训练了4个Knowledge Tracing模型：

| 模型 | GPU | PID | 日志文件 |
|------|-----|-----|----------|
| **LPKT** | 2 | 98299 | `/tmp/nips_task34_training_logs/lpkt.log` |
| **simpleKT** | 3 | 98444 | `/tmp/nips_task34_training_logs/simplekt.log` |
| **DKT** | 4 | 98652 | `/tmp/nips_task34_training_logs/dkt.log` |
| **AKT** | 5 | 98992 | `/tmp/nips_task34_training_logs/akt.log` |

### 训练参数
- **Dataset**: nips_task34
- **Fold**: 0 (5-fold cross-validation)
- **WandB**: 启用 (use_wandb=1)
- **UUID**: 禁用 (add_uuid=0)
- **运行方式**: 后台运行 (nohup)
- **输出**: unbuffered (stdbuf -oL -eL)

---

## 📈 当前训练进度

### 初步结果（前5个epoch）

#### DKT (最快进展)
```
Epoch 1: valid AUC=0.7225, ACC=0.6688
Epoch 2: valid AUC=0.7452, ACC=0.6831
Epoch 3: valid AUC=0.7521, ACC=0.6876
Epoch 4: valid AUC=0.7554, ACC=0.6906
Epoch 5: valid AUC=0.7572, ACC=0.6921
```

#### simpleKT
```
Epoch 1: valid AUC=0.7281, ACC=0.6691
Epoch 2: valid AUC=0.7374, ACC=0.6758
```

#### LPKT & AKT
正在训练中...

---

## 🖥️ GPU使用情况

| GPU | 模型 | 显存使用 | GPU利用率 | 状态 |
|-----|------|----------|-----------|------|
| 0 | - | ~1 MiB | 0% | 空闲 |
| 1 | - | ~1 MiB | 0% | 空闲 |
| 2 | **LPKT** | ~1.6 GB | 11% | ✅ 训练中 |
| 3 | **simpleKT** | ~1.4 GB | 35% | ✅ 训练中 |
| 4 | **DKT** | ~1.4 GB | 19% | ✅ 训练中 |
| 5 | **AKT** | ~9.6 GB | 55% | ✅ 训练中 |
| 6 | - | ~1 MiB | 0% | 空闲 |
| 7 | - | ~1 MiB | 0% | 空闲 |

**注意**: AKT模型使用显存较多（~9.6GB），这是正常现象。

---

## 📁 文件位置

### 数据文件
```
/mnt/localssd/pykt-toolkit/data/nips_task34/
├── train_task_3_4.csv              # 主训练数据 (31MB)
├── metadata/
│   ├── answer_metadata_task_3_4.csv      (70MB)
│   ├── question_metadata_task_3_4.csv    (23KB)
│   ├── student_metadata_task_3_4.csv     (131KB)
│   └── subject_metadata.csv              (14KB) ⭐ Concept描述
├── data.txt                        # 预处理后的数据
├── keyid2idx.json                  # ID映射
├── train_valid_sequences.csv       # 训练序列
└── test_sequences.csv              # 测试序列
```

### 模型保存位置
```
/mnt/localssd/pykt-toolkit/examples/saved_model/
├── nips_task34_lpkt_*.ckpt
├── nips_task34_simplekt_*.ckpt
├── nips_task34_dkt_*.ckpt
└── nips_task34_akt_*.ckpt
```

### 日志文件
```
/tmp/nips_task34_training_logs/
├── lpkt.log
├── simplekt.log
├── dkt.log
└── akt.log
```

---

## 🔍 监控命令

### 查看训练进度
```bash
# 运行监控脚本
/mnt/localssd/monitor_nips_task34_training.sh

# 持续监控（每5秒刷新）
watch -n 5 /mnt/localssd/monitor_nips_task34_training.sh
```

### 查看实时日志
```bash
# LPKT
tail -f /tmp/nips_task34_training_logs/lpkt.log

# simpleKT
tail -f /tmp/nips_task34_training_logs/simplekt.log

# DKT
tail -f /tmp/nips_task34_training_logs/dkt.log

# AKT
tail -f /tmp/nips_task34_training_logs/akt.log
```

### 查看GPU使用
```bash
nvidia-smi
# 或持续监控
watch -n 1 nvidia-smi
```

### 查看进程状态
```bash
ps aux | grep nips_task34
```

---

## 🎯 Concept描述示例

NIPS Task 3&4有完整的concept（subject）描述！

### 查看Subject描述
```python
import pandas as pd

# 读取subject metadata
subject_df = pd.read_csv('/mnt/localssd/pykt-toolkit/data/nips_task34/metadata/subject_metadata.csv')

# 查看Level 3 subjects (用作concepts)
level3 = subject_df[subject_df['Level'] == 3]
print(level3[['SubjectId', 'Name', 'Level']])
```

### 典型Subjects（基于Eedi平台）
可能包括（需查看actual metadata）:
- **Number**: Fractions, Decimals, Percentages
- **Algebra**: Linear Equations, Solving Equations
- **Geometry**: Area, Angles, Transformations
- **Statistics**: Mean, Median, Probability

这使得结果非常易于解释！例如：
- "学生在**Fractions**上的遗忘分数为0.68"
- "**Linear Equations**的遗忘率高于**Area**"

---

## 📊 与其他数据集对比

| 特性 | EdNet | ASSISTments2017 | **NIPS Task 3&4** |
|------|-------|-----------------|-------------------|
| **学生数** | 4,687 | 1,708 | **4,918** |
| **交互数** | 1.3M | 940K | **1.4M** |
| **Concept数** | 188 | 102 | **57** |
| **Concept描述** | ❌ 无 | ✅ 有 | ✅✅ **有+层级** |
| **层级结构** | ❌ | ❌ | ✅ **3层** |
| **多Concept题目** | ❌ | ❌ | ✅ **支持** |
| **正确率** | 67% | 37% | **待评估** |
| **可解释性** | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

**NIPS Task 3&4在concept描述方面最丰富！**

---

## 💡 使用建议

### 适合的研究场景

1. **需要concept文字描述**
   - ✅ 适合 (有完整的subject names)

2. **需要层级知识结构**
   - ✅✅ 非常适合 (唯一有3层层级的数据集)

3. **研究多concept题目**
   - ✅✅ 非常适合 (唯一支持的数据集)

4. **Forgetting Score分析**
   - ✅✅ 非常适合 (可以分析不同层级的遗忘)

5. **教育应用**
   - ✅✅ 非常适合 (结果易于向教师解释)

### Forgetting Score应用

特别适合NIPS Task 3&4的分析：
- 分析不同Level的知识遗忘模式
- 研究多concept题目的遗忘机制
- 层级遗忘分析（Level 1 → Level 2 → Level 3）

例如：
```
Level 1: Mathematics遗忘分数: 0.65
  ├── Level 2: Algebra遗忘分数: 0.70
  │   └── Level 3: Linear Equations遗忘分数: 0.75
  └── Level 2: Geometry遗忘分数: 0.60
      └── Level 3: Area遗忘分数: 0.62
```

---

## 🔄 后续步骤

### 等待训练完成
- 估计时间: 根据之前经验，每个模型约需1-2小时
- 4个模型并行训练

### 评估模型
训练完成后运行：
```bash
cd /mnt/localssd/pykt-toolkit/examples

# 评估各模型
for model in lpkt simplekt dkt akt; do
    python wandb_eval.py \
        --dataset_name nips_task34 \
        --model_name $model \
        --fold 0
done
```

### Forgetting Score分析
使用训练好的模型进行forgetting score计算：
```python
from flexible_forgetting_api import FlexibleForgettingScoreAPI

# 对每个模型
for model_name in ['lpkt', 'simplekt', 'dkt', 'akt']:
    api = FlexibleForgettingScoreAPI(
        model_name=model_name,
        dataset_name='nips_task34',
        model_dir=f'saved_model/nips_task34_{model_name}_...',
        tau=7*24*60  # 7天
    )
    
    # 计算并报告
    report = api.generate_report(num_students=5)
    print(report)
```

---

## 📚 相关文档

- **数据集信息**: `/mnt/localssd/NIPS_TASK34_INFO.md`
- **三数据集对比**: `/mnt/localssd/ALL_DATASETS_CONCEPT_COMPARISON.md`
- **Concept描述**: `/mnt/localssd/CONCEPT_DESCRIPTIONS.md`
- **监控脚本**: `/mnt/localssd/monitor_nips_task34_training.sh`
- **训练脚本**: `/mnt/localssd/train_nips_task34_all_models.sh`

---

## ✅ 完成状态

- [x] 下载NIPS Task 3&4数据集
- [x] 解压并组织文件结构
- [x] 运行数据预处理
- [x] 启动LPKT训练 (GPU 2)
- [x] 启动simpleKT训练 (GPU 3)
- [x] 启动DKT训练 (GPU 4)
- [x] 启动AKT训练 (GPU 5)
- [ ] 等待训练完成
- [ ] 评估模型性能
- [ ] 进行Forgetting Score分析

---

**更新时间**: 2025-10-19 22:28  
**状态**: 🟢 训练进行中  
**预计完成**: 1-2小时

