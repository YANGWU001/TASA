# Overall.json 使用指南

## 📊 概述

`overall.json` 整合了所有KT方法的forgetting score数据，以 **`history.json`** 作为基准，包含所有模型的 `s_tc` 和 `fs` 值，方便对比和分析。

## 📁 文件位置

```
/mnt/localssd/bank/forgetting/{dataset}/overall.json
```

可用数据集：
- `assist2017`
- `nips_task34`
- `algebra2005`
- `bridge2006`

## 📋 数据结构

```json
{
  "student_id": {
    "concept_text": {
      "methods": {
        "history": {
          "s_tc": 0.6667,    // 历史accuracy
          "fs": 0.0025       // forgetting score
        },
        "lpkt": {
          "s_tc": 0.7069,    // LPKT模型预测
          "fs": 0.0769
        },
        "dkt": {
          "s_tc": 0.7507,    // DKT模型预测
          "fs": 0.0654
        },
        "akt": {
          "s_tc": 0.8680,    // AKT模型预测
          "fs": 0.0346
        },
        "simplekt": {
          "s_tc": 0.6667,    // SimpleKT (历史accuracy)
          "fs": 0.0025
        }
      },
      "delta_t": 31.35,           // 时间差（分钟）
      "tau": 4219.2,              // tau参数（分钟）
      "last_response": 1,         // 最后一次回答（0/1）
      "num_attempts": 13,         // 总交互次数
      "level": "high"             // forgetting level
    }
  }
}
```

## 📊 统计信息

### 文件大小和条目数

| 数据集 | 文件大小 | 学生数 | Concept条目 |
|--------|----------|--------|-------------|
| Assist2017 | 33.0 MB | 1,708 | 59,379 |
| NIPS Task 3&4 | 60.8 MB | 4,918 | 113,553 |
| Algebra2005 | 11.2 MB | 574 | 21,894 |
| Bridge2006 | 43.8 MB | 1,138 | 85,771 |

### 方法覆盖率

#### Assist2017
- **History**: 59,379 (100.0%) ✅
- **SimpleKT**: 59,379 (100.0%) ✅
- **LPKT**: 37,564 (63.3%)
- **DKT**: 37,564 (63.3%)
- **AKT**: 37,564 (63.3%)

#### NIPS Task 3&4
- **History**: 113,553 (100.0%) ✅
- **SimpleKT**: 113,553 (100.0%) ✅
- **LPKT**: 66,299 (58.4%)
- **DKT**: 74,275 (65.4%)
- **AKT**: 74,275 (65.4%)

#### Algebra2005
- **History**: 21,894 (100.0%) ✅
- **SimpleKT**: 21,894 (100.0%) ✅
- **LPKT**: 5,037 (23.0%) ⚠️
- **DKT**: 14,213 (64.9%)
- **AKT**: 14,213 (64.9%)

#### Bridge2006
- **History**: 85,771 (100.0%) ✅
- **SimpleKT**: 85,771 (100.0%) ✅
- **LPKT**: 41,085 (47.9%)
- **DKT**: 45,641 (53.2%)
- **AKT**: 45,641 (53.2%)

## 💡 使用示例

### 1. 读取数据

```python
import json

# 加载overall.json
with open('/mnt/localssd/bank/forgetting/assist2017/overall.json') as f:
    data = json.load(f)

# 获取某个学生的数据
student_id = '1365'
student_data = data[student_id]

# 获取某个concept的数据
concept_text = 'concept_7'
concept_data = student_data[concept_text]

# 查看所有方法的预测
for method, values in concept_data['methods'].items():
    print(f"{method}: s_tc={values['s_tc']:.4f}, fs={values['fs']:.4f}")
```

### 2. 对比不同模型的预测效果

```python
import pandas as pd

# 对比history和各个KT模型的s_tc差异
differences = []

for uid, concepts in data.items():
    for concept_text, concept_data in concepts.items():
        methods = concept_data['methods']
        
        if 'history' in methods and 'lpkt' in methods:
            history_stc = methods['history']['s_tc']
            lpkt_stc = methods['lpkt']['s_tc']
            
            differences.append({
                'uid': uid,
                'concept': concept_text,
                'history_stc': history_stc,
                'lpkt_stc': lpkt_stc,
                'diff': lpkt_stc - history_stc
            })

df = pd.DataFrame(differences)
print(f"LPKT平均预测偏差: {df['diff'].mean():.4f}")
print(f"LPKT预测标准差: {df['diff'].std():.4f}")
```

### 3. 分析模型一致性

```python
# 计算不同模型之间的相关性
import numpy as np
from scipy.stats import pearsonr

method_pairs = [('history', 'lpkt'), ('history', 'dkt'), ('history', 'akt')]
correlations = []

for method1, method2 in method_pairs:
    stc1_list = []
    stc2_list = []
    
    for uid, concepts in data.items():
        for concept_text, concept_data in concepts.items():
            methods = concept_data['methods']
            
            if method1 in methods and method2 in methods:
                stc1_list.append(methods[method1]['s_tc'])
                stc2_list.append(methods[method2]['s_tc'])
    
    if len(stc1_list) > 0:
        corr, pval = pearsonr(stc1_list, stc2_list)
        correlations.append({
            'pair': f"{method1} vs {method2}",
            'correlation': corr,
            'p_value': pval
        })

for c in correlations:
    print(f"{c['pair']}: r={c['correlation']:.4f} (p={c['p_value']:.4e})")
```

### 4. 筛选高遗忘风险的学生-concept组合

```python
# 找出不同模型都预测为高遗忘的cases
high_forgetting_cases = []

for uid, concepts in data.items():
    for concept_text, concept_data in concepts.items():
        methods = concept_data['methods']
        
        # 检查所有模型的fs是否都超过阈值
        fs_values = [methods[m]['fs'] for m in methods.keys()]
        
        if all(fs > 0.5 for fs in fs_values):  # 所有模型都预测高遗忘
            high_forgetting_cases.append({
                'uid': uid,
                'concept': concept_text,
                'avg_fs': np.mean(fs_values),
                'num_attempts': concept_data['num_attempts']
            })

print(f"发现 {len(high_forgetting_cases)} 个高遗忘风险cases")
```

### 5. 评估模型预测准确性

```python
# 使用last_response作为ground truth，评估模型预测
from sklearn.metrics import roc_auc_score

for method in ['history', 'lpkt', 'dkt', 'akt']:
    predictions = []
    ground_truth = []
    
    for uid, concepts in data.items():
        for concept_text, concept_data in concepts.items():
            if method in concept_data['methods']:
                predictions.append(concept_data['methods'][method]['s_tc'])
                ground_truth.append(concept_data['last_response'])
    
    if len(predictions) > 0:
        auc = roc_auc_score(ground_truth, predictions)
        print(f"{method}: AUC = {auc:.4f}")
```

## 🎯 使用场景

### 1. 模型对比研究
- 对比不同KT模型的预测准确性
- 分析模型over/under-prediction的模式
- 评估模型的一致性和可靠性

### 2. 个性化学习推荐
- 结合多个模型的预测做集成决策
- 识别所有模型都认为需要复习的concepts
- 根据预测差异识别不确定性高的cases

### 3. 遗忘模式分析
- 对比历史accuracy与模型预测的差异
- 分析时间因素（delta_t）对遗忘的影响
- 研究不同concepts的遗忘特征

### 4. 模型优化
- 识别模型预测失败的cases
- 分析预测偏差与学生特征的关系
- 优化模型参数和架构

## ⚠️ 注意事项

1. **覆盖率差异**: LPKT/DKT/AKT的覆盖率低于100%，因为它们只保留了至少有2次交互的student-concept组合

2. **History vs SimpleKT**: 两者都使用历史accuracy，理论上应该完全一致

3. **LPKT数据问题**: 某些数据集的LPKT使用了Question ID而非Concept ID，覆盖率特别低

4. **数据一致性**: 共同字段（delta_t, tau, last_response, num_attempts）都来自history，保证了基准的一致性

## 📈 推荐分析流程

1. **加载overall.json** → 获取完整的多模型数据
2. **筛选完整数据** → 只使用所有模型都有数据的student-concept组合
3. **计算模型指标** → AUC, 相关性, MAE等
4. **可视化对比** → 绘制散点图、箱线图等
5. **深度分析** → 按student类型、concept类型、time因素等分层分析

## ✨ 优势总结

- ✅ **一站式数据源**: 所有模型的数据集中在一个文件
- ✅ **完整的基准**: 以history为基准，保证100%覆盖
- ✅ **方便对比**: 同一student-concept的所有模型预测并列
- ✅ **标准格式**: 统一的JSON结构，易于解析和分析
- ✅ **丰富信息**: 包含预测值、时间、交互次数等多维度信息

Overall.json是进行KT模型对比和集成学习的最佳数据源！

