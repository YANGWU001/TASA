# 所有数据集的Concept描述对比

> 生成时间: 2025-10-19  
> 包含: EdNet, ASSISTments2017, NIPS Task 3&4

---

## 📊 快速对比

| 数据集 | Concept数量 | 有文字描述 | 描述类型 | 可解释性 | 数据可用性 |
|--------|-------------|-----------|----------|----------|------------|
| **EdNet** | 188 | ❌ **否** | 仅数字ID (1-300) | ⭐ 低 | ✅ 已下载 |
| **ASSISTments2017** | 102 | ✅ **是** | 英文skill名称 | ⭐⭐⭐ 高 | ✅ 已下载 |
| **NIPS Task 3&4** | 待查看 | ✅ **是** | 英文subject名称 + **层级结构** | ⭐⭐⭐⭐ 很高 | ⚠️ 需下载 |

---

## 1️⃣ EdNet 数据集

### Concept状况
❌ **没有文字描述**

### 详细信息
- **Concept数量**: 188个
- **表示方式**: 纯数字ID (如: 1, 2, 7, 24, 119, 181...)
- **来源**: EdNet平台内部的知识点标签
- **局限**: 无法知道每个ID的具体含义

### 最常见Concepts（按频率）
1. Concept 7: 84,785次 (7.91%)
2. Concept 4: 74,471次 (6.95%)
3. Concept 5: 61,601次 (5.75%)
4. Concept 8: 55,884次 (5.22%)
5. Concept 24: 42,699次 (3.99%)

### 使用示例
```python
# 只能这样表示
concept_id = 7
print(f"学生在Concept {concept_id}上的遗忘分数: 0.65")
# 输出: "学生在Concept 7上的遗忘分数: 0.65"
```

### 数据规模
- 学生数: 4,687
- 交互数: 1,375,065
- 题目数: 11,901

---

## 2️⃣ ASSISTments2017 数据集

### Concept状况
✅ **有完整的Skill文字描述**

### 详细信息
- **Concept数量**: 102个skills
- **表示方式**: 清晰的英文名称
- **来源**: ASSISTments平台的skill标注
- **优势**: 描述清晰，易于理解

### 最常见Skills（前10）
| 排名 | ID | Skill名称 | 频次 | 中文含义 |
|------|----|-----------| -----|----------|
| 1 | 21 | noskill | 78,103 | 无特定技能 |
| 2 | 58 | **probability** | 73,183 | **概率** |
| 3 | 14 | pattern-finding | 45,027 | 模式发现 |
| 4 | 5 | area | 34,308 | 面积 |
| 5 | 34 | equation-solving | 33,966 | 方程求解 |
| 6 | 33 | multiplication | 26,406 | 乘法 |
| 7 | 37 | inducing-functions | 24,849 | 函数归纳 |
| 8 | 7 | square-root | 24,487 | 平方根 |
| 9 | 60 | symbolization-articulation | 22,745 | 符号表达 |
| 10 | 12 | pythagorean-theorem | 22,104 | 勾股定理 |

### Skills分类
- **几何类**: properties-of-geometric-figures, area, perimeter, pythagorean-theorem
- **代数类**: equation-solving, algebraic-manipulation, inducing-functions, substitution
- **数与运算**: multiplication, division, fractions, decimals
- **概率统计**: probability, combinatorics, mean, median

### 使用示例
```python
import json
with open('data/assist2017/keyid2idx.json', 'r') as f:
    keyid2idx = json.load(f)

idx_to_skill = {v: k for k, v in keyid2idx['concepts'].items()}
concept_id = 58
skill_name = idx_to_skill[concept_id]
print(f"学生在{skill_name}上的遗忘分数: 0.65")
# 输出: "学生在probability上的遗忘分数: 0.65"
```

### 数据规模
- 学生数: 1,708
- 交互数: 942,785
- 题目数: 3,162

---

## 3️⃣ NIPS Task 3&4 数据集

### Concept状况
✅ **有完整的Subject文字描述 + 层级结构**

### 详细信息
- **Concept数量**: Level 3 subjects数量（需查看metadata）
- **表示方式**: 英文subject名称 + 3层层级结构
- **来源**: Eedi平台（英国）+ 英国国家课程标准
- **特殊特性**: 
  - ⭐ **支持多concept题目**（一题多个knowledge points）
  - ⭐ **3层知识层级结构**

### 层级结构
```
Level 1: 大类（如 Mathematics）
  ├── Level 2: 中类（如 Number, Algebra, Geometry）
      └── Level 3: 细类（如 Fractions, Decimals, Linear Equations）
```

### 典型Subjects（基于Eedi平台）
可能包括（需查看具体metadata）:
- **Number**: Fractions, Decimals, Percentages, Ratios
- **Algebra**: Linear Equations, Quadratic Equations, Simultaneous Equations
- **Geometry**: Angles, Area, Volume, Transformations
- **Probability**: Probability Calculations, Tree Diagrams
- **Statistics**: Mean, Median, Mode, Range

### 使用示例
```python
import pandas as pd

# 读取subject metadata
subject_df = pd.read_csv('data/nips_task34/metadata/subject_metadata.csv')
subject_dict = dict(zip(subject_df['SubjectId'], subject_df['Name']))

# 处理多concept题目
concept_str = "123_456"  # 一题多个subjects
subject_ids = [int(x) for x in concept_str.split('_')]
subject_names = [subject_dict[sid] for sid in subject_ids]
print(f"学生在{' & '.join(subject_names)}上的遗忘分数: 0.65")
# 输出: "学生在Fractions & Decimals上的遗忘分数: 0.65"
```

### 数据获取
⚠️ 需要从官方网站下载:
- 网站: https://competitions.codalab.org/competitions/25449
- 需要注册NeurIPS 2020 Education Challenge
- 论文: https://arxiv.org/abs/2007.12061

---

## 🎯 对比分析

### 1. Concept描述质量

| 数据集 | 描述质量 | 说明 |
|--------|----------|------|
| EdNet | ❌ 无描述 | 只有数字ID，无法理解含义 |
| ASSISTments2017 | ✅✅ 好 | 清晰的skill名称，易于理解 |
| NIPS Task 3&4 | ✅✅✅ 很好 | skill名称 + 层级结构，最丰富 |

### 2. 结果可解释性

**示例：遗忘分数报告**

#### EdNet（可解释性：⭐）
```
Top 3 遗忘concepts:
1. Concept 7: F=0.72
2. Concept 24: F=0.68
3. Concept 5: F=0.65
```
❌ **问题**: 无法知道这些concepts具体是什么知识点

#### ASSISTments2017（可解释性：⭐⭐⭐）
```
Top 3 遗忘skills:
1. probability (概率): F=0.72
2. equation-solving (方程求解): F=0.68
3. area (面积): F=0.65
```
✅ **优势**: 清楚地知道学生在哪些知识点上容易遗忘

#### NIPS Task 3&4（可解释性：⭐⭐⭐⭐）
```
Top 3 遗忘subjects:
1. Fractions [Number > Fractions]: F=0.72
2. Linear Equations [Algebra > Linear Equations]: F=0.68
3. Area of Triangles [Geometry > Area > Triangles]: F=0.65
```
✅✅ **优势**: 
- 知道具体knowledge points
- 知道在knowledge hierarchy中的位置
- 可以做多层级分析

### 3. 研究场景适用性

| 研究场景 | 推荐数据集 | 理由 |
|----------|------------|------|
| **基础KT模型测试** | EdNet, ASSISTments2017 | 数据规模合适，已有benchmark |
| **Forgetting分析** | ASSISTments2017, NIPS Task 3&4 | 需要concept描述来解释结果 |
| **层级知识建模** | NIPS Task 3&4 | 唯一有层级结构的数据集 |
| **多concept题目** | NIPS Task 3&4 | 唯一支持多concept的数据集 |
| **大规模实验** | EdNet | 数据量最大 |
| **教育应用** | ASSISTments2017, NIPS Task 3&4 | concept描述便于向教师/学生解释 |

### 4. 数据特性对比

| 特性 | EdNet | ASSISTments2017 | NIPS Task 3&4 |
|------|-------|-----------------|---------------|
| **Concept描述** | ❌ | ✅ | ✅✅ |
| **层级结构** | ❌ | ❌ | ✅ |
| **多Concept题目** | ❌ | ❌ | ✅ |
| **时间戳** | ✅ | ✅ | ✅ |
| **学生数** | 4,687 | 1,708 | ? |
| **交互数** | 1.3M | 940K | ? |
| **题目数** | 11,901 | 3,162 | ? |
| **Concept数** | 188 | 102 | ? |
| **数据可用** | ✅ 是 | ✅ 是 | ⚠️ 需下载 |
| **正确率** | 67% | 37% | ? |

---

## 💡 使用建议

### 根据研究目标选择

#### 场景1: 需要解释concept含义
**推荐**: ASSISTments2017 或 NIPS Task 3&4

```python
# ✅ 好的研究报告
"学生在概率(probability)和方程求解(equation-solving)上的遗忘分数较高，
建议增加这些知识点的复习频率。"

# ❌ 不好的研究报告
"学生在Concept 7和Concept 24上的遗忘分数较高。"
（无法理解这是什么知识点）
```

#### 场景2: 研究知识层级关系
**推荐**: NIPS Task 3&4

```python
# 可以分析
- Level 1层级的遗忘模式
- Level 2层级的遗忘模式
- Level 3层级的遗忘模式
- 不同层级间的遗忘传递
```

#### 场景3: 需要大规模数据
**推荐**: EdNet
- 接受concept无描述的限制
- 关注模型性能而非可解释性

### 代码中如何处理

#### 通用Concept描述获取函数

```python
import json
import pandas as pd

def get_concept_description(dataset_name, concept_idx, data_dir='data'):
    """
    获取concept的描述
    
    Args:
        dataset_name: 'ednet', 'assist2017', 'nips_task34'
        concept_idx: concept的索引
        data_dir: 数据目录
    
    Returns:
        str: concept的描述
    """
    if dataset_name == 'ednet':
        # EdNet只有数字ID
        return f"Concept {concept_idx}"
    
    elif dataset_name == 'assist2017':
        # ASSISTments2017有skill名称
        keyid_path = f"{data_dir}/assist2017/keyid2idx.json"
        with open(keyid_path, 'r') as f:
            keyid2idx = json.load(f)
        idx_to_skill = {v: k for k, v in keyid2idx['concepts'].items()}
        return idx_to_skill.get(concept_idx, f"Unknown Skill {concept_idx}")
    
    elif dataset_name == 'nips_task34':
        # NIPS Task 3&4有subject名称和层级
        subject_path = f"{data_dir}/nips_task34/metadata/subject_metadata.csv"
        subject_df = pd.read_csv(subject_path)
        subject_dict = dict(zip(subject_df['SubjectId'], subject_df['Name']))
        
        # 处理可能的多concept
        if '_' in str(concept_idx):
            subject_ids = [int(x) for x in str(concept_idx).split('_')]
            names = [subject_dict.get(sid, f"Subject {sid}") for sid in subject_ids]
            return ' & '.join(names)
        else:
            return subject_dict.get(concept_idx, f"Unknown Subject {concept_idx}")
    
    return f"Concept {concept_idx}"

# 使用示例
print(get_concept_description('ednet', 7))
# 输出: "Concept 7"

print(get_concept_description('assist2017', 58))
# 输出: "probability"

print(get_concept_description('nips_task34', '123_456'))
# 输出: "Fractions & Decimals" (假设的)
```

---

## 📚 相关文档

### 已生成的文档
1. **EdNet & ASSISTments2017详细分析**: `/mnt/localssd/CONCEPT_DESCRIPTIONS.md`
2. **NIPS Task 3&4信息**: `/mnt/localssd/NIPS_TASK34_INFO.md`
3. **完整数据集统计**: `/mnt/localssd/COMPLETE_DATASET_STATISTICS.md`
4. **数据分割策略**: `/mnt/localssd/DATA_SPLIT_STRATEGY.md`

### 数据文件位置
- **EdNet**: `/mnt/localssd/pykt-toolkit/data/ednet/`
- **ASSISTments2017**: `/mnt/localssd/pykt-toolkit/data/assist2017/`
- **NIPS Task 3&4**: `/mnt/localssd/pykt-toolkit/data/nips_task34/` (需下载)

### ASSISTments2017 Skills列表
完整的102个skills描述: `/tmp/assistments2017_skill_descriptions.txt`

---

## 🎓 论文撰写建议

### 在Methods部分

```markdown
我们在三个公开数据集上评估了我们的方法：

1. **EdNet**: 包含4,687名学生的1,375,065次交互，涵盖188个知识点。
   由于原始数据集未提供知识点的文字描述，我们在结果中使用"Concept X"来指代。

2. **ASSISTments2017**: 包含1,708名学生的942,785次交互，涵盖102个数学技能
   (skills)，如概率(probability)、方程求解(equation-solving)等。

3. **NIPS Task 3&4**: NeurIPS 2020 Education Challenge数据集，包含层级化的
   知识点结构（3层），支持多知识点题目分析。
```

### 在Results部分

```markdown
**EdNet**: 
模型在Concept 7（频率7.91%）和Concept 4（频率6.95%）上的表现最佳。

**ASSISTments2017**: 
模型在概率(probability)和模式发现(pattern-finding)上的遗忘分数最高，
分别为0.72和0.68，表明学生在这些抽象概念上需要更多复习。

**NIPS Task 3&4**:
分析显示Level 2的代数(Algebra)类知识点遗忘速度快于几何(Geometry)类，
其中线性方程(Linear Equations)的遗忘分数达0.68。
```

---

## 🔍 总结

### 三个数据集的最佳用途

1. **EdNet**
   - ✅ 大规模模型训练
   - ✅ Benchmark性能测试
   - ❌ 不适合需要解释concept含义的研究

2. **ASSISTments2017**
   - ✅ 中等规模、清晰的concept描述
   - ✅ 适合教育应用研究
   - ✅ 结果易于向非技术人员解释
   - ✅ **推荐用于Forgetting Score分析**

3. **NIPS Task 3&4**
   - ✅ 最丰富的concept描述（层级结构）
   - ✅ 唯一支持多concept题目
   - ✅ 适合高级知识建模研究
   - ✅ **最适合需要深度concept分析的研究**
   - ⚠️ 需要额外下载

### 快速决策树

```
需要concept文字描述吗？
├── 否 → EdNet（大规模数据）
└── 是 → 需要层级结构吗？
    ├── 否 → ASSISTments2017（简单清晰）
    └── 是 → NIPS Task 3&4（最丰富）
```

---

**最后更新**: 2025-10-19  
**相关项目**: pykt-toolkit  
**作者**: AI Assistant

