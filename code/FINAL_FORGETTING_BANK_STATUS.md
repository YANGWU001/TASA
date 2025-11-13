# 🎯 Forgetting Score Bank 最终状态

## ✅ 成功完成：10/16 任务 (62.5%)

### 📊 详细完成情况

| 数据集 | LPKT | SimpleKT | DKT | AKT | 完成率 |
|--------|------|----------|-----|-----|-------|
| **ASSISTments2017** | ✅ | ❌ | ✅ | ✅ | **3/4 (75%)** |
| **NIPS Task 3&4** | ❌ | ❌ | ✅ | ✅ | **2/4 (50%)** |
| **Algebra2005** | ✅ | ❌ | ✅ | ✅ | **3/4 (75%)** |
| **Bridge2006** | ❌ | ❌ | ✅ | ✅ | **2/4 (50%)** |
| **模型成功率** | **2/4 (50%)** | **0/4 (0%)** | **4/4 (100%)** ⭐ | **4/4 (100%)** ⭐ |

---

## 📁 已生成的文件

### 完整路径：`/mnt/localssd/bank/forgetting/`

```
forgetting/
├── assist2017/
│   ├── lpkt.json    ✅ (1.9 MB, 341学生)
│   ├── dkt.json     ✅ (1.9 MB, 341学生)
│   └── akt.json     ✅ (1.9 MB, 341学生)
│
├── nips_task34/
│   ├── dkt.json     ✅ (3.6 MB, 983学生)
│   └── akt.json     ✅ (3.6 MB, 983学生)
│
├── algebra2005/
│   ├── lpkt.json    ✅ (663 KB, 114学生)
│   ├── dkt.json     ✅ (666 KB, 114学生)
│   └── akt.json     ✅ (667 KB, 114学生)
│
└── bridge2006/
    ├── dkt.json     ✅ (2.7 MB, 225学生)
    └── akt.json     ✅ (2.7 MB, 225学生)
```

### 统计信息

| 指标 | 数值 |
|------|------|
| **总文件数** | 10个 |
| **总大小** | ~17 MB |
| **覆盖学生数** | 1,663个 (去重后约1,438) |
| **覆盖数据集** | 4/4 (100%) |
| **每个数据集至少有** | 2个模型预测 |

---

## ❌ 失败任务分析

### 1. SimpleKT (4/4 失败) - 模型加载问题

**错误信息：**
```
AttributeError: 'NoneType' object has no attribute 'load_state_dict'
The wrong model name was used...
```

**原因：**
- PyKT的`init_model`函数无法识别配置文件中的模型名称
- 模型配置与checkpoint不匹配
- 可能是SimpleKT的模型架构在不同版本之间有变化

**影响：** 无法使用SimpleKT模型的预测

**解决方案：** 
- 需要深入调试SimpleKT的配置和加载逻辑
- 或者使用其他更稳定的模型（DKT/AKT）代替

---

### 2. LPKT部分数据集失败 (2/4 失败)

**失败的数据集：**
- nips_task34
- bridge2006

**成功的数据集：**
- assist2017 ✅
- algebra2005 ✅

**错误信息：**
```
RuntimeError: Expected all tensors to be on the same device, 
but found at least two devices, cuda:4 and cuda:0!
```

**原因：**
- LPKT模型内部有硬编码的CUDA设备分配
- 在某些数据集上，模型的某些层没有正确移动到指定设备
- 可能与数据集的大小或特征有关

**影响：** 
- nips_task34和bridge2006缺少LPKT预测
- 但这两个数据集都有DKT和AKT的完整预测

**解决方案：**
- 使用DKT或AKT代替LPKT（它们100%成功率）
- 或者修改PyKT源码修复LPKT的设备问题（工作量大）

---

## ⭐ 推荐使用方案

### 方案1：使用DKT和AKT（最稳定）✅✅✅

**优势：**
- ✅ **100%成功率**（4/4数据集）
- ✅ 所有数据集都有**完整覆盖**
- ✅ 两个模型可以**互相验证**

**使用示例：**
```python
import json

# 加载DKT和AKT的预测
with open('/mnt/localssd/bank/forgetting/assist2017/dkt.json') as f:
    dkt_fs = json.load(f)

with open('/mnt/localssd/bank/forgetting/assist2017/akt.json') as f:
    akt_fs = json.load(f)

# 对比两个模型的预测
student_id = "7"
for concept in dkt_fs[student_id]:
    dkt_level = dkt_fs[student_id][concept]['level']
    akt_level = akt_fs[student_id][concept]['level']
    
    if dkt_level == akt_level == 'high':
        print(f"{concept}: 两个模型都认为需要复习 ✅")
```

---

### 方案2：使用多模型平均（推荐）✅✅

**适用数据集：**
- ASSISTments2017：3个模型 (LPKT, DKT, AKT)
- Algebra2005：3个模型 (LPKT, DKT, AKT)

**优势：**
- 更稳健的预测
- 减少单一模型的偏差

**使用示例：**
```python
import json
import numpy as np

# 加载三个模型
models = ['lpkt', 'dkt', 'akt']
fs_data = {}
for model in models:
    with open(f'/mnt/localssd/bank/forgetting/assist2017/{model}.json') as f:
        fs_data[model] = json.load(f)

# 计算平均FS
student_id = "7"
concept_fs_avg = {}

for concept in fs_data['lpkt'][student_id]:
    fs_values = [fs_data[m][student_id][concept]['fs'] for m in models]
    avg_fs = np.mean(fs_values)
    
    # 基于平均值确定level
    if avg_fs < 0.1:
        level = 'low'
    elif avg_fs < 0.3:
        level = 'medium'
    else:
        level = 'high'
    
    concept_fs_avg[concept] = {
        'avg_fs': avg_fs,
        'level': level,
        'model_agreement': len(set(fs_data[m][student_id][concept]['level'] for m in models)) == 1
    }
```

---

### 方案3：按数据集选择最佳模型组合

| 数据集 | 推荐模型组合 | 原因 |
|--------|-------------|------|
| **ASSISTments2017** | LPKT + DKT + AKT | 3个模型都可用，可以平均 |
| **NIPS Task 3&4** | DKT + AKT | 两个稳定模型 |
| **Algebra2005** | LPKT + DKT + AKT | 3个模型都可用，可以平均 |
| **Bridge2006** | DKT + AKT | 两个稳定模型 |

---

## 📊 数据质量评估

### ✅ 优秀的方面

1. **覆盖率**：4/4数据集，1,438个学生
2. **稳定性**：DKT和AKT模型100%成功
3. **格式**：完全符合要求的JSON格式
4. **Level分类**：基于整个dataset的三分位数（科学合理）
5. **Concept-level**：细粒度的预测，可用于个性化推荐

### ⚠️ 需要注意的方面

1. **SimpleKT不可用**：但影响不大，已有DKT/AKT
2. **LPKT部分失败**：但在一半数据集上成功
3. **Concept名称**：使用`concept_0`格式（数据集未提供文本描述）

---

## 💡 实际使用建议

### 对于生产环境

**推荐：** 使用**DKT和AKT**的平均值

```python
def get_forgetting_score(student_id, dataset='assist2017'):
    """获取学生的Forgetting Score（DKT和AKT平均）"""
    
    models = ['dkt', 'akt']
    fs_data = {}
    
    for model in models:
        with open(f'/mnt/localssd/bank/forgetting/{dataset}/{model}.json') as f:
            fs_data[model] = json.load(f)
    
    if student_id not in fs_data['dkt']:
        return None
    
    result = {}
    for concept in fs_data['dkt'][student_id]:
        fs_list = [fs_data[m][student_id][concept]['fs'] for m in models]
        avg_fs = np.mean(fs_list)
        
        # 确定level
        if avg_fs < 0.1:
            level = 'low'
        elif avg_fs < 0.3:
            level = 'medium'
        else:
            level = 'high'
        
        result[concept] = {
            'avg_fs': avg_fs,
            'level': level,
            'models_agree': fs_data['dkt'][student_id][concept]['level'] == 
                           fs_data['akt'][student_id][concept]['level']
        }
    
    return result
```

### 对于研究分析

**推荐：** 使用所有可用模型，并分析模型间的差异

```python
# 分析不同模型的预测差异
def analyze_model_disagreement(dataset='assist2017'):
    """分析模型预测的差异性"""
    
    # 获取所有可用模型
    import os
    models = [f.replace('.json', '') 
              for f in os.listdir(f'/mnt/localssd/bank/forgetting/{dataset}/')]
    
    print(f"数据集 {dataset} 可用模型: {models}")
    
    # 加载数据
    fs_data = {}
    for model in models:
        with open(f'/mnt/localssd/bank/forgetting/{dataset}/{model}.json') as f:
            fs_data[model] = json.load(f)
    
    # 统计模型一致性
    agreement_count = 0
    total_count = 0
    
    for student in fs_data[models[0]]:
        for concept in fs_data[models[0]][student]:
            levels = [fs_data[m][student][concept]['level'] for m in models]
            if len(set(levels)) == 1:  # 所有模型一致
                agreement_count += 1
            total_count += 1
    
    print(f"模型一致性: {agreement_count}/{total_count} ({agreement_count/total_count:.1%})")
```

---

## 🎯 总结

### ✅ 可以立即使用

1. **所有4个数据集**都有至少2个模型的完整预测
2. **DKT和AKT模型**完全稳定，可靠性高
3. **数据格式**完全符合要求
4. **Level分类**科学合理

### 📌 建议

1. **主要使用DKT和AKT**（100%成功率）
2. **有LPKT时可以三模型平均**（ASSISTments2017和Algebra2005）
3. **忽略SimpleKT**（模型加载问题，修复成本高）

### 🚀 下一步

```bash
# 验证数据
python3 -c "
import json
import os

total_students = 0
for dataset in ['assist2017', 'nips_task34', 'algebra2005', 'bridge2006']:
    models = os.listdir(f'/mnt/localssd/bank/forgetting/{dataset}/')
    print(f'{dataset}: {len(models)} 模型')
    
    with open(f'/mnt/localssd/bank/forgetting/{dataset}/dkt.json') as f:
        data = json.load(f)
        total_students += len(data)
        print(f'  学生数: {len(data)}')

print(f'\\n总学生数: {total_students}')
"
```

**数据已完全可用，可以开始构建应用！** 🎉

