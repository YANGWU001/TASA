# Student Bank Creation - 运行命令

## 🚀 启动命令

### 方法1：使用启动脚本（推荐）
```bash
cd /mnt/localssd
bash START_BANK_CREATION.sh
```

### 方法2：直接nohup命令
```bash
cd /mnt/localssd
nohup bash -c "source /home/colligo/miniconda3/etc/profile.d/conda.sh && conda activate pykt && python -u create_student_bank_final.py" > bank_creation_full_final.log 2>&1 &
```

### 方法3：前台运行（可以看到实时输出）
```bash
cd /mnt/localssd
source /home/colligo/miniconda3/etc/profile.d/conda.sh
conda activate pykt
python -u create_student_bank_final.py
```

---

## 📊 任务信息

| 项目 | 值 |
|------|-----|
| 总学生数 | ~8,345 |
| 数据集 | ASSISTments2017, NIPS34, Algebra2005, Bridge2006 |
| 预计文件数 | ~41,725 |
| 预计大小 | ~3.7GB |
| 预计时间 | ~10小时 |

---

## 🔍 监控命令

### 查看实时日志
```bash
tail -f /mnt/localssd/bank_creation_full_final.log
```

### 查看进度（最后50行）
```bash
tail -50 /mnt/localssd/bank_creation_full_final.log
```

### 检查进程状态
```bash
ps aux | grep create_student_bank_final | grep -v grep
```

### 统计已生成文件数
```bash
# 总文件数
find /mnt/localssd/bank -type f | wc -l

# JSON文件数
find /mnt/localssd/bank -name "*.json" | wc -l

# Embedding文件数
find /mnt/localssd/bank -name "*.npz" | wc -l

# 各类型文件统计
echo "Persona data: $(find /mnt/localssd/bank/persona/*/data -name "*.json" | wc -l)"
echo "Memory data: $(find /mnt/localssd/bank/memory/*/data -name "*.json" | wc -l)"
echo "Last interactions: $(find /mnt/localssd/bank/persona/*/last_interactions -name "*.json" | wc -l)"
echo "Description embeddings: $(find /mnt/localssd/bank -name "*_description.npz" | wc -l)"
echo "Keywords embeddings: $(find /mnt/localssd/bank -name "*_keywords.npz" | wc -l)"
```

### 查看磁盘使用
```bash
du -sh /mnt/localssd/bank
du -sh /mnt/localssd/bank/persona
du -sh /mnt/localssd/bank/memory
```

### 检查GPU使用
```bash
nvidia-smi
```

### 查看各数据集进度
```bash
# 查看每个数据集已处理学生数
for dataset in assist2017 nips_task34 algebra2005 bridge2006; do
    count=$(find /mnt/localssd/bank/persona/$dataset/data -name "*.json" 2>/dev/null | wc -l)
    echo "$dataset: $count 个学生"
done
```

---

## ⏸️ 停止任务

### 温和停止（等待当前学生处理完成）
```bash
pkill -SIGTERM -f "create_student_bank_final.py"
```

### 强制停止
```bash
pkill -9 -f "create_student_bank_final.py"
```

### 验证已停止
```bash
ps aux | grep create_student_bank_final | grep -v grep
```

---

## 🧹 清理数据（谨慎使用）

### 清理所有生成的数据
```bash
cd /mnt/localssd
rm -rf bank
rm -f bank_creation_full_final.log
```

### 只清理某个数据集
```bash
rm -rf /mnt/localssd/bank/persona/assist2017
rm -rf /mnt/localssd/bank/memory/assist2017
```

---

## 📁 输出文件结构

每个学生会生成7个文件：

```
bank/
├── persona/{dataset}/
│   ├── data/{uid}.json                          # Persona数据
│   ├── embeddings/{uid}_description.npz         # Persona description embedding
│   ├── embeddings/{uid}_keywords.npz            # Persona keywords embedding
│   └── last_interactions/{uid}.json             # 每个concept的最后一次交互
└── memory/{dataset}/
    ├── data/{uid}.json                          # Memory数据
    ├── embeddings/{uid}_description.npz         # Memory description embedding
    └── embeddings/{uid}_keywords.npz            # Memory keywords embedding
```

### 文件示例
```bash
# 查看某个学生的所有文件
find /mnt/localssd/bank -name "0.*" -o -name "0_*"
```

---

## 🔧 故障排查

### 如果进程意外停止
```bash
# 查看日志末尾的错误信息
tail -100 /mnt/localssd/bank_creation_full_final.log

# 从上次停止的地方继续（脚本会自动跳过已处理的学生）
cd /mnt/localssd
bash START_BANK_CREATION.sh
```

### 如果磁盘空间不足
```bash
# 检查磁盘空间
df -h /mnt/localssd

# 查看哪个文件夹占用最多
du -sh /mnt/localssd/bank/*
```

### 如果内存不足
```bash
# 查看内存使用
free -h

# 查看进程内存使用
ps aux | grep create_student_bank_final | awk '{print $6/1024 " MB"}'
```

---

## ✅ 验证数据质量

### 检查某个学生的文件
```bash
# 查看persona数据
cat /mnt/localssd/bank/persona/assist2017/data/0.json | jq '.[0]'

# 查看memory数据
cat /mnt/localssd/bank/memory/assist2017/data/0.json | jq '.[0]'

# 查看last interactions
cat /mnt/localssd/bank/persona/assist2017/last_interactions/0.json | jq '.["0"]'

# 查看embedding文件信息
python -c "import numpy as np; data=np.load('/mnt/localssd/bank/persona/assist2017/embeddings/0_description.npz'); print('Shape:', data['embeddings'].shape)"
```

### 验证数据完整性
```bash
# 检查是否所有学生都有完整的7个文件
cd /mnt/localssd
python -c "
import os
datasets = ['assist2017', 'nips_task34', 'algebra2005', 'bridge2006']
for ds in datasets:
    persona_data = set([f.replace('.json','') for f in os.listdir(f'bank/persona/{ds}/data') if f.endswith('.json')]) if os.path.exists(f'bank/persona/{ds}/data') else set()
    memory_data = set([f.replace('.json','') for f in os.listdir(f'bank/memory/{ds}/data') if f.endswith('.json')]) if os.path.exists(f'bank/memory/{ds}/data') else set()
    print(f'{ds}: Persona={len(persona_data)}, Memory={len(memory_data)}, Match={persona_data == memory_data}')
"
```

---

## 📈 预期完成时间估算

```bash
# 查看当前处理速度和预估剩余时间（在日志中）
grep "it/s" /mnt/localssd/bank_creation_full_final.log | tail -1
```

---

**环境**: pykt (Python 3.7.5)  
**所有依赖已安装**: ✅  
**配置已优化**: ✅  
**准备就绪**: 🚀

