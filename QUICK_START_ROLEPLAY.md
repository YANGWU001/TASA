# 🚀 学生Role-Play评估系统 - 快速开始指南

## ✅ 第一步：配置API凭证

编辑 `roleplay_config.py` 文件：

```python
ENDPOINT = "http://your-endpoint:4000"  # 你的endpoint
API_KEY = "sk-your-key-here"             # 你的API key
```

获取凭证方式：
- Slack命令: `/get-llm-cred`
- 参考: `use_gpt/bear/example.py`

## 🧪 第二步：快速测试

```bash
cd /mnt/localssd
python test_roleplay_single.py
```

这会测试学生1，回答3个问题，查看效果。

**预期输出：**
```
学生Role-Play快速测试
================================================================================

📖 加载数据...

👤 学生信息:
   学生ID: 1
   Concept: transformations-rotations
   准确率: 3/11 = 27.3%
   距离上次: 2.0 分钟

📝 问题数量: 10

示例问题:
   1. What is a rotation in geometry, and how does it differ from other transformations?
   2. If a shape is rotated 90 degrees clockwise about the origin, what happens to the coordinates of its points?
   3. Describe the characteristics that remain unchanged after a rotation transformation.

🎭 构建学生人设...

System Prompt预览:
--------------------------------------------------------------------------------
You are role-playing as a student with the following characteristics:

**Student Profile:**
- Student shows needs improvement of 'transformations-rotations' with 27% accuracy over 11 attempts.
...
```

## 📊 第三步：完整评估单个学生

```bash
python student_roleplay_evaluation.py
```

结果保存在：`bank/evaluation_results/assist2017/student_1_concept_3.json`

## 🔄 第四步：批量评估

```bash
# 评估10个学生
python batch_evaluate_students.py --dataset assist2017 --num 10 --sample first

# 评估所有学生
python batch_evaluate_students.py --dataset assist2017
```

## 📈 查看结果

### 单个学生结果

```bash
cat bank/evaluation_results/assist2017/student_1_concept_3.json
```

关键字段：
- `original_accuracy`: 0.27 (27%)
- `roleplay_score`: 3.5/10
- `feedback`: "Student shows partial understanding..."

### 汇总报告

```bash
cat bank/evaluation_results/assist2017/summary_report.csv
```

使用Python/Excel查看分析：
```python
import pandas as pd
df = pd.read_csv('bank/evaluation_results/assist2017/summary_report.csv')
print(df.describe())
```

## 🎯 系统工作原理

```
Session数据 (学生历史记录)
    ↓
构建Persona (准确率、最近表现)
    ↓
gpt-oss-120b Role-play学生
    ↓
生成10个答案
    ↓
gpt-4o-mini批改答案
    ↓
得分 (0-10) + 反馈
```

## 💡 示例场景

### 低准确率学生 (27%)

**Persona:**
"Student shows needs improvement of 'transformations-rotations' with 27% accuracy over 11 attempts."

**问题：** "What is a rotation in geometry?"

**Role-play答案：**
"Um, rotation is when you turn something around? I think it's different from moving it because... well, you're spinning it instead of just sliding it. Not totally sure though."

**得分：** 0.5/1 (部分正确)

### 高准确率学生 (85%)

**Persona:**
"Student demonstrates strong mastery of 'transformations-rotations' with 85% accuracy over 20 attempts."

**问题：** "What is a rotation in geometry?"

**Role-play答案：**
"A rotation is a transformation that turns a figure around a fixed point called the center of rotation by a specified angle. Unlike translations which slide a figure, rotations preserve the size and shape of the figure while changing its orientation."

**得分：** 1.0/1 (完全正确)

## 🔧 常见问题

### Q: API调用失败？
A: 检查 `roleplay_config.py` 中的ENDPOINT和API_KEY是否正确。

### Q: 结果与预期不符？
A: 调整 `STUDENT_TEMPERATURE` 参数（在roleplay_config.py中）。

### Q: 处理速度太慢？
A: 调整 `SLEEP_BETWEEN_QUESTIONS` 减少等待时间（但注意rate limit）。

### Q: 批改结果不一致？
A: 降低 `GRADER_TEMPERATURE` 使批改更稳定。

## 📊 预期相关性

好的persona构建应该显示：
- **原始准确率 vs Role-play准确率**: 相关系数 > 0.6
- **低准确率学生** (<30%): Role-play得分应 < 4/10
- **高准确率学生** (>70%): Role-play得分应 > 7/10

## 📁 文件结构

```
/mnt/localssd/
├── roleplay_config.py              # 配置文件 (你需要编辑这个)
├── student_roleplay_evaluation.py  # 核心评估逻辑
├── batch_evaluate_students.py      # 批量评估
├── test_roleplay_single.py         # 快速测试
├── ROLEPLAY_README.md              # 详细文档
├── QUICK_START_ROLEPLAY.md         # 这个文件
└── bank/
    ├── session/{dataset}/          # 输入：Session数据
    ├── test_data/{dataset}/        # 输入：题库
    └── evaluation_results/{dataset}/ # 输出：评估结果
```

## 🎓 下一步

1. ✅ 配置API凭证
2. ✅ 运行快速测试
3. ✅ 查看结果是否合理
4. ✅ 批量评估少量样本 (--num 5)
5. ✅ 分析相关性
6. ✅ 全量评估

## 📞 需要帮助？

查看详细文档：`ROLEPLAY_README.md`

