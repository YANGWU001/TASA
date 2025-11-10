# Concept ID 映射分析报告

## 📋 问题描述

用户提出：Memory中的concept_id和Persona中相同的concept_id对应的concept_text是否不一样？

## 🔍 调查结果

### 1. Concept ID的来源

**原始数据来源：**
- Concept ID直接来自PyKT数据集的CSV文件中的`concepts`列
- 这是一个**数字ID**（如0, 1, 2, ...）
- 每个数据集都有自己的concept编号体系

**数据流程：**
```
原始CSV (test_sequences.csv, train_valid_sequences.csv)
  └─> concepts列包含concept_id数字
      └─> 通过keyid2idx.json映射为concept_text
```

### 2. Concept Text的映射

**映射文件：** `pykt-toolkit/data/{dataset}/keyid2idx.json`

**映射结构：**
```json
{
  "concepts": {
    "concept_text_1": 0,
    "concept_text_2": 1,
    ...
  }
}
```

**反向映射（代码中使用）：**
```python
# 在 create_student_bank_final.py 第101行
idx2concept = {v: k for k, v in keyid2idx['concepts'].items()}
# 结果: {0: "concept_text_1", 1: "concept_text_2", ...}
```

### 3. Persona和Memory的生成流程

#### 共同的数据提取（`extract_student_data`函数）

```python
def extract_student_data(row, dataset_name, idx2concept):
    # 1. 从CSV中读取concepts列（数字ID）
    concepts = parse_csv_field(row['concepts'])  # [0, 1, 2, ...]
    
    # 2. 对每个interaction创建记录
    for i in range(...):
        interactions.append({
            'concept_id': concepts[i],  # 数字ID
            'concept_text': get_concept_text(concepts[i], idx2concept),  # 通过映射获取文本
            ...
        })
    
    # 3. 分离历史数据和最后一次interaction
    # - history: 用于生成persona和memory
    # - last_interactions: 保存最后一次，不用于生成
```

#### Persona生成流程

```python
def generate_persona_llm(uid, history, dataset_name):
    # 1. 按concept_id统计
    stats = defaultdict(lambda: {'correct': 0, 'total': 0, 'concept_text': ''})
    for inter in history:
        cid = inter['concept_id']  # 使用数字ID作为key
        stats[cid]['concept_text'] = inter['concept_text']  # 保存对应的文本
        ...
    
    # 2. LLM生成后，创建persona记录
    personas.append({
        'concept_id': cid,  # 数字ID
        'concept_text': stats[cid]['concept_text'],  # 对应的文本
        ...
    })
```

#### Memory生成流程

```python
def generate_memory_llm(uid, history, dataset_name):
    # 1. 直接使用history中的interaction
    for inter in history:
        # inter已经包含了concept_id和concept_text
        # 这些是从extract_student_data中来的
        ...
    
    # 2. LLM生成后，创建memory记录
    memories.append({
        'concept_id': inter['concept_id'],  # 数字ID
        'concept_text': inter['concept_text'],  # 对应的文本
        ...
    })
```

### 4. 验证结果

通过对多个数据集和学生的检查：

#### ✅ Algebra2005 - 学生4
- Persona和Memory中concept_id的映射**完全一致**
- 没有发现不匹配

#### ✅ Bridge2006 - 学生255
- 对比concept_id=28: 
  - Persona: "List factor of large number"
  - Memory: "List factor of large number"
  - **完全匹配**

#### ✅ 结论
**Persona和Memory使用相同的映射机制，concept_id和concept_text的对应关系是一致的。**

## 📊 为什么可能出现"不一样"的感觉？

### 1. Memory可能为空或记录少
- Memory排除了每个concept的**最后一次interaction**
- 如果一个concept只有1-2次交互，排除最后一次后可能没有memory记录
- 但这不是映射错误，而是数据筛选的结果

### 2. 不同concept可能有相似的文本
- 某些数据集的concept名称很相似（如algebra2005的SkillRule系列）
- 需要完整查看concept_text才能区分

### 3. Concept ID的不同含义
在不同场景中，concept_id可能指：
- **数字ID**（如5）- 原始数据中的编号
- **字符串key**（如"concept_5"）- 在overall.json等文件中使用
- 这可能造成混淆，但实际映射是一致的

## 🔧 技术细节：Concept ID定义

### 数据预处理阶段（PyKT）

```
原始数据集
  └─> pykt预处理
      └─> 生成keyid2idx.json
          └─> concepts字段: {concept_text: concept_id}
      └─> 生成train_valid_sequences.csv / test_sequences.csv
          └─> concepts列: 数字ID序列（如"0,1,2,..."）
```

### Bank创建阶段（本项目）

```
1. 加载keyid2idx.json
   └─> 创建反向映射 idx2concept: {concept_id: concept_text}

2. 读取CSV数据
   └─> 解析concepts列为数字列表
   └─> 每个数字通过idx2concept映射为文本

3. 生成Persona和Memory
   └─> 都使用相同的concept_id和concept_text
   └─> 来自同一次extract_student_data调用
```

## ✅ 最终结论

1. **Concept ID来源**：原始CSV数据的concepts列（数字）
2. **Concept Text来源**：通过keyid2idx.json的反向映射
3. **映射一致性**：Persona和Memory使用**完全相同**的映射机制
4. **数据验证**：多次验证显示concept_id和concept_text的对应关系**一致且正确**

如果在特定学生/concept上发现不匹配，可能原因：
- 查看的是不同concept（ID碰巧相同但来自不同数据集）
- Memory记录被排除（因为是最后一次interaction）
- 显示时文本被截断导致看起来不同

## 📝 推荐验证方法

如果要验证特定学生的映射：

```python
import json

dataset = 'your_dataset'
student_id = 'your_student_id'

# 1. 查看persona
with open(f'bank/persona/{dataset}/data/{student_id}.json') as f:
    persona = json.load(f)

# 2. 查看memory  
with open(f'bank/memory/{dataset}/data/{student_id}.json') as f:
    memory = json.load(f)

# 3. 对比同一个concept_id
test_id = 5  # 你想检查的concept_id

persona_matches = [p for p in persona if p['concept_id'] == test_id]
memory_matches = [m for m in memory if m['concept_id'] == test_id]

print(f"Persona: {persona_matches[0]['concept_text'] if persona_matches else 'Not found'}")
print(f"Memory:  {memory_matches[0]['concept_text'] if memory_matches else 'Not found'}")
```

---

**生成时间**: 2025年10月20日  
**调查数据集**: assist2017, nips_task34, algebra2005, bridge2006  
**验证学生数**: 10+

