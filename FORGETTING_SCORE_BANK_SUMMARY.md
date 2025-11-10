# 🎯 Forgetting Score Bank 生成总结

## ✅ 任务完成情况

### 成功完成：8/16 任务 (50%)

| 数据集 | LPKT | SimpleKT | DKT | AKT | 完成率 |
|--------|------|----------|-----|-----|-------|
| **ASSISTments2017** | ✅ | ❌ | ✅ | ✅ | 3/4 (75%) |
| **NIPS Task 3&4** | ❌ | ❌ | ✅ | ✅ | 2/4 (50%) |
| **Algebra2005** | ✅ | ❌ | ✅ | ✅ | 3/4 (75%) |
| **Bridge2Algebra2006** | ❌ | ❌ | ❌ | ❌ | 0/4 (0%) |
| **总计** | 2/4 | 0/4 | 3/4 | 3/4 | **8/16** |

---

## 📁 成功生成的文件

### ASSISTments2017 (3个模型)
```
/mnt/localssd/bank/forgetting/assist2017/
├── lpkt.json (1.9 MB, 341学生)
├── dkt.json (1.9 MB, 341学生)
└── akt.json (1.9 MB, 341学生)
```

### NIPS Task 3&4 (2个模型)
```
/mnt/localssd/bank/forgetting/nips_task34/
├── dkt.json (3.6 MB, 983学生)
└── akt.json (3.6 MB, 983学生)
```

### Algebra2005 (3个模型)
```
/mnt/localssd/bank/forgetting/algebra2005/
├── lpkt.json (663 KB, 114学生)
├── dkt.json (666 KB, 114学生)
└── akt.json (667 KB, 114学生)
```

### Bridge2Algebra2006 (0个模型)
```
❌ 所有模型都失败了
```

---

## 📊 数据格式

### JSON结构 ✅
```json
{
  "student_id": {
    "concept_text": {
      "s_tc": 0.4109388,          // 模型预测的答对概率
      "fs": 0.029075,              // Forgetting Score
      "level": "high",             // 基于dataset的level (low/medium/high)
      "last_response": 1,          // 最后一次答题结果
      "num_attempts": 5            // 尝试次数
    }
  }
}
```

### Level定义（基于整个dataset）
- **Low**: FS < 33rd percentile
- **Medium**: 33rd ≤ FS < 67th percentile
- **High**: FS ≥ 67th percentile

---

## ❌ 失败原因分析

### 1. SimpleKT (4/4 失败)
**错误信息：**
```
AttributeError: 'NoneType' object has no attribute 'load_state_dict'
The wrong model name was used...
```

**原因：** 模型加载失败，可能是配置文件或模型架构不匹配

**解决方案：** 需要检查SimpleKT的配置和checkpoint文件

### 2. Bridge2Algebra2006 (4/4 失败)
**LPKT错误：**
```
Expected all tensors to be on the same device, but found at least two devices, cuda:4 and cuda:0!
```

**原因：** CUDA设备不一致问题

**DKT/AKT：** 运行中或失败（未生成输出）

**解决方案：** 需要修复CUDA设备分配或强制CPU运行

### 3. NIPS Task 3&4 LPKT (1/1 失败)
**错误信息：** 同上CUDA设备问题

**解决方案：** 同上

---

## 📈 统计信息

### 成功处理的数据

| 数据集 | 学生数 | 模型数 | 总文件大小 |
|--------|--------|--------|-----------|
| ASSISTments2017 | 341 | 3 | 5.7 MB |
| NIPS Task 3&4 | 983 | 2 | 7.2 MB |
| Algebra2005 | 114 | 3 | 2.0 MB |
| **总计** | **1,438** | **8** | **14.9 MB** |

### 每个模型的成功率

| 模型 | 成功 | 失败 | 成功率 |
|------|------|------|--------|
| **LPKT** | 2 | 2 | 50% |
| **SimpleKT** | 0 | 4 | 0% |
| **DKT** | 3 | 1 | 75% ⭐ |
| **AKT** | 3 | 1 | 75% ⭐ |

---

## 🎯 实际可用性

### ✅ 三个数据集完全可用

**ASSISTments2017：** 
- ✅ LPKT, DKT, AKT (3个模型)
- 可以对比不同模型的FS预测

**Algebra2005：**
- ✅ LPKT, DKT, AKT (3个模型)
- 可以对比不同模型的FS预测

**NIPS Task 3&4：**
- ✅ DKT, AKT (2个模型)
- 可以对比两个模型的FS预测

### ⚠️ Bridge2Algebra2006需要修复

所有模型都失败，需要：
1. 修复CUDA设备分配问题
2. 或者强制使用CPU运行
3. 检查模型配置

---

## 💡 使用示例

### 查询学生的Forgetting Score

```python
import json

# 加载LPKT的预测
with open('/mnt/localssd/bank/forgetting/assist2017/lpkt.json') as f:
    lpkt_fs = json.load(f)

# 查询特定学生
student_id = "7"
if student_id in lpkt_fs:
    print(f"Student {student_id} FS:")
    for concept, info in lpkt_fs[student_id].items():
        if info['level'] == 'high':
            print(f"  {concept}: FS={info['fs']:.3f} (需要重点复习)")
```

### 对比不同模型的预测

```python
import json

# 加载三个模型
datasets = ['lpkt', 'dkt', 'akt']
models = {}
for model in datasets:
    with open(f'/mnt/localssd/bank/forgetting/assist2017/{model}.json') as f:
        models[model] = json.load(f)

# 对比特定学生
student_id = "7"
for model_name, data in models.items():
    if student_id in data:
        avg_fs = sum(c['fs'] for c in data[student_id].values()) / len(data[student_id])
        print(f"{model_name.upper()}: 平均FS = {avg_fs:.3f}")
```

---

## 📂 文件位置总览

```
/mnt/localssd/bank/forgetting/
├── assist2017/
│   ├── lpkt.json ✅
│   ├── dkt.json ✅
│   └── akt.json ✅
├── nips_task34/
│   ├── dkt.json ✅
│   └── akt.json ✅
├── algebra2005/
│   ├── lpkt.json ✅
│   ├── dkt.json ✅
│   └── akt.json ✅
└── bridge2algebra2006/
    └── (空)
```

---

## 🚀 后续步骤

### 选项1：使用已有的8个模型 ✅

**优点：**
- 已经有3个数据集完全可用
- 每个数据集有2-3个模型可对比
- DKT和AKT表现最稳定（75%成功率）

**推荐：** 直接使用现有结果开始分析

### 选项2：修复失败的任务

**需要修复：**
1. **SimpleKT (4个)**: 检查模型配置和加载逻辑
2. **Bridge2Algebra2006 (4个)**: 修复CUDA设备问题
3. **NIPS LPKT (1个)**: 修复CUDA设备问题

**工作量：** 中等，需要调试模型加载和设备分配

### 选项3：补充运行Bridge2Algebra2006

使用CPU模式重新运行Bridge2Algebra2006的所有模型：

```bash
cd /mnt/localssd/pykt-toolkit/examples

# 强制CPU运行
CUDA_VISIBLE_DEVICES="" python calc_fs_all_data_simple.py \
    --dataset=bridge2algebra2006 \
    --model=lpkt \
    --save_dir=saved_model/bridge2algebra2006_lpkt_... \
    --gpu=0
```

---

## ✅ 总结

### 成功的部分 ✅
- **8个模型**成功生成了Forgetting Score
- 覆盖了**3个数据集**的**1,438个学生**
- **DKT和AKT模型最稳定**（75%成功率）
- 数据格式完全符合要求（student_id -> concept_text -> metrics）
- Level基于整个dataset定义（low/medium/high）

### 待改进的部分 ⚠️
- SimpleKT完全失败（模型加载问题）
- Bridge2Algebra2006完全失败（CUDA问题）
- NIPS Task 3&4缺少LPKT

### 推荐行动 🎯
**立即可用：** 使用已有的8个模型开始分析

**可选优化：** 修复Bridge2Algebra2006和SimpleKT（如果需要完整覆盖）

---

## 📞 相关文件

- **运行脚本**: `/mnt/localssd/run_all_fs_parallel.sh`
- **监控脚本**: `/mnt/localssd/monitor_fs_parallel.sh`
- **计算脚本**: `/mnt/localssd/pykt-toolkit/examples/calc_fs_all_data_simple.py`
- **日志目录**: `/mnt/localssd/pykt-toolkit/examples/log_fs_all_*.txt`
- **输出目录**: `/mnt/localssd/bank/forgetting/`

