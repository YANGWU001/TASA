# Forgetting Score 数据快速参考

## 📊 数据文件总览

每个数据集包含6个JSON文件：

| 文件 | 说明 | Tau | Level计算 |
|------|------|-----|-----------|
| **history.json** | 基于历史accuracy | 中位数 | 基于自身FS分布 |
| **lpkt.json** | LPKT模型预测 | 中位数 | 基于自身FS分布 |
| **dkt.json** | DKT模型预测 | 中位数 | 基于自身FS分布 |
| **akt.json** | AKT模型预测 | 中位数 | 基于自身FS分布 |
| **simplekt.json** | SimpleKT模型预测 | 中位数 | 基于自身FS分布 |
| **overall.json** ⭐ | 整合所有方法 | 中位数 | 每个方法独立 |

## ⭐ 推荐使用：overall.json

**为什么选择overall.json？**
- ✅ 一个文件包含所有5个方法的数据
- ✅ 使用优化的tau（中位数）重新计算了所有FS
- ✅ 每个方法有独立的level判断
- ✅ 便于横向对比不同模型

## 📋 数据格式对比

### 单方法文件 (history.json, lpkt.json等)
```json
{
  "student_id": {
    "concept_text": {
      "s_tc": 0.6667,
      "fs": 0.3293,
      "delta_t": 1881.0,
      "tau": 23.0,
      "level": "medium",
      "last_response": 1,
      "num_attempts": 13
    }
  }
}
```

### overall.json ⭐
```json
{
  "student_id": {
    "concept_text": {
      "methods": {
        "history": {"s_tc": 0.6667, "fs": 0.3293, "level": "medium"},
        "lpkt": {"s_tc": 0.7069, "fs": 0.2896, "level": "medium"},
        "dkt": {"s_tc": 0.7507, "fs": 0.2463, "level": "medium"},
        "akt": {"s_tc": 0.8680, "fs": 0.1304, "level": "medium"},
        "simplekt": {"s_tc": 0.6667, "fs": 0.3293, "level": "high"}
      },
      "delta_t": 1881.0,
      "tau": 23.0,
      "last_response": 1,
      "num_attempts": 13
    }
  }
}
```

## 🔢 关键统计

| 数据集 | 学生数 | Concepts | Tau | FS中位数(history) |
|--------|--------|----------|-----|-------------------|
| **Assist2017** | 1,708 | 59,379 | 23分钟 | 0.238 |
| **NIPS Task34** | 4,918 | 113,553 | 300分钟 | 0.051 |
| **Algebra2005** | 574 | 21,894 | 235分钟 | 0.095 |
| **Bridge2006** | 1,138 | 85,771 | 2.5分钟 | 0.050 |

## 💡 常见使用场景

### 1. 加载数据
```python
import json

# 推荐：使用overall.json
with open('/mnt/localssd/bank/forgetting/assist2017/overall.json') as f:
    data = json.load(f)

# 获取某个学生的某个concept的数据
student_data = data['1365']['concept_7']
print(student_data['methods']['lpkt']['fs'])  # LPKT的forgetting score
print(student_data['methods']['history']['level'])  # History的level
```

### 2. 对比不同模型
```python
# 对比所有模型对同一concept的预测
for method, values in student_data['methods'].items():
    print(f"{method}: FS={values['fs']:.4f}, Level={values['level']}")
```

### 3. 识别高遗忘风险
```python
# 找出所有模型都认为是"high"的cases
high_risk = []
for uid, concepts in data.items():
    for concept, info in concepts.items():
        levels = [m['level'] for m in info['methods'].values()]
        if all(l == 'high' for l in levels):
            high_risk.append((uid, concept))
```

### 4. 计算模型一致性
```python
from scipy.stats import pearsonr

# 比较history和lpkt的FS相关性
history_fs = []
lpkt_fs = []

for uid, concepts in data.items():
    for concept, info in concepts.items():
        if 'history' in info['methods'] and 'lpkt' in info['methods']:
            history_fs.append(info['methods']['history']['fs'])
            lpkt_fs.append(info['methods']['lpkt']['fs'])

corr, pval = pearsonr(history_fs, lpkt_fs)
print(f"相关系数: {corr:.4f}")
```

## 📂 文件位置

```
/mnt/localssd/bank/forgetting/
├── assist2017/
│   ├── overall.json ⭐ (37MB)
│   ├── history.json (12MB)
│   ├── lpkt.json (12MB)
│   ├── dkt.json (12MB)
│   ├── akt.json (12MB)
│   └── simplekt.json (15MB)
├── nips_task34/
│   ├── overall.json ⭐ (68MB)
│   └── ...
├── algebra2005/
│   ├── overall.json ⭐ (13MB)
│   └── ...
└── bridge2006/
    ├── overall.json ⭐ (49MB)
    └── ...
```

## ⚠️ 重要说明

1. **Tau值**: 使用delta_t的中位数，不是平均值
   - 避免极端值影响
   - 更合理地反映典型学习间隔

2. **Level定义**: 基于FS分布的三分位数
   - Low: < 33rd percentile
   - Medium: 33rd - 67th percentile
   - High: > 67th percentile
   - **每个方法独立计算！**

3. **覆盖率**: 
   - History/SimpleKT: 100%覆盖（使用历史数据）
   - LPKT/DKT/AKT: 50-65%覆盖（只包含≥2次交互的cases）

4. **数据一致性**:
   - 所有方法使用**相同的delta_t和tau**
   - FS差异仅来自**不同的s_tc预测**
   - Level是**各方法独立计算的**

## 🎯 最佳实践

1. **首选overall.json**进行多模型对比
2. 使用**history.json**作为baseline
3. **LPKT/DKT/AKT**覆盖率较低，注意missing data
4. 使用**last_response**验证预测效果
5. 考虑**集成多个模型**的预测结果

---

**详细文档**: `/mnt/localssd/OVERALL_V2_SUMMARY.md`
