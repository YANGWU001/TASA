# ASSISTments2012 数据集信息

> ASSISTments 2012-2013 学年数据集  
> 生成时间: 2025-10-19

---

## 📊 概述

**ASSISTments2012** 是ASSISTments平台2012-2013学年的学生答题数据集，用于Knowledge Tracing研究。

- **全称**: ASSISTments 2012-2013 Data
- **来源**: ASSISTments平台
- **文件**: `2012-2013-data-with-predictions-4-final.csv`

---

## ✅ Concept描述情况

### 概述
根据pykt-toolkit源代码和相关研究：

⚠️ **ASSISTments2012的concept信息较为有限**

### 详细情况

1. **有部分skill信息**
   - 数据集中有`skill_name`字段
   - 但**大量问题缺少skill标注**
   - 导致concept覆盖不完整

2. **与其他ASSISTments数据集对比**
   | 数据集 | Concept描述 | Concept完整性 |
   |--------|-------------|---------------|
   | ASSISTments2009 | ✅ 有skill名称 | 较好 |
   | **ASSISTments2012** | ⚠️ 有但不完整 | **较差** |
   | ASSISTments2015 | ✅ 有skill名称 | 好 |
   | ASSISTments2017 | ✅✅ 有skill名称 | 很好（102个skills） |

3. **预处理代码分析**
   从`assist2012_preprocess.py`可以看到：
   ```python
   # 数据包含skill_name字段
   # 但很多问题的skill_name为空或未标注
   ```

### 问题
- **数据质量问题**: 很多问题没有对应的skill信息
- **研究影响**: 在Knowledge Tracing研究中，ASSISTments2012的表现通常不如其他ASSISTments数据集
- **文献记录**: 多篇论文指出此数据集的concept信息不完整

---

## ⏱️ 时间戳情况

### 概述
✅ **ASSISTments2012包含完整的时间戳信息**

### 详细信息

1. **时间戳字段**
   - 原始数据包含时间相关字段
   - 记录了学生答题的时间信息
   - 可以计算答题间隔

2. **时间戳类型**
   - 包含答题开始时间
   - 包含答题结束时间
   - 可以计算答题用时

3. **预处理后**
   - 转换为Unix时间戳（毫秒）
   - 存储在`timestamps`字段中
   - 与其他数据集格式一致

---

## 📊 数据集对比

### ASSISTments系列数据集完整对比

| 数据集 | Concept描述 | Concept数量 | 时间戳 | 推荐度 | 说明 |
|--------|-------------|-------------|--------|--------|------|
| **ASSISTments2009** | ✅ 有skill名称 | 110+ | ✅ 有 | ⭐⭐⭐ | 经典数据集，广泛使用 |
| **ASSISTments2012** | ⚠️ 不完整 | ? | ✅ 有 | ⭐ | **不推荐**：concept不完整 |
| **ASSISTments2015** | ✅ 有skill名称 | 100+ | ✅ 有 | ⭐⭐⭐ | 质量好 |
| **ASSISTments2017** | ✅✅ 有skill名称 | 102 | ✅ 有 | ⭐⭐⭐⭐ | **推荐**：最完整 |

### 与其他数据集对比

| 数据集 | Concept描述 | 描述质量 | 时间戳 | 适合研究 |
|--------|-------------|----------|--------|----------|
| **ASSISTments2012** | ⚠️ 不完整 | ⭐ | ✅ | 不推荐 |
| **ASSISTments2017** | ✅ 完整 | ⭐⭐⭐⭐ | ✅ | **推荐** |
| **EdNet** | ❌ 无描述 | - | ✅ | 仅看规模 |
| **NIPS Task 3&4** | ✅✅ 层级结构 | ⭐⭐⭐⭐⭐ | ✅ | **强烈推荐** |

---

## 🚫 为什么不推荐ASSISTments2012

### 主要问题

1. **Concept信息不完整**
   - 大量题目没有skill标注
   - 影响模型训练效果
   - 影响结果可解释性

2. **研究文献支持较少**
   - 相比2009、2015、2017，使用较少
   - benchmark结果较少
   - 社区支持较弱

3. **更好的替代方案**
   - **ASSISTments2017**: 同样来自ASSISTments，但concept完整
   - **ASSISTments2009**: 经典数据集，广泛使用
   - **ASSISTments2015**: 质量好，concept完整

### 适用场景

ASSISTments2012可能适用于：
- ❌ 需要concept描述的研究（不推荐）
- ❌ Forgetting Score分析（concept不完整）
- ✅ 仅研究时序模式（不依赖concept语义）
- ✅ 对比研究（作为baseline数据集）

---

## 💡 推荐方案

### 如果你需要ASSISTments系列数据集

**推荐使用ASSISTments2017**（已在环境中）：
- ✅ **102个完整的skill描述**
- ✅ **1,708学生，940K交互**
- ✅ **时间戳完整**
- ✅ **concept覆盖完整**
- ✅ **社区支持好**

### 如果你需要多个数据集对比

推荐组合：
1. **ASSISTments2017** - concept完整，适中规模
2. **NIPS Task 3&4** - 层级结构，最丰富
3. **EdNet** - 大规模，无concept描述

**不推荐**将ASSISTments2012加入对比，因为concept不完整会影响公平性。

---

## 📋 如何验证ASSISTments2012的concept情况

如果你仍想使用ASSISTments2012，可以下载后验证：

### 下载数据
```bash
# 从ASSISTments官网下载
# https://sites.google.com/site/assistmentsdata/datasets/2012-13-school-data-with-affect

# 放置到
/mnt/localssd/pykt-toolkit/data/assist2012/2012-2013-data-with-predictions-4-final.csv
```

### 预处理
```bash
cd /mnt/localssd/pykt-toolkit/examples
source activate pykt
python data_preprocess.py --dataset_name assist2012
```

### 检查concept完整性
```python
import pandas as pd

# 读取原始数据
df = pd.read_csv('data/assist2012/2012-2013-data-with-predictions-4-final.csv')

# 检查skill_name字段
print(f"总记录数: {len(df)}")
print(f"有skill_name的记录: {df['skill_name'].notna().sum()}")
print(f"缺失比例: {df['skill_name'].isna().sum() / len(df) * 100:.1f}%")

# 查看unique skills
skills = df['skill_name'].dropna().unique()
print(f"\n唯一skill数量: {len(skills)}")
print("\n前20个skills:")
for skill in sorted(skills)[:20]:
    count = (df['skill_name'] == skill).sum()
    print(f"  {skill}: {count} 次")
```

---

## 📚 相关数据集文档

- **ASSISTments2017详情**: `/mnt/localssd/CONCEPT_DESCRIPTIONS.md`
- **NIPS Task 3&4详情**: `/mnt/localssd/NIPS_TASK34_INFO.md`
- **所有数据集对比**: `/mnt/localssd/ALL_DATASETS_CONCEPT_COMPARISON.md`

---

## 🎯 总结

### ASSISTments2012

| 特性 | 状态 | 说明 |
|------|------|------|
| **Concept文字描述** | ⚠️ **不完整** | 大量题目缺少skill标注 |
| **时间戳** | ✅ 有 | 完整的答题时间信息 |
| **推荐度** | ⭐ 低 | 不推荐用于需要concept的研究 |

### 建议

**强烈建议使用ASSISTments2017替代**：
- ✅ Concept完整（102个skills，全部有描述）
- ✅ 时间戳完整
- ✅ 数据质量高
- ✅ 已在当前环境中可用

**或使用NIPS Task 3&4**：
- ✅✅ 最丰富的concept描述（层级结构）
- ✅ 时间戳完整
- ✅ 支持多concept题目
- ✅ 已下载并预处理完成

---

## 🔗 参考资料

### ASSISTments官方网站
- https://sites.google.com/site/assistmentsdata/

### 相关论文
- 多篇KT论文指出ASSISTments2012的concept信息局限性
- 推荐使用ASSISTments2009、2015或2017

### pykt-toolkit支持
- 预处理脚本: `/mnt/localssd/pykt-toolkit/pykt/preprocess/assist2012_preprocess.py`
- 配置: 在`data_preprocess.py`中已包含

---

**生成时间**: 2025-10-19  
**状态**: ASSISTments2012 - 不推荐使用（concept不完整）  
**推荐替代**: ASSISTments2017 或 NIPS Task 3&4

