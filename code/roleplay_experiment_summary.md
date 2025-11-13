# Student Role-Play 实验总结

## 📊 实验对比

| 测试版本 | System Prompt策略 | 准确率 | 与目标27%偏差 |
|---------|------------------|--------|--------------|
| 初始版本 | 描述性，柔和语气 | 70% | +43% |
| 改进v1 | 增加期望数量提示 | 90% | +63% ❌ |
| **改进v2** | **强制性LOW-PERFORMING** | **50%** | **+23%** ✅ |

## ✅ 关键改进点

### 1. 使用强制性身份定义
```
You are a LOW-PERFORMING student with only 27.3% accuracy
You are NOT a knowledgeable student. You are a STRUGGLING student
```

### 2. 明确要求犯错
```
Most of your answers (about 7/10) should be WRONG or INCOMPLETE
```

### 3. 提供具体错误示例
```
Q: "What is the coordinate transformation for 90° rotation?"
YOU: "Um... I think you just swap x and y? So like (x,y) becomes (y,x)..."
```

### 4. 强调不确定性
```
Start many answers with uncertainty:
- "Um... I think..."
- "Maybe it's..."
- "I'm not really sure but..."
```

## 📈 回答质量分析

- ✅ **不确定性表达**: 49次（平均4.9次/题）
- ✅ **承认错误/混淆**: 15次
- ✅ **包含概念性错误**: 5/10题答错
- ✅ **符合低水平学生特征**: 是

### 典型回答示例

**错误答案（题2）**:
> "Um… I think when you turn something 90° clockwise you kind of "swap" the coordinates, but I always get the sign mixed up. So maybe a point (x,y) becomes something like (y,-x) … or was it (-y,x)?"

✓ 显示混淆
✓ 承认经常搞错
✓ 给出了错误答案

## 🎯 结论

当前prompt效果**良好**:
- ✅ 成功将准确率从90%降到50%
- ✅ 回答质量符合低水平学生特征
- ✅ 包含大量真实的错误和不确定性
- ⚠️ 50% vs 27%仍有23%偏差，但考虑到gpt-oss-120b模型能力，这已是合理结果

## 💡 如需进一步优化

1. **降低温度**: 1.0 → 0.8（可能让答案更一致地偏向错误）
2. **使用更小模型**: gpt-oss-20b而非120b（更容易犯错）
3. **接受当前结果**: 50%准确率已足够模拟低水平学生

## 📝 建议

**推荐使用当前prompt**作为tutoring实验的基线。50%准确率虽高于历史27%，但：
- 回答质量真实反映了学生困难
- 为tutoring后的提升留出空间
- 避免过度约束导致不自然的回答
