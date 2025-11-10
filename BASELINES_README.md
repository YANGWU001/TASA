# Baseline Methods Implementation

实现了4种baseline方法用于对比TASA系统的效果。

## 📊 Baseline方法

### 1. Vanilla ICL (In-Context Learning)
**文件**: `baseline_vanilla_icl.py`

**特点**:
- 只使用persona description
- 不涉及knowledge tracing和memory
- 最简单的baseline

### 2. MathChat
**文件**: `baseline_mathchat.py`

**特点**:
- 带calculator功能 (`<calculate>expression</calculate>`)
- 解释学生答案 + 生成新问题
- 可以进行数值计算

### 3. TutorLLM
**文件**: `baseline_tutorllm.py`

**特点**:
- 使用persona + 3条相关memory (RAG)
- 不考虑knowledge tracing
- 比Vanilla ICL多了memory信息

### 4. PSS-MV (Personalized Student Style - Memory View)
**文件**: `baseline_pssmv.py`

**特点**:
- 先用LLM从memory总结learning style
- 根据learning style生成个性化tutoring
- 关注学习风格适配

## 🚀 使用方法

### 快速测试单个baseline

```bash
# 给脚本执行权限
chmod +x test_baseline.sh

# 测试Vanilla-ICL (前3个学生)
./test_baseline.sh Vanilla-ICL assist2017

# 测试其他方法
./test_baseline.sh MathChat algebra2005
./test_baseline.sh TutorLLM bridge2006
./test_baseline.sh PSS-MV assist2017
```

### 评估单个baseline on 单个数据集

```bash
# 评估Vanilla-ICL on assist2017的所有符合条件的学生
/opt/venv/bin/python3 evaluate_baselines.py \
    --method Vanilla-ICL \
    --dataset assist2017 \
    --max-workers 10

# 评估其他组合
/opt/venv/bin/python3 evaluate_baselines.py \
    --method TutorLLM \
    --dataset algebra2005 \
    --max-workers 10
```

### 运行所有baselines on 所有数据集

```bash
# 运行所有方法在所有数据集上
/opt/venv/bin/python3 run_all_baselines.py

# 只运行特定方法
/opt/venv/bin/python3 run_all_baselines.py \
    --methods Vanilla-ICL TutorLLM \
    --datasets assist2017 algebra2005

# 只运行特定数据集
/opt/venv/bin/python3 run_all_baselines.py \
    --datasets assist2017 \
    --max-workers 10
```

## 📂 数据结构

### Dialogue保存位置
```
bank/dialogue/
├── Vanilla-ICL/{dataset}/{student_id}-{concept}.json
├── MathChat/{dataset}/{student_id}-{concept}.json
├── TutorLLM/{dataset}/{student_id}-{concept}.json
└── PSS-MV/{dataset}/{student_id}-{concept}.json
```

### 评估结果保存位置
```
bank/evaluation_results/
├── Vanilla-ICL/{dataset}/
│   ├── student_{id}.json
│   └── overall.json
├── MathChat/{dataset}/
│   ├── student_{id}.json
│   └── overall.json
├── TutorLLM/{dataset}/
│   ├── student_{id}.json
│   └── overall.json
└── PSS-MV/{dataset}/
    ├── student_{id}.json
    └── overall.json
```

### Overall.json格式
```json
{
  "dataset": "assist2017",
  "method": "Vanilla-ICL",
  "num_students": 189,
  "overall": {
    "avg_learning_gain": 0.35,
    "std_learning_gain": 0.22,
    "median_learning_gain": 0.30,
    "min_gain": 0.0,
    "max_gain": 0.85
  },
  "students": [...]
}
```

## ⏱️ 预计时间

基于assist2017的经验 (189个学生):

| 方法 | 每学生时间 | 189个学生 (10并发) |
|------|-----------|-------------------|
| Vanilla-ICL | ~6分钟 | ~2小时 |
| MathChat | ~6分钟 | ~2小时 |
| TutorLLM | ~6.5分钟 | ~2小时 |
| PSS-MV | ~7分钟 | ~2.2小时 |

**所有4个方法在3个数据集**: 约24-26小时 (串行)

## 📊 当前数据集状态

| 数据集 | Pre-test | 符合条件(20-60%) | TASA完成 |
|--------|---------|-----------------|---------|
| assist2017 | ✅ | 189个 | ✅ (Gain=41.9%) |
| algebra2005 | ✅ | 29个 | ✅ (运行中) |
| bridge2006 | ✅ | 46个 | ✅ (运行中) |
| nips_task34 | 🔄 | ? | ⏳ |

## 🎯 推荐执行流程

### 方案1: 快速验证 (推荐先做)
```bash
# 1. 测试每个baseline是否能正常运行 (各3个学生)
./test_baseline.sh Vanilla-ICL assist2017
./test_baseline.sh MathChat assist2017
./test_baseline.sh TutorLLM assist2017
./test_baseline.sh PSS-MV assist2017

# 2. 如果都成功，开始完整评估
```

### 方案2: 完整评估
```bash
# 在3个数据集上运行所有baselines
nohup /opt/venv/bin/python3 run_all_baselines.py \
    --datasets assist2017 algebra2005 bridge2006 \
    --max-workers 10 \
    > logs/all_baselines.log 2>&1 &

# 预计时间: 约24-26小时
```

### 方案3: 分批运行
```bash
# 先运行Vanilla-ICL和MathChat (较快)
nohup /opt/venv/bin/python3 run_all_baselines.py \
    --methods Vanilla-ICL MathChat \
    --max-workers 10 \
    > logs/baselines_batch1.log 2>&1 &

# 再运行TutorLLM和PSS-MV
nohup /opt/venv/bin/python3 run_all_baselines.py \
    --methods TutorLLM PSS-MV \
    --max-workers 10 \
    > logs/baselines_batch2.log 2>&1 &
```

## 📈 结果对比

完成后可以比较所有方法的Learning Gain:

```bash
# 查看所有方法的结果
python3 << 'EOF'
import json
import os

methods = ['Vanilla-ICL', 'MathChat', 'TutorLLM', 'PSS-MV', 'TASA-best-of-2']
datasets = ['assist2017', 'algebra2005', 'bridge2006']

print(f"{'方法':<20s} {'数据集':<15s} {'学生数':<10s} {'平均Gain'}")
print("-"*80)

for method in methods:
    for dataset in datasets:
        overall_file = f'/mnt/localssd/bank/evaluation_results/{method}/{dataset}/overall.json'
        if os.path.exists(overall_file):
            with open(overall_file) as f:
                data = json.load(f)
            print(f"{method:<20s} {dataset:<15s} {data['num_students']:<10d} {data['overall']['avg_learning_gain']*100:.1f}%")
        else:
            print(f"{method:<20s} {dataset:<15s} {'N/A':<10s} N/A")
EOF
```

## 💡 注意事项

1. **模型加载**: TutorLLM和PSS-MV需要加载BGE模型，初始化时间较长
2. **并行度**: 建议max_workers=10，太高可能导致API限流
3. **断点续传**: 如果dialogue已存在会自动跳过，可以重新运行失败的任务
4. **日志文件**: 所有日志保存在`logs/`目录

## 🐛 故障排查

如果遇到问题:

1. 查看日志: `tail -f logs/{method}_{dataset}.log`
2. 测试单个学生: `./test_baseline.sh {method} {dataset}`
3. 检查API配置: `tasa_config.py`中的ENDPOINT和API_KEY
4. 检查模型路径: BGE模型需要能访问Hugging Face

## ✅ 完成检查清单

- [ ] 快速测试所有4个baseline (各3个学生)
- [ ] 确认所有baseline能正常运行
- [ ] 开始完整评估
- [ ] 等待评估完成 (~24小时)
- [ ] 查看结果对比
- [ ] 生成对比图表

