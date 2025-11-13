# 🧠 Concept-level Forgetting Score 计算指南

## 📖 概述

遗忘分数（Forgetting Score）用于量化学生对某个知识概念（concept）的遗忘程度，结合了：
1. **掌握程度**：从LPKT模型获得的预测答对概率
2. **时间因素**：距离上次学习该concept的时间间隔

## 📐 公式

```
F_c(t) ≈ (1 - s_{t,c}) · (Δt_c / (Δt_c + τ))
```

### 参数说明

| 符号 | 含义 | 说明 |
|------|------|------|
| `F_c(t)` | 遗忘分数 | 范围 [0, 1]，越高表示遗忘越严重 |
| `s_{t,c}` | 预测概率 | LPKT模型预测在时间t答对concept c的概率 |
| `(1 - s_{t,c})` | 掌握因子 | 掌握越差，遗忘风险越高 |
| `Δt_c` | 时间间隔 | 距离上次学习concept c的时间（分钟） |
| `τ` | 时间尺度 | 控制遗忘曲线的陡峭程度（分钟） |

### 公式解释

1. **掌握因子** `(1 - s_{t,c})`
   - 如果预测概率高（如0.9），说明掌握好，掌握因子低（0.1）
   - 如果预测概率低（如0.3），说明掌握差，掌握因子高（0.7）

2. **时间衰减因子** `Δt_c / (Δt_c + τ)`
   - 当 `Δt_c = 0` 时，因子 = 0（刚学完，还没遗忘）
   - 当 `Δt_c = τ` 时，因子 = 0.5（遗忘一半）
   - 当 `Δt_c → ∞` 时，因子 → 1（完全遗忘）

## 🔧 使用方法

### 方法1: 演示模式

```bash
cd /mnt/localssd/pykt-toolkit/examples
source activate pykt
python forgetting_score_calculator.py --mode demo
```

### 方法2: Python API

```python
from forgetting_score_calculator import ForgettingScoreCalculator
import torch
from datetime import datetime

# 初始化计算器
calculator = ForgettingScoreCalculator(
    model_dir="saved_model/ednet_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_0_0",
    tau=7*24*60,  # τ = 7天（以分钟为单位）
    device="cuda" if torch.cuda.is_available() else "cpu"
)

# 更新学生答题历史
student_id = "S001"
current_time = int(datetime.now().timestamp() * 1000)

# 添加答题记录
calculator.update_student_history(
    student_id=student_id,
    concept_id=5,
    response=1,  # 1=答对, 0=答错
    timestamp=current_time - (7*24*60*60*1000)  # 7天前
)

# 计算特定concept的遗忘分数
score_info = calculator.calculate_forgetting_score(
    student_id=student_id,
    target_concept=5,
    current_time=current_time
)

print(f"遗忘分数: {score_info['forgetting_score']:.4f}")
print(f"预测概率: {score_info['predicted_prob']:.4f}")
print(f"时间间隔: {score_info['time_delta_days']:.2f}天")

# 获取所有concepts的遗忘分数（按遗忘程度排序）
all_scores = calculator.calculate_all_concept_forgetting(
    student_id=student_id,
    current_time=current_time
)

# 推荐需要复习的concepts
review_list = calculator.recommend_review_concepts(
    student_id=student_id,
    current_time=current_time,
    top_k=5,           # 返回前5个
    threshold=0.2      # 遗忘分数阈值
)

for concept in review_list:
    print(f"Concept {concept['concept_id']}: 遗忘分数 {concept['forgetting_score']:.4f}")
```

## 📊 返回值说明

`calculate_forgetting_score()` 返回的字典包含：

```python
{
    'forgetting_score': 0.3456,        # 遗忘分数 [0, 1]
    'predicted_prob': 0.7234,          # LPKT预测的答对概率
    'time_delta_minutes': 10080.0,     # 时间间隔（分钟）
    'time_delta_hours': 168.0,         # 时间间隔（小时）
    'time_delta_days': 7.0,            # 时间间隔（天）
    'last_attempt_time': 1234567890,   # 上次答题时间戳
    'mastery_factor': 0.2766,          # 掌握因子 (1 - s_t,c)
    'time_decay_factor': 0.5,          # 时间衰减因子
    'tau_minutes': 10080,              # τ参数（分钟）
    'tau_days': 7.0                    # τ参数（天）
}
```

## 🎯 遗忘分数解读

| 分数范围 | 遗忘程度 | 建议 |
|---------|---------|------|
| 0.0 - 0.2 | 轻微 | 掌握良好，暂时不需要复习 |
| 0.2 - 0.4 | 轻度 | 建议安排复习 |
| 0.4 - 0.6 | 中度 | 需要尽快复习 |
| 0.6 - 0.8 | 重度 | 需要立即复习 |
| 0.8 - 1.0 | 严重 | 急需复习，可能需要重新学习 |

## ⚙️ τ参数选择

τ（tau）是时间尺度参数，控制遗忘曲线的形状。

### τ的影响

```
小τ (如1天 = 1440分钟):
  - 遗忘曲线陡峭
  - 时间影响大
  - 适合需要频繁练习的技能

大τ (如30天 = 43200分钟):
  - 遗忘曲线平缓
  - 时间影响小
  - 适合长期记忆的知识
```

### 推荐τ值

| 学习内容类型 | 推荐τ值 | 说明 |
|------------|--------|------|
| 基础概念 | 3-7天 | 需要及时复习 |
| 技能应用 | 7-14天 | 需要定期练习 |
| 知识理解 | 14-30天 | 长期记忆 |

### 如何选择τ

#### 方法1: 基于验证集（推荐）

```python
best_tau = ForgettingScoreCalculator.select_tau_by_validation(
    model_dir="saved_model/ednet_lpkt_...",
    val_data_path="data/ednet/train_valid_sequences.csv",
    tau_candidates=[1*24*60, 3*24*60, 7*24*60, 14*24*60, 30*24*60]
)
```

#### 方法2: 基于concept特性

对不同类型的concept使用不同的τ值：

```python
# 为每个concept设置不同的τ
concept_tau = {
    1: 3*24*60,   # 基础概念，3天
    2: 7*24*60,   # 进阶概念，7天
    3: 14*24*60,  # 复杂概念，14天
}

calculator = ForgettingScoreCalculator(
    model_dir=model_dir,
    tau=concept_tau.get(concept_id, 7*24*60)  # 默认7天
)
```

#### 方法3: 基于经验规则

```python
# 根据Ebbinghaus遗忘曲线
# τ = 学习后到记忆强度减半的时间

# 典型值:
tau_1_day = 1 * 24 * 60      # 1440分钟
tau_3_days = 3 * 24 * 60     # 4320分钟
tau_1_week = 7 * 24 * 60     # 10080分钟 (推荐默认值)
tau_2_weeks = 14 * 24 * 60   # 20160分钟
tau_1_month = 30 * 24 * 60   # 43200分钟
```

## 📈 应用场景

### 1. 个性化复习推荐

```python
# 每天为学生推荐最需要复习的concepts
def daily_review_recommendation(student_id):
    current_time = int(datetime.now().timestamp() * 1000)
    
    # 获取推荐列表
    review_list = calculator.recommend_review_concepts(
        student_id=student_id,
        current_time=current_time,
        top_k=10,
        threshold=0.3
    )
    
    # 生成复习计划
    for concept in review_list:
        if concept['forgetting_score'] > 0.6:
            priority = "高优先级"
        elif concept['forgetting_score'] > 0.4:
            priority = "中优先级"
        else:
            priority = "低优先级"
        
        print(f"{priority}: 复习Concept {concept['concept_id']}")
    
    return review_list
```

### 2. 学习进度监控

```python
# 监控学生的整体遗忘情况
def monitor_forgetting_status(student_id):
    current_time = int(datetime.now().timestamp() * 1000)
    all_scores = calculator.calculate_all_concept_forgetting(student_id, current_time)
    
    if not all_scores:
        return
    
    avg_forgetting = np.mean([s['forgetting_score'] for s in all_scores])
    max_forgetting = max([s['forgetting_score'] for s in all_scores])
    
    print(f"平均遗忘分数: {avg_forgetting:.4f}")
    print(f"最大遗忘分数: {max_forgetting:.4f}")
    
    # 预警
    if avg_forgetting > 0.5:
        print("⚠️  警告：整体遗忘程度较高，需要加强复习")
    elif max_forgetting > 0.7:
        print("⚠️  注意：某些concept遗忘严重，需要重点复习")
```

### 3. 智能间隔重复（Spaced Repetition）

```python
# 基于遗忘分数动态调整复习间隔
def adaptive_review_schedule(student_id, concept_id):
    current_time = int(datetime.now().timestamp() * 1000)
    
    score_info = calculator.calculate_forgetting_score(
        student_id, concept_id, current_time
    )
    
    forgetting_score = score_info['forgetting_score']
    
    # 根据遗忘分数计算下次复习时间
    if forgetting_score < 0.2:
        next_review_days = 14  # 掌握好，14天后复习
    elif forgetting_score < 0.4:
        next_review_days = 7   # 一般，7天后复习
    elif forgetting_score < 0.6:
        next_review_days = 3   # 较差，3天后复习
    else:
        next_review_days = 1   # 很差，明天复习
    
    next_review_time = current_time + (next_review_days * 24 * 60 * 60 * 1000)
    
    return {
        'next_review_time': next_review_time,
        'days_until_review': next_review_days,
        'forgetting_score': forgetting_score
    }
```

## 🔬 高级用法

### 多τ值策略

为不同难度的concepts使用不同的τ：

```python
class AdaptiveForgettingCalculator(ForgettingScoreCalculator):
    def __init__(self, model_dir, concept_difficulty, device="cpu"):
        # concept_difficulty: {concept_id: difficulty_level}
        # difficulty_level: 'easy', 'medium', 'hard'
        
        self.concept_difficulty = concept_difficulty
        self.tau_map = {
            'easy': 3 * 24 * 60,    # 3天
            'medium': 7 * 24 * 60,  # 7天
            'hard': 14 * 24 * 60    # 14天
        }
        
        # 使用默认τ初始化
        super().__init__(model_dir, tau=7*24*60, device=device)
    
    def calculate_forgetting_score(self, student_id, target_concept, current_time):
        # 根据concept难度动态调整τ
        difficulty = self.concept_difficulty.get(target_concept, 'medium')
        self.tau = self.tau_map[difficulty]
        
        return super().calculate_forgetting_score(student_id, target_concept, current_time)
```

## 📝 注意事项

1. **冷启动问题**：新学生或新concept需要至少一次答题记录
2. **时间戳精度**：使用毫秒级时间戳以保持精度
3. **模型依赖**：遗忘分数依赖于LPKT模型的预测准确性
4. **τ参数调优**：不同数据集和学习场景需要不同的τ值
5. **实时更新**：每次答题后应及时更新历史记录

## 🆘 常见问题

**Q: 遗忘分数为0是什么意思？**  
A: 表示学生刚刚学完（时间间隔为0）或者掌握非常好（预测概率接近1）

**Q: 如何处理学生从未学过的concept？**  
A: 返回None或error信息，建议先让学生学习该concept

**Q: τ设置太大或太小会怎样？**  
A: 
- τ太小：时间因素影响过大，可能过早推荐复习
- τ太大：时间因素影响太小，可能错过最佳复习时机

**Q: 可以用于其他KT模型吗？**  
A: 可以，只要模型能提供预测概率s_{t,c}即可

## 📚 参考

- Ebbinghaus遗忘曲线
- Spaced Repetition算法
- LPKT: Learning Process-consistent Knowledge Tracing

---

**立即尝试**：
```bash
cd /mnt/localssd/pykt-toolkit/examples
source activate pykt
python forgetting_score_calculator.py --mode demo
```

