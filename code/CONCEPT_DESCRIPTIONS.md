# Concept描述信息总结

> 生成时间: 2025-10-19  
> 分析工具: extract_concept_descriptions.py

---

## 📊 概述

两个数据集在concept描述方面有很大差异：

| 数据集 | Concept数量 | 有文字描述 | 描述类型 |
|--------|-------------|-----------|----------|
| **EdNet** | 188 | ❌ 否 | 仅数字ID (1-300) |
| **ASSISTments2017** | 102 | ✅ 是 | 英文skill名称 |

---

## 🔍 EdNet 数据集

### 状况

⚠️ **EdNet数据集没有提供concept的文字描述**

- Concepts只是数字ID，如: `1`, `2`, `7`, `24`, `119`, `181`...
- 这些ID对应EdNet平台内部的知识点标签
- 原始数据集未包含这些ID的含义说明
- 无法直接知道每个concept代表什么知识点

### Concept ID 示例

预处理后的映射（`keyid2idx.json`）:
```
原始Tag -> 索引
  119 -> 0
   30 -> 1
   24 -> 2
   48 -> 3
  181 -> 4
  182 -> 5
  ...
```

### 最常见的Concepts（来自训练数据统计）

根据之前的统计分析：

1. **Concept 7**: 84,785 次 (7.91%) - 最高频
2. **Concept 4**: 74,471 次 (6.95%)
3. **Concept 5**: 61,601 次 (5.75%)
4. **Concept 8**: 55,884 次 (5.22%)
5. **Concept 24**: 42,699 次 (3.99%)
6. **Concept 27**: 41,547 次 (3.88%)
7. **Concept 2**: 33,353 次 (3.11%)
8. **Concept 85**: 22,428 次 (2.09%)
9. **Concept 56**: 19,465 次 (1.82%)
10. **Concept 20**: 16,096 次 (1.50%)

### 使用建议

1. **在研究中**:
   - 直接使用 "Concept X" 来指代
   - 例如: "Concept 7 是最高频的知识点"
   
2. **如需获取描述**:
   - 联系EdNet数据集提供方
   - 查看EdNet官方文档或论文
   - 根据题目内容人工推断

3. **分析方法**:
   - 可以分析高频concept对应的题目内容
   - 通过题目关联推断concept含义
   - 使用聚类等方法分析concept之间的关系

---

## ✅ ASSISTments2017 数据集

### 状况

✅ **ASSISTments2017有完整的Skill（Concept）文字描述！**

- 每个concept都有清晰的英文名称
- 描述了具体的数学知识点
- 原始数据中的 `skill` 列包含完整描述
- 预处理时转换为数字索引，但可通过 `keyid2idx.json` 查看映射

### 最常见的20个Skills

| 排名 | 索引 | Skill名称 | 出现次数 | 比例 | 中文含义 |
|------|------|-----------|---------|------|----------|
| 1 | 21 | noskill | 78,103 | 8.28% | 无特定技能 |
| 2 | 58 | probability | 73,183 | 7.76% | 概率 |
| 3 | 14 | pattern-finding | 45,027 | 4.78% | 模式发现 |
| 4 | 5 | area | 34,308 | 3.64% | 面积 |
| 5 | 34 | equation-solving | 33,966 | 3.60% | 方程求解 |
| 6 | 33 | multiplication | 26,406 | 2.80% | 乘法 |
| 7 | 37 | inducing-functions | 24,849 | 2.64% | 函数归纳 |
| 8 | 7 | square-root | 24,487 | 2.60% | 平方根 |
| 9 | 60 | symbolization-articulation | 22,745 | 2.41% | 符号表达 |
| 10 | 12 | pythagorean-theorem | 22,104 | 2.34% | 勾股定理 |
| 11 | 10 | multiplying-decimals | 21,976 | 2.33% | 小数乘法 |
| 12 | 13 | interpreting-linear-equations | 20,166 | 2.14% | 线性方程解释 |
| 13 | 4 | reading-graph | 19,262 | 2.04% | 读图 |
| 14 | 46 | substitution | 19,227 | 2.04% | 代入法 |
| 15 | 0 | properties-of-geometric-figures | 18,626 | 1.98% | 几何图形性质 |
| 16 | 35 | discount | 18,557 | 1.97% | 折扣 |
| 17 | 2 | point-plotting | 18,054 | 1.91% | 点绘制 |
| 18 | 45 | evaluating-functions | 17,898 | 1.90% | 函数求值 |
| 19 | 25 | percent-of | 16,227 | 1.72% | 百分比 |
| 20 | 59 | combinatorics | 15,923 | 1.69% | 组合数学 |

### 完整Skills列表

所有102个skills的完整列表已保存到:
📄 **`/tmp/assistments2017_skill_descriptions.txt`**

包括：
- **几何类**: properties-of-geometric-figures, area, perimeter, pythagorean-theorem, congruence, similar-triangles 等
- **代数类**: equation-solving, algebraic-manipulation, inducing-functions, substitution, inequality-solving 等
- **数与运算**: multiplication, division, addition, subtraction, fractions, decimals 等
- **概率统计**: probability, combinatorics, mean, median, mode 等
- **其他**: pattern-finding, reading-graph, venn-diagram 等

### Concept ID 映射示例

在预处理数据中，skills被转换为数字索引：

```python
# 在模型中看到的是索引
concept_id = 58  # 对应 "probability"
concept_id = 0   # 对应 "properties-of-geometric-figures"
concept_id = 21  # 对应 "noskill"
```

可以通过 `keyid2idx.json` 中的 `concepts` 字段查看完整映射：

```json
{
  "concepts": {
    "properties-of-geometric-figures": 0,
    "sum-of-interior-angles-more-than-3-sides": 1,
    "point-plotting": 2,
    ...
    "probability": 58,
    ...
  }
}
```

### 使用建议

1. **在研究中**:
   - 可以直接使用skill的英文名称
   - 例如: "probability是最高频的skill之一"
   
2. **中文报告**:
   - 可以翻译为中文
   - 例如: "概率 (probability)" 或 "几何图形性质 (properties-of-geometric-figures)"

3. **查看映射**:
   ```bash
   # 查看完整映射
   cat /mnt/localssd/pykt-toolkit/data/assist2017/keyid2idx.json | python -m json.tool | less
   
   # 或查看保存的描述文件
   cat /tmp/assistments2017_skill_descriptions.txt
   ```

---

## 🔄 在代码中使用Concept描述

### ASSISTments2017 - 获取concept名称

```python
import json

# 读取映射
with open('/mnt/localssd/pykt-toolkit/data/assist2017/keyid2idx.json', 'r') as f:
    keyid2idx = json.load(f)

# 创建反向映射
concepts_map = keyid2idx['concepts']
idx_to_concept = {v: k for k, v in concepts_map.items()}

# 使用
concept_idx = 58
concept_name = idx_to_concept[concept_idx]
print(f"Concept {concept_idx}: {concept_name}")  # Concept 58: probability
```

### EdNet - 只能使用数字ID

```python
import json

# 读取映射
with open('/mnt/localssd/pykt-toolkit/data/ednet/keyid2idx.json', 'r') as f:
    keyid2idx = json.load(f)

# EdNet的concepts只是数字到索引的映射
concepts_map = keyid2idx['concepts']
# 例如: {'119': 0, '30': 1, '24': 2, ...}

# 只能这样使用
concept_idx = 2
original_tag = None
for tag, idx in concepts_map.items():
    if idx == concept_idx:
        original_tag = tag
        break

print(f"Concept Index {concept_idx}: Original Tag {original_tag}")
# Concept Index 2: Original Tag 24
# （但无法知道Tag 24的具体含义）
```

---

## 📝 在Forgetting Score中使用

### 示例代码片段

```python
def get_concept_description(dataset_name, concept_idx):
    """
    获取concept的描述
    """
    if dataset_name == 'assist2017':
        # ASSISTments2017有描述
        with open(f'data/{dataset_name}/keyid2idx.json', 'r') as f:
            keyid2idx = json.load(f)
        idx_to_concept = {v: k for k, v in keyid2idx['concepts'].items()}
        return idx_to_concept.get(concept_idx, f"Unknown Concept {concept_idx}")
    
    elif dataset_name == 'ednet':
        # EdNet只有数字ID
        return f"Concept {concept_idx}"
    
    else:
        return f"Concept {concept_idx}"

# 使用示例
dataset = 'assist2017'
concept_id = 58
description = get_concept_description(dataset, concept_id)
print(f"需要复习的概念: {description}")  # 需要复习的概念: probability
```

---

## 📊 数据集对比总结

### EdNet
- ✅ 数据规模大 (4,687学生, 1.3M交互)
- ✅ 题库丰富 (11,901题)
- ❌ **Concept无文字描述**
- ⚠️ 需要额外工作来理解concept含义

### ASSISTments2017
- ✅ **Concept有完整文字描述**
- ✅ 描述清晰易懂
- ✅ 便于结果解释和报告撰写
- ⚠️ 数据规模相对较小

---

## 🔗 相关文件

- **EdNet keyid2idx**: `/mnt/localssd/pykt-toolkit/data/ednet/keyid2idx.json`
- **ASSISTments2017 keyid2idx**: `/mnt/localssd/pykt-toolkit/data/assist2017/keyid2idx.json`
- **ASSISTments2017原始数据**: `/mnt/localssd/pykt-toolkit/data/assist2017/anonymized_full_release_competition_dataset.csv`
- **Skills描述列表**: `/tmp/assistments2017_skill_descriptions.txt`
- **分析脚本**: `/mnt/localssd/extract_concept_descriptions.py`
- **分析日志**: `/tmp/concept_descriptions_analysis.txt`

---

## 💡 建议

### 对于论文/报告

1. **使用ASSISTments2017时**:
   - 可以直接引用skill名称
   - 使结果更具可解释性
   - 例如: "学生在概率 (probability) 和几何图形性质 (properties-of-geometric-figures) 上的遗忘率最高"

2. **使用EdNet时**:
   - 使用 "Concept X" 格式
   - 必要时在附录中列出高频concepts
   - 例如: "Concept 7 和 Concept 4 是最常见的知识点"

### 对于进一步研究

1. **EdNet concept标注**:
   - 可以考虑人工标注高频concepts
   - 或通过题目内容分析推断
   - 联系EdNet官方获取标签说明

2. **跨数据集对比**:
   - 使用concept频率进行对比
   - 关注不同数据集的知识点分布
   - 分析forgetting score在不同类型concept上的表现

---

**生成时间**: 2025-10-19  
**分析工具**: extract_concept_descriptions.py  
**数据集**: EdNet, ASSISTments2017

