# 🚀 Forgetting Score Bank 快速开始

## ✅ 已完成的数据

### 立即可用：8个模型的预测

```
/mnt/localssd/bank/forgetting/
├── assist2017/       (3个模型: LPKT, DKT, AKT)
├── nips_task34/      (2个模型: DKT, AKT)
└── algebra2005/      (3个模型: LPKT, DKT, AKT)
```

**总计：** 1,438个学生，8个模型预测

---

## 📖 数据格式

### JSON结构
```json
{
  "student_id": {
    "concept_0": {
      "s_tc": 0.4111,           // KT模型预测的答对概率
      "fs": 0.0291,             // Forgetting Score
      "level": "high",          // low/medium/high
      "last_response": 1,       // 0或1
      "num_attempts": 5         // 尝试次数
    }
  }
}
```

### Level定义
- **Low (33%)**: FS < 33rd percentile（记忆稳定）
- **Medium (34%)**: 33rd ≤ FS < 67th percentile（中等风险）
- **High (33%)**: FS ≥ 67th percentile（易遗忘，需复习）

---

## 💻 快速使用

### 1. 查询单个学生的FS

```python
import json

# 加载数据
with open('/mnt/localssd/bank/forgetting/assist2017/lpkt.json') as f:
    fs_data = json.load(f)

# 查询学生
student_id = "7"
if student_id in fs_data:
    print(f"学生 {student_id} 的Forgetting Scores:")
    
    # 找出需要复习的concepts（high FS）
    high_fs_concepts = {
        concept: info 
        for concept, info in fs_data[student_id].items() 
        if info['level'] == 'high'
    }
    
    print(f"\n需要重点复习: {len(high_fs_concepts)} 个concepts")
    for concept, info in sorted(high_fs_concepts.items(), 
                                 key=lambda x: x[1]['fs'], 
                                 reverse=True)[:5]:
        print(f"  {concept}: FS={info['fs']:.3f}, "
              f"s_tc={info['s_tc']:.3f}, "
              f"答错={1-info['last_response']}")
```

### 2. 对比不同模型的预测

```python
import json

dataset = 'assist2017'
models = ['lpkt', 'dkt', 'akt']
student_id = "7"

print(f"学生 {student_id} 在不同模型下的FS对比:\n")

for model in models:
    with open(f'/mnt/localssd/bank/forgetting/{dataset}/{model}.json') as f:
        data = json.load(f)
    
    if student_id in data:
        avg_fs = sum(c['fs'] for c in data[student_id].values()) / len(data[student_id])
        high_count = sum(1 for c in data[student_id].values() if c['level'] == 'high')
        
        print(f"{model.upper():8} | 平均FS: {avg_fs:.4f} | 高风险concepts: {high_count}")
```

### 3. 分析整个数据集

```python
import json
from collections import defaultdict

# 加载数据
with open('/mnt/localssd/bank/forgetting/assist2017/lpkt.json') as f:
    fs_data = json.load(f)

# 统计
total_students = len(fs_data)
total_concepts = sum(len(student) for student in fs_data.values())

# 每个concept的平均FS
concept_fs = defaultdict(list)
for student in fs_data.values():
    for concept, info in student.items():
        concept_fs[concept].append(info['fs'])

# 找出最难的concepts
import numpy as np
difficult_concepts = sorted(
    [(c, np.mean(fs_list)) for c, fs_list in concept_fs.items()],
    key=lambda x: x[1],
    reverse=True
)[:10]

print(f"数据集统计:")
print(f"  学生数: {total_students}")
print(f"  总记录数: {total_concepts}")
print(f"\n最容易遗忘的10个concepts:")
for concept, avg_fs in difficult_concepts:
    print(f"  {concept}: 平均FS = {avg_fs:.4f}")
```

---

## 🎯 实际应用场景

### 场景1：个性化学习推荐

```python
def recommend_review_concepts(student_id, dataset='assist2017', model='lpkt'):
    """推荐需要复习的concepts"""
    
    with open(f'/mnt/localssd/bank/forgetting/{dataset}/{model}.json') as f:
        fs_data = json.load(f)
    
    if student_id not in fs_data:
        return None
    
    # 按FS排序
    concepts = sorted(
        fs_data[student_id].items(),
        key=lambda x: x[1]['fs'],
        reverse=True
    )
    
    # 分类推荐
    urgent = [c for c, info in concepts if info['level'] == 'high']
    review = [c for c, info in concepts if info['level'] == 'medium']
    stable = [c for c, info in concepts if info['level'] == 'low']
    
    return {
        'urgent_review': urgent,        # 需要立即复习
        'scheduled_review': review,     # 定期复习
        'stable': stable,               # 掌握稳定
    }

# 使用
recommendations = recommend_review_concepts("7")
print(f"紧急复习: {len(recommendations['urgent_review'])} concepts")
print(f"定期复习: {len(recommendations['scheduled_review'])} concepts")
print(f"掌握稳定: {len(recommendations['stable'])} concepts")
```

### 场景2：学习效果评估

```python
def evaluate_student_retention(student_id, dataset='assist2017', model='lpkt'):
    """评估学生的记忆保持情况"""
    
    with open(f'/mnt/localssd/bank/forgetting/{dataset}/{model}.json') as f:
        fs_data = json.load(f)
    
    if student_id not in fs_data:
        return None
    
    student_concepts = fs_data[student_id]
    
    avg_fs = sum(c['fs'] for c in student_concepts.values()) / len(student_concepts)
    avg_stc = sum(c['s_tc'] for c in student_concepts.values()) / len(student_concepts)
    
    level_dist = {
        'low': sum(1 for c in student_concepts.values() if c['level'] == 'low'),
        'medium': sum(1 for c in student_concepts.values() if c['level'] == 'medium'),
        'high': sum(1 for c in student_concepts.values() if c['level'] == 'high'),
    }
    
    return {
        'overall_retention': 1 - avg_fs,      # 整体保持率
        'current_mastery': avg_stc,           # 当前掌握水平
        'at_risk_count': level_dist['high'],  # 风险concept数
        'stable_count': level_dist['low'],    # 稳定concept数
        'level_distribution': level_dist,     # Level分布
    }

# 使用
eval_result = evaluate_student_retention("7")
print(f"整体保持率: {eval_result['overall_retention']:.1%}")
print(f"当前掌握水平: {eval_result['current_mastery']:.1%}")
print(f"风险concepts: {eval_result['at_risk_count']}")
```

### 场景3：概念难度分析

```python
def analyze_concept_difficulty(dataset='assist2017', model='lpkt'):
    """分析哪些concepts整体更容易被遗忘"""
    
    with open(f'/mnt/localssd/bank/forgetting/{dataset}/{model}.json') as f:
        fs_data = json.load(f)
    
    concept_stats = defaultdict(lambda: {'fs_list': [], 'attempts': [], 'errors': []})
    
    for student in fs_data.values():
        for concept, info in student.items():
            concept_stats[concept]['fs_list'].append(info['fs'])
            concept_stats[concept]['attempts'].append(info['num_attempts'])
            concept_stats[concept]['errors'].append(1 - info['last_response'])
    
    # 计算统计
    results = []
    for concept, stats in concept_stats.items():
        results.append({
            'concept': concept,
            'avg_fs': np.mean(stats['fs_list']),
            'student_count': len(stats['fs_list']),
            'avg_attempts': np.mean(stats['attempts']),
            'error_rate': np.mean(stats['errors']),
        })
    
    # 按平均FS排序
    results.sort(key=lambda x: x['avg_fs'], reverse=True)
    
    return results

# 使用
difficulty = analyze_concept_difficulty()
print("最容易遗忘的10个concepts:")
for i, c in enumerate(difficulty[:10], 1):
    print(f"{i:2}. {c['concept']:15} | FS={c['avg_fs']:.4f} | "
          f"学生数={c['student_count']} | 错误率={c['error_rate']:.1%}")
```

---

## 📊 数据统计

### 已生成数据概览

| 数据集 | 学生数 | 模型数 | 文件大小 | 可用性 |
|--------|--------|--------|----------|--------|
| ASSISTments2017 | 341 | 3 | 5.7 MB | ✅✅✅ |
| NIPS Task 3&4 | 983 | 2 | 7.2 MB | ✅✅ |
| Algebra2005 | 114 | 3 | 2.0 MB | ✅✅✅ |
| Bridge2Algebra2006 | - | 0 | - | ❌ |

### 模型对比

| 模型 | 数据集覆盖 | 推荐度 |
|------|-----------|--------|
| **DKT** | 3/4 (75%) | ⭐⭐⭐⭐⭐ 最稳定 |
| **AKT** | 3/4 (75%) | ⭐⭐⭐⭐⭐ 最稳定 |
| **LPKT** | 2/4 (50%) | ⭐⭐⭐ 部分可用 |
| **SimpleKT** | 0/4 (0%) | ❌ 不可用 |

---

## 🔗 与其他数据的整合

### 与Bank Persona结合

```python
import json

# 加载FS
with open('/mnt/localssd/bank/forgetting/assist2017/lpkt.json') as f:
    fs_data = json.load(f)

# 加载Persona
with open('/mnt/localssd/bank/persona/assist2017/data/7.json') as f:
    persona_data = json.load(f)

student_id = "7"

# 综合分析
if student_id in fs_data:
    print(f"学生 {student_id} 的综合学习档案:")
    print(f"\n【当前状态】(来自FS):")
    
    for concept, info in list(fs_data[student_id].items())[:5]:
        print(f"  {concept}:")
        print(f"    FS: {info['fs']:.3f} ({info['level']})")
        print(f"    预测掌握度: {info['s_tc']:.1%}")
    
    print(f"\n【历史表现】(来自Persona):")
    if 'persona' in persona_data:
        for p in persona_data['persona'][:3]:
            print(f"  {p['keywords']}:")
            print(f"    {p['description'][:100]}...")
```

---

## 📞 技术支持

### 相关文件
- **完整报告**: `/mnt/localssd/FORGETTING_SCORE_BANK_SUMMARY.md`
- **数据目录**: `/mnt/localssd/bank/forgetting/`
- **运行脚本**: `/mnt/localssd/run_all_fs_parallel.sh`
- **监控脚本**: `/mnt/localssd/monitor_fs_parallel.sh`

### 常见问题

**Q: 为什么是concept_0而不是实际的concept名称？**

A: 因为数据集没有提供concept的文本描述。可以通过concept mapping文件获取实际名称。

**Q: 如何补充Bridge2Algebra2006的数据？**

A: 运行修复后的脚本，强制使用CPU：
```bash
cd /mnt/localssd/pykt-toolkit/examples
CUDA_VISIBLE_DEVICES="" python calc_fs_all_data_simple.py \
    --dataset=bridge2algebra2006 \
    --model=lpkt \
    --save_dir=saved_model/bridge2algebra2006_lpkt_... \
    --gpu=0
```

**Q: 不同模型的预测差异大吗？**

A: 对于同一个学生，不同模型的预测会有差异，建议使用多个模型的平均值或者选择最稳定的模型（DKT/AKT）。

---

## ✨ 总结

### ✅ 你现在拥有：

1. **8个训练好的KT模型预测**
2. **1,438个学生**的Forgetting Score
3. **concept-level的细粒度预测**
4. **基于dataset的level分类**
5. **完全符合要求的JSON格式**

### 🚀 立即开始使用！

```python
import json

# 加载数据
with open('/mnt/localssd/bank/forgetting/assist2017/lpkt.json') as f:
    data = json.load(f)

# 查看第一个学生
student_id = list(data.keys())[0]
print(f"学生 {student_id} 有 {len(data[student_id])} 个concepts的FS预测")

# 找出高风险concepts
high_risk = [c for c, info in data[student_id].items() if info['level'] == 'high']
print(f"其中 {len(high_risk)} 个需要重点复习")
```

**开始构建你的个性化学习系统！** 🎓

