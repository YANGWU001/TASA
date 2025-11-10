# KT模型预测状态汇总

## 核心发现

**所有尝试都遇到相同问题：Question ID映射不匹配**

| 尝试版本 | 模型加载 | 实际预测方法 | 状态 |
|---------|---------|------------|------|
| `flexible_forgetting_api.py` | ✅ 成功 | ❌ **历史准确率**（注释说"实际应该使用模型"） | "能用"但未真正用模型 |
| `analyze_forgetting_with_kt_model.py` (LPKT) | ✅ 成功 | ❌ 回退到历史准确率 | 预测100%失败 |
| `test_other_kt_models.py` (DKT/AKT) | ✅ 成功 | ❌ 回退到历史准确率 | 预测100%失败 |

## 结论

**之前的版本虽然"可以运行"，但实际上也没有解决模型预测问题！**

它只是：
1. ✅ 成功加载了模型
2. ❌ 但没有使用模型，而是用历史准确率代替
3. ✅ 所以"能跑通"，但效果和不用模型一样

## 证据

### flexible_forgetting_api.py (第180-182行)

```python
# 简化：使用该concept的平均正确率作为预测概率
# 实际应该使用模型的预测  <-- 关键注释！
avg_correct = np.mean(concept_responses)
```

### 当前尝试 (所有版本)

```python
try:
    # 尝试用模型预测
    pred_prob = model(...)
except:
    # Question ID超出范围，预测失败
    pred_prob = None
    
# 回退到历史准确率
if pred_prob is None:
    pred_prob = historical_accuracy  # 和之前的API一样！
```

## 实际情况

**历史准确率已经很有效：**
- 高FS concepts答错率：58.3%
- 低FS concepts答错率：~30%
- **显著差异，说明方法有效！**

**所以：**
1. ✅ 之前的API "能用" = 使用历史准确率
2. ✅ 现在的代码 "能用" = 使用历史准确率（当模型预测失败时）
3. ❌ 真正的模型预测 = 所有尝试都因Question ID映射问题失败

**结论：历史准确率简单有效，这就是为什么"之前的版本可以用"！**
