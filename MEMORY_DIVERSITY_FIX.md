# Memory生成多样性改进

## 🔍 问题诊断

用户正确指出：原来的"Vary your language"指令在system prompt中**几乎没有作用**，因为：

1. **每个学生独立处理**：不同学生之间的LLM调用互相独立
2. **批次独立处理**：每批10个事件，批次之间互相独立  
3. **无记忆机制**：GPT无法"记住"之前生成的内容

结果：虽然单批内部有一定变化，但**跨批次、跨学生会出现大量重复**。

---

## ✅ 解决方案：批次级风格随机化

### 核心改进

在每批次的user prompt中，**动态注入**6种不同的风格提示：

```python
style_hints = [
    "Use active voice and action verbs like 'tackled', 'mastered', 'struggled with'.",
    "Focus on the learning process: 'attempted', 'worked through', 'practiced'.",
    "Emphasize outcomes: 'succeeded in', 'got right', 'missed', 'nailed'.",
    "Use casual academic tone: 'answered correctly', 'made an error on', 'solved'.",
    "Be descriptive: 'demonstrated understanding', 'showed proficiency', 'had difficulty'.",
    "Mix metaphors: 'cracked', 'fumbled', 'aced', 'stumbled on'."
]

# 为每批选择不同风格
style_idx = (batch_idx + hash(uid)) % len(style_hints)
current_style = style_hints[style_idx]
```

### 效果

- ✅ **同一学生的不同批次**：使用不同风格（batch_idx递增）
- ✅ **不同学生**：使用不同风格分布（hash(uid)不同）
- ✅ **全局多样性**：6种风格 × 批次数 = 大量变化

---

## 📊 预期效果示例

**学生A - 批次1**（风格：active voice）:
- "The student tackled an equation-solving problem."
- "They mastered the concept of proportion."

**学生A - 批次2**（风格：learning process）:
- "The student attempted a geometry question."
- "They worked through an area-perimeter problem."

**学生B - 批次1**（风格：outcomes）:
- "The student succeeded in solving the equation."
- "They nailed the proportion concept."

---

## 🎯 关键参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `batch_size` | 10 | 每批处理的事件数 |
| `style_hints` | 6种 | 风格提示种类 |
| `temperature` | 0.7 | Memory生成温度 |
| 选择算法 | `(batch_idx + hash(uid)) % 6` | 确定性随机 |

---

## 🚀 部署状态

- ✅ 代码已更新：`create_student_bank_final.py`
- ✅ 进程已重启：PID 177299
- ⏳ 预计完成时间：~10小时
- 📁 输出位置：`/mnt/localssd/bank/`

---

## 🔍 验证方法

等待处理完成后，抽样检查不同学生的memory文件：

```bash
# 查看不同学生的memory
head -30 bank/memory/assist2017/data/1188.json
head -30 bank/memory/assist2017/data/631.json
head -30 bank/memory/assist2017/data/1365.json

# 统计描述的多样性
grep "description" bank/memory/assist2017/data/*.json | sort | uniq -c | sort -nr | head -20
```

预期结果：描述用词和句式有明显变化，不再重复"Student answered a question on X incorrectly"。

