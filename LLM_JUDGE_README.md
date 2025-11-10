# LLM as Judge: Personalization Evaluation

## 📋 功能说明

使用**gpt-5-chat**作为judge，评估不同tutoring方法的dialogue个性化程度。

### 比较逻辑
- **Target Methods**: 各种tutoring方法（TASA, TutorLLM, PSS-MV, MathChat等）
- **Baseline**: Vanilla-ICL（三种backbone版本）
- **评估标准**: 根据学生的persona和memory，判断哪个dialogue更个性化
- **输出**: Win Rate = Target胜利次数 / 总比较次数

### 评估维度
1. **Adaptation to Student's Level**: 难度和节奏是否适合学生
2. **Relevance to Past Learning**: 是否利用学生的历史学习经验
3. **Pedagogical Alignment**: 教学风格是否匹配学生需求
4. **Appropriate Scaffolding**: 支持程度是否合适
5. **Engagement Strategy**: 策略是否对该学生有效

## 🚀 使用方法

### 1. 测试单个学生（快速验证）
```bash
cd /mnt/localssd
python3 test_llm_judge.py
```

### 2. 运行完整评估（所有methods × 所有datasets）
```bash
cd /mnt/localssd
nohup python3 llm_as_judge_personalization.py > logs/llm_judge.log 2>&1 &
```

### 3. 评估特定method
```python
from llm_as_judge_personalization import batch_judge

# 例如：只评估TASA-llama在assist2017上
result = batch_judge('TASA-llama', dataset='assist2017', max_workers=20)
```

## 📊 输出结果

### 结果文件位置
```
/mnt/localssd/llm_judge_results/
├── TASA-llama_vs_Vanilla-ICL-llama_assist2017.json
├── TutorLLM_vs_Vanilla-ICL_assist2017.json
└── ...
```

### 结果格式
```json
{
  "target_method": "TASA-llama",
  "baseline_method": "Vanilla-ICL-llama",
  "dataset": "assist2017",
  "backbone": "llama",
  "total_comparisons": 10,
  "target_wins": 7,
  "baseline_wins": 2,
  "ties": 1,
  "win_rate": 0.7,
  "detailed_results": [...]
}
```

## 🎯 Target Methods列表

### 按Backbone分组

**GPT-oss-120b** (无后缀):
- Vanilla-ICL
- TutorLLM
- PSS-MV
- MathChat

**Llama3.1-8B-Instruct** (-llama):
- Vanilla-ICL-llama
- TutorLLM-llama
- PSS-MV-llama
- MathChat-llama
- TASA-llama
- TASA-woForgetting-llama
- TASA-woMemory-llama
- TASA-woPersona-llama

**Qwen3-4B-Instruct** (-qwen):
- Vanilla-ICL-qwen
- TutorLLM-qwen
- PSS-MV-qwen
- MathChat-qwen
- TASA-lambda0.5-qwen

**GPT Lambda Ablation**:
- TASA-lambda0.5-gpt

## ⚙️ 配置参数

- **Judge Model**: gpt-5-chat
- **Temperature**: 0.0 (确定性输出)
- **Max Tokens**: 无限制（允许完整输出长dialogue分析）
- **Max Workers**: 20（并行评估20个学生）

## 📈 预计时间

- **单个学生**: ~30-60秒（取决于dialogue长度）
- **单个method×dataset**: ~5-15分钟（10个学生 × 30-60秒 / 20 workers）
- **所有methods×datasets**: ~2-4小时

## 🔍 Judge Prompt核心逻辑

Judge会收到：
1. 学生的persona（学习风格、历史表现）
2. 学生的memory（过去的学习记录）
3. Target dialogue（格式化为Student/Tutor交替）
4. Baseline dialogue（格式化为Student/Tutor交替）

然后判断哪个dialogue在以下方面更好：
- 是否针对该学生的特点调整教学
- 是否利用了学生的历史学习经验
- 是否采用了适合该学生的教学策略

输出格式：
```
Winner: [A or B or Tie]
Reasoning: [详细分析]
Confidence: [High/Medium/Low]
```

## 📝 注意事项

1. **相同backbone比较**: Target和baseline必须使用相同的LLM backbone
2. **Dialogue格式**: 自动格式化为"Student: ...\nTutor: ..."
3. **缺失数据处理**: 如果dialogue文件不存在，该学生会被跳过
4. **Token限制**: 不设置max_tokens，允许judge充分分析长dialogue

## 🛠️ 故障排查

### 问题1: dialogue文件找不到
```bash
# 检查dialogue目录结构
ls -la /mnt/localssd/bank/dialogue/TASA-llama/assist2017/
```

### 问题2: API调用失败
```bash
# 检查环境变量
echo $API_KEY
echo $ENDPOINT
```

### 问题3: 结果解析失败
查看logs/llm_judge.log中的详细错误信息

