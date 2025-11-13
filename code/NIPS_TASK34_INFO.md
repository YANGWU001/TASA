# NIPS Task 3&4 数据集信息

> NeurIPS 2020 Education Challenge  
> 数据来源: https://competitions.codalab.org/competitions/25449  
> 论文: https://arxiv.org/abs/2007.12061

---

## 📊 概述

**NIPS Task 3&4** 是NeurIPS 2020 Education Challenge中使用的数据集，专门用于Knowledge Tracing任务。

- **全称**: NeurIPS 2020 Education Challenge - Task 3 & 4
- **数据来源**: Eedi平台（英国在线教育平台）
- **任务**: 预测学生答题正确率

---

## 🔍 数据集结构

### 主要文件

根据预处理代码，NIPS Task 3&4需要以下文件：

```
nips_task34/
├── train_task_3_4.csv          # 主要训练数据
└── metadata/
    ├── answer_metadata_task_3_4.csv      # 答题元数据（包含时间戳）
    ├── question_metadata_task_3_4.csv    # 题目元数据（包含subject）
    ├── student_metadata_task_3_4.csv     # 学生元数据
    └── subject_metadata.csv              # Subject描述（知识点层级）
```

### 数据字段

**主数据 (train_task_3_4.csv)**:
- `UserId`: 学生ID
- `QuestionId`: 题目ID
- `AnswerId`: 答题记录ID
- `IsCorrect`: 是否答对 (0/1)

**Metadata**:
- `answer_metadata`: 包含 `DateAnswered`（答题时间）
- `question_metadata`: 包含 `SubjectId`（知识点列表）
- `subject_metadata`: 包含 `SubjectId`, `Name`, `Level`（知识点层级）

---

## ✅ Concept描述情况

### 有完整的Concept（Subject）描述！

**NIPS Task 3&4 提供了完整的知识点（Subject）层级结构：**

根据预处理代码和论文：

1. **使用Level 3的Subjects作为Concepts**
   - Subject有多个层级（Level 1, 2, 3...）
   - Level 3是最细粒度的知识点
   - 每个题目可能关联多个Level 3 subjects

2. **Subjects有文字描述**
   - 每个Subject都有 `Name` 字段
   - 例如（基于Eedi平台）：
     - "Fractions"（分数）
     - "Algebra"（代数）
     - "Geometry"（几何）
     - "Probability"（概率）
     - 等等...

3. **层级结构**
   ```
   Level 1: 大类（如 Mathematics）
     └── Level 2: 中类（如 Number, Algebra, Geometry）
         └── Level 3: 细类（如 Fractions, Decimals, Linear Equations）
   ```

### Concept处理方式

在预处理中：
```python
# 只保留Level 3的subjects
keep_subject_ids = set(df_subject[df_subject['Level']==3]['SubjectId'])
df_question['SubjectId_level3'] = df_question['SubjectId'].apply(
    lambda x: set(eval(x)) & keep_subject_ids
)
```

- 每个题目可能有多个Level 3 subjects
- 存储格式: `SubjectId_level3_str` = "subject1_subject2_subject3"
- pykt会处理多concept的情况

---

## 📊 数据集统计

根据预处理代码的输出信息：

预处理会显示：
- 学生数 (`Num of student`)
- 题目数 (`Num of question`)
- 知识点数 (`Num of knowledge`)

**特点**:
- ✅ 有时间戳（`answer_timestamp`）
- ✅ 有concept描述（Subject names）
- ✅ 有层级结构（Subject hierarchy）
- ✅ 支持多concept题目

---

## 🔄 与其他数据集对比

| 数据集 | Concept数量 | 有文字描述 | 描述类型 | 特殊特性 |
|--------|-------------|-----------|----------|----------|
| **NIPS Task 3&4** | Level 3 subjects数量（需查看metadata） | ✅ 是 | 英文subject名称 + 层级结构 | 多concept题目、层级结构 |
| ASSISTments2017 | 102 | ✅ 是 | 英文skill名称 | 单concept题目 |
| EdNet | 188 | ❌ 否 | 仅数字ID | 单concept题目 |

---

## 💡 如何使用NIPS Task 3&4

### 1. 下载数据

访问官方网站下载：
```
https://competitions.codalab.org/competitions/25449
```

需要注册比赛才能下载数据。

### 2. 数据准备

将数据放置在以下结构：
```bash
/mnt/localssd/pykt-toolkit/data/nips_task34/
├── train_task_3_4.csv
└── metadata/
    ├── answer_metadata_task_3_4.csv
    ├── question_metadata_task_3_4.csv
    ├── student_metadata_task_3_4.csv
    └── subject_metadata.csv
```

### 3. 数据预处理

```bash
cd /mnt/localssd/pykt-toolkit/examples
source activate pykt
python data_preprocess.py --dataset_name nips_task34
```

### 4. 模型训练

```bash
# 使用LPKT模型
python wandb_lpkt_train.py --dataset_name=nips_task34 --use_wandb=1
```

---

## 📝 Concept描述使用

### 查看Subject描述

```python
import pandas as pd

# 读取subject metadata
subject_df = pd.read_csv('data/nips_task34/metadata/subject_metadata.csv')

# 查看Level 3的subjects
level3_subjects = subject_df[subject_df['Level'] == 3]
print(level3_subjects[['SubjectId', 'Name', 'Level']])
```

### 在结果中使用

```python
# 读取keyid2idx.json（预处理后生成）
import json
with open('data/nips_task34/keyid2idx.json', 'r') as f:
    keyid2idx = json.load(f)

# Subject ID到subject名称的映射
# 需要结合subject_metadata.csv使用
subject_metadata = pd.read_csv('data/nips_task34/metadata/subject_metadata.csv')
subject_dict = dict(zip(subject_metadata['SubjectId'], subject_metadata['Name']))

# 获取concept名称
concept_id_str = "123_456"  # 可能包含多个subject
subject_ids = concept_id_str.split('_')
concept_names = [subject_dict.get(int(sid), f"Subject {sid}") for sid in subject_ids]
print(f"Concept: {' & '.join(concept_names)}")
```

---

## 🎯 NIPS Task 3&4 的优势

### 相比其他数据集

✅ **优势**:
1. **完整的层级结构**
   - 3层knowledge hierarchy
   - 便于多粒度分析

2. **Subject有文字描述**
   - 来自Eedi平台的真实教育场景
   - 英国国家课程标准

3. **多concept支持**
   - 一个题目可以测试多个knowledge points
   - 更真实的教育场景

4. **丰富的metadata**
   - 学生信息
   - 题目信息
   - 时间戳

5. **官方benchmark**
   - NeurIPS竞赛数据
   - 有官方baseline和评估标准

⚠️ **局限**:
1. 需要注册比赛账号才能下载
2. 数据结构相对复杂（需要合并多个文件）
3. 多concept处理较复杂

---

## 📚 参考资料

### 官方资源

1. **竞赛网站**: 
   - https://competitions.codalab.org/competitions/25449

2. **论文**:
   - NeurIPS 2020 Education Challenge
   - https://arxiv.org/abs/2007.12061

3. **Eedi平台**:
   - 数据来源平台
   - https://eedi.com

### pykt-toolkit支持

- **预处理脚本**: `/mnt/localssd/pykt-toolkit/pykt/preprocess/nips_task34_preprocess.py`
- **数据配置**: 在 `data_preprocess.py` 中已包含
- **支持的模型**: 所有pykt支持的模型都可以使用

---

## 🔧 当前环境状态

### 检查数据是否可用

```bash
# 检查数据目录
ls -la /mnt/localssd/pykt-toolkit/data/ | grep nips

# 如果没有输出，说明数据尚未下载
```

**当前状态**: ⚠️ 数据尚未下载到环境中

### 下载和准备数据

如需使用NIPS Task 3&4数据集：

1. 访问竞赛网站注册并下载数据
2. 解压到 `/mnt/localssd/pykt-toolkit/data/nips_task34/`
3. 运行预处理脚本

---

## 📊 三个数据集对比总结

| 特性 | EdNet | ASSISTments2017 | NIPS Task 3&4 |
|------|-------|-----------------|---------------|
| **Concept描述** | ❌ 无 | ✅ 有 | ✅ 有（带层级） |
| **Concept数量** | 188 | 102 | Level 3数量（需查看） |
| **多Concept题目** | ❌ 否 | ❌ 否 | ✅ 是 |
| **时间戳** | ✅ 有 | ✅ 有 | ✅ 有 |
| **数据规模** | 大 (4,687学生) | 中 (1,708学生) | 需查看 |
| **下载难度** | 容易 | 容易 | 需注册 |
| **结果可解释性** | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

**NIPS Task 3&4 在concept描述方面最丰富，支持层级结构分析！**

---

## 💡 建议

### 对于研究

1. **如果看重concept描述**:
   - 首选: NIPS Task 3&4（有层级结构）
   - 次选: ASSISTments2017（简单清晰）

2. **如果看重数据规模**:
   - 首选: EdNet
   - 但需要接受concept无描述

3. **如果研究多concept题目**:
   - 必须使用: NIPS Task 3&4
   - 其他数据集不支持

### 对于Forgetting Score分析

NIPS Task 3&4特别适合：
- 可以分析不同层级knowledge的遗忘
- 可以研究多concept题目的遗忘模式
- 有完整的concept名称，结果易于解释

例如：
- "学生在**Fractions** (分数) 上的遗忘分数为0.65"
- "Level 2概念**Algebra**下的遗忘分数分布"

---

**生成时间**: 2025-10-19  
**基于**: pykt-toolkit源代码分析  
**数据集状态**: 需要手动下载

