# Multi-Backbone Experiment Plan

## 📋 实验概览

### 目标
1. 测试不同Forgetting Score Method对TASA效果的影响
2. 在Llama-3.1-8B和Qwen3-4B上运行TASA和Baselines
3. 对比GPT-OSS-120B、Llama、Qwen三种backbone的效果

### 实验配置
- **Datasets**: assist2017, algebra2005, bridge2006, nips_task34
- **TASA Backbones**: gpt-oss-120b, llama-3.1-8b, qwen3-4b
- **Baseline Methods**: Vanilla-ICL, MathChat, TutorLLM, PSS-MV
- **Forgetting Score Methods**: simple_time, history, lpkt, dkt, akt, simplekt
- **Max Workers**: TASA=30, Baselines=40

## 🔧 已创建的文件

### 1. `/mnt/localssd/llm_client.py`
**作用**: 统一的LLM客户端接口
- 支持GPT、Llama、Qwen三种backbone
- 自动处理不同API格式
- 统一的chat_completion接口

### 2. `/mnt/localssd/tasa_config.py` (已修改)
**新增配置**:
```python
FORGETTING_SCORE_METHOD = "simple_time"  # 可选: history, lpkt, dkt, akt, simplekt
```

### 3. `/mnt/localssd/tasa_rewrite.py` (已修改)
**改进**:
- 支持从session的methods中读取对应method的FS值和level
- Level映射: medium → moderate
- Prompt更新: 说明FS范围(0-1)和含义(越大越遗忘)

**Prompt示例**:
```
Forgetting Score: 0.3294 (range: 0-1, where higher values indicate more forgetting)
Forgetting Level: moderate - moderate (some knowledge retained)
```

### 4. `/mnt/localssd/test_forgetting_methods.py`
**作用**: 测试不同FS method在llama上的效果
- 自动测试6种FS method
- 在所有4个dataset上运行
- 自动选出最好的method
- 保存结果到`best_forgetting_method.txt`

### 5. `/mnt/localssd/run_all_experiments_with_backbones.py`
**作用**: Master实验脚本
**流程**:
1. 备份旧的GPT-OSS-120B结果
2. 在llama上测试所有FS method
3. 选出最好的FS method
4. 用最好的method运行所有实验:
   - GPT-OSS-120B (重新跑，使用新的FS method)
   - Llama-3.1-8B
   - Qwen3-4B
5. 生成对比报告

## 📊 Forgetting Score详解

### 当前实现 (已修改)

**Method数据格式** (来自session):
```json
{
  "history": {
    "s_tc": 0.6667,
    "fs": 0.3294,      // Forgetting Score: 0-1
    "level": "medium"  // low/medium/high
  },
  "lpkt": {...},
  "dkt": {...},
  "akt": {...},
  "simplekt": {...}
}
```

**使用方式**:
- **数值**: 直接使用method的`fs`值（0-1范围，越大越遗忘）
- **Level**: 使用method的`level`，映射medium→moderate
- **Prompt**: 同时提供数值和level

**Level映射**:
- Method: `low`, `medium`, `high`
- TASA: `low`, `moderate`, `high`
- 映射: `medium` → `moderate`

### Simple Time Method (旧版本)
```python
forgetting_score = 1 - 1 / (1 + delta_t_days / 7)
```
- 只依赖时间
- 不考虑学习质量
- 7天半衰期

## 🚀 执行流程

### 等PSS-MV完成后执行

#### Step 1: 备份当前GPT结果
```bash
# 自动执行，备份到带时间戳的目录
/mnt/localssd/bank/evaluation_results/TASA-best-of-2_OLD_simple_time_YYYYMMDD_HHMMSS/
```

#### Step 2: 测试FS Methods (Llama)
```bash
python3 /mnt/localssd/test_forgetting_methods.py
```
**输出**:
- `forgetting_method_comparison_llama-3.1-8b.json`: 详细结果
- `best_forgetting_method.txt`: 最好的method名称

#### Step 3: 运行所有实验
```bash
python3 /mnt/localssd/run_all_experiments_with_backbones.py
```

## 📁 结果存储结构

**新的命名规则**：根据backbone明确标注

```
/mnt/localssd/bank/evaluation_results/
# TASA结果
├── TASA-best-of-2/                    # GPT-OSS-120B (默认，不带标注)
├── TASA-best-of-2_OLD_simple_time_*/  # GPT (旧版本备份)
├── TASA-llama-best-of-2/              # Llama-3.1-8B
├── TASA-qwen-best-of-2/               # Qwen3-4B

# Baseline结果 (GPT-OSS-120B，默认不带标注)
├── Vanilla-ICL-conservative/
├── MathChat-conservative/
├── TutorLLM-conservative/
├── PSS-MV-conservative/

# Baseline结果 (Llama-3.1-8B)
├── Vanilla-ICL-llama-conservative/
├── MathChat-llama-conservative/
├── TutorLLM-llama-conservative/
├── PSS-MV-llama-conservative/

# Baseline结果 (Qwen3-4B)
├── Vanilla-ICL-qwen-conservative/
├── MathChat-qwen-conservative/
├── TutorLLM-qwen-conservative/
└── PSS-MV-qwen-conservative/
```

**命名规则说明**：
- **GPT-OSS-120B**: 不带标注（保持向后兼容）
- **Llama-3.1-8B**: 添加`-llama`后缀
- **Qwen3-4B**: 添加`-qwen`后缀
- 其他模型: 添加`-{backbone}`后缀

## ⏱️ 预计时间

### 单个Dataset (以assist2017为例，189学生)
- **TASA (1次)**: ~30分钟 (max_workers=30)
- **Baseline (1个method)**: ~31分钟 (max_workers=40)

### 总时间估算
1. **测试FS Methods** (llama, 6 methods × 4 datasets): ~12小时
2. **TASA All Backbones** (3 backbones × 4 datasets): ~6小时
3. **Baselines All Backbones** (3 backbones × 4 methods × 4 datasets): ~24小时

**总计**: ~42小时

## 📈 预期输出

### 1. FS Method对比报告
```json
{
  "simple_time": {"avg_gain": 0.34},
  "history": {"avg_gain": 0.36},
  "lpkt": {"avg_gain": 0.35},
  "dkt": {"avg_gain": 0.37},  // ← 假设最好
  "akt": {"avg_gain": 0.35},
  "simplekt": {"avg_gain": 0.33}
}
```

### 2. Backbone对比报告
```json
{
  "gpt-oss-120b": {
    "TASA": {"assist2017": 0.419, ...},
    "Baselines": {...}
  },
  "llama-3.1-8b": {...},
  "qwen3-4b": {...}
}
```

## ⚠️ 注意事项

1. **Baseline不依赖FS Method**: Baseline只改TUTOR_MODEL
2. **GPT需要重跑**: 旧版本用的是simple_time，新版本用最好的method
3. **API URLs**: Llama和Qwen需要确保ngrok URLs可用
4. **并发控制**: TASA=30, Baselines=40，避免API限流
5. **错误处理**: 如果某个method不存在，自动fallback到simple_time

## ✅ TODO

- [x] 创建LLM Client
- [x] 修改TASA Config支持FS Method
- [x] 修改TASA Rewrite使用Method FS
- [x] 创建FS Method测试脚本
- [x] 创建Master实验脚本
- [ ] 创建Baseline with Backbone脚本
- [ ] 等待PSS-MV完成
- [ ] 执行实验

## 🔍 监控命令

```bash
# 查看当前baseline进度
tail -f /mnt/localssd/logs/baselines_max40_v4.log

# 查看进程
ps aux | grep baseline_evaluation

# 查看GPU使用
nvidia-smi

# 查看FS method测试进度
tail -f /mnt/localssd/logs/TASA_llama-3.1-8b_*_*.log
```

