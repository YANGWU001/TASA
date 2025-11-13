# 学生Role-Play评估系统

这个系统让LLM扮演学生，根据他们的历史表现来回答问题，然后用另一个LLM来评估答案的正确性。

## 📋 系统架构

1. **Student Role-Play Model**: `gpt-oss-120b` - 扮演学生回答问题
2. **Grader Model**: `gpt-4o-mini` - 批改答案并给出分数

## 🚀 快速开始

### 1. 配置API凭证

编辑脚本中的API配置：

```python
ENDPOINT = "<Insert your endpoint>"
API_KEY = "<Insert your key>"
```

### 2. 测试单个学生 (推荐先运行这个)

```bash
cd /mnt/localssd
python test_roleplay_single.py
```

这会：
- 加载学生1的session数据
- 显示学生信息和persona
- 让LLM role-play学生回答前3个问题
- 批改并显示结果

### 3. 评估单个完整session

```bash
python student_roleplay_evaluation.py
```

这会评估学生1的所有10个问题，并保存完整结果。

### 4. 批量评估多个学生

```bash
# 评估assist2017数据集的前10个学生
python batch_evaluate_students.py --dataset assist2017 --num 10 --sample first

# 评估所有学生
python batch_evaluate_students.py --dataset assist2017

# 随机采样评估20个学生
python batch_evaluate_students.py --dataset assist2017 --num 20 --sample random
```

## 📁 输出结果

### 单个学生结果

保存在 `/mnt/localssd/bank/evaluation_results/{dataset}/student_{id}_concept_{cid}.json`

```json
{
  "student_id": "1",
  "concept_id": "3",
  "concept_text": "transformations-rotations",
  "original_accuracy": 0.27,
  "roleplay_score": 3.5,
  "individual_scores": [0.5, 0, 1, 0, 0.5, 0, 0.5, 0, 1, 0],
  "feedback": "Student shows partial understanding...",
  "answers": [...]
}
```

### 批量评估汇总

保存在 `/mnt/localssd/bank/evaluation_results/{dataset}/`

- `summary_report.csv` - CSV格式的统计表格
- `all_results.json` - 完整的JSON结果

## 🎭 系统工作流程

### Step 1: 构建学生Persona

基于session数据构建system prompt：

```
You are role-playing as a student with the following characteristics:

**Student Profile:**
- Student shows needs improvement of 'transformations-rotations' with 27% accuracy over 11 attempts.
- Current accuracy on 'transformations-rotations': 27.3%
- Time since last attempt on this concept: 2.0 minutes

**Recent Performance History:**
- The student correctly applied transformations-rotations knowledge. (Result: correct)
- The student answered a transformations-rotations question accurately. (Result: correct)
- The student struggled to apply transformations-rotations. (Result: incorrect)
...

**Your Role:**
You should answer the following questions AS THIS STUDENT would answer them...
```

### Step 2: 学生回答问题

LLM role-play学生回答10个问题，例如：

**Question**: "What is a rotation in geometry, and how does it differ from other transformations?"

**Student Answer**: "Um, rotation is when you turn something around? I think it's different from moving it because... well, you're spinning it instead of just sliding it. Not totally sure though."

### Step 3: 批改答案

另一个LLM批改所有答案并给出：
- 每题得分 (0, 0.5, 或 1)
- 总分 (0-10的小数)
- 整体反馈

## 📊 评估指标

- **Original Accuracy**: 学生在实际历史记录中的准确率
- **Role-play Score**: LLM扮演学生后获得的分数 (0-10)
- **Role-play Accuracy**: Role-play Score / 10
- **Correlation**: 原始准确率与role-play准确率的相关性

## 🎯 使用场景

1. **验证Persona质量**: 检查构建的persona是否能反映学生真实水平
2. **生成合成数据**: 为没有完整答案记录的学生生成合理的答案
3. **难度评估**: 通过不同水平学生的表现评估题目难度
4. **模型一致性**: 检验LLM是否能准确扮演不同水平的学生

## 📝 自定义选项

### 修改模型温度

在 `get_student_answers()` 中：

```python
temperature=0.7,  # 增加随机性模拟真实学生
```

### 修改批改标准

在 `grade_answers()` 中调整grading_prompt。

### 添加更多context

在 `build_student_system_prompt()` 中添加更多信息：
- Forgetting curve数据
- 其他concept的表现
- 学习时间分布

## 🔧 故障排除

### API错误

检查endpoint和API key是否正确配置。

### Rate Limiting

在 `get_student_answers()` 中增加 `time.sleep()` 的时间。

### 内存不足

批量评估时减少 `--num` 参数的值。

## 📈 预期结果

对于表现较差的学生（准确率<30%），role-play得分应该也较低。
对于表现较好的学生（准确率>70%），role-play得分应该较高。

**相关性分析**: 期望原始准确率与role-play准确率有较强的正相关性（correlation > 0.6）。

## 🔄 工作流程图

```
Session Data → Build Persona → LLM Role-Play → Generate Answers
                                                      ↓
Grading Results ← LLM Grader ← Collect Answers ← Save Answers
       ↓
Save Results (JSON + CSV)
```

## 📚 相关文件

- `student_roleplay_evaluation.py` - 核心评估逻辑
- `batch_evaluate_students.py` - 批量评估工具
- `test_roleplay_single.py` - 快速测试脚本
- `bank/test_data/{dataset}/concept_questions.json` - 题库
- `bank/session/{dataset}/*.json` - Session数据

## 💡 提示

1. 先用 `test_roleplay_single.py` 测试，确认系统正常工作
2. 批量评估前先评估少量样本（--num 5）检查结果
3. 查看生成的答案是否合理反映学生水平
4. 分析相关性指标判断persona构建质量

