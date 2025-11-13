# 🚀 所有KT模型训练总览

## 📊 训练任务配置

### 总共8个训练任务：4个模型 × 2个数据集

| GPU | 模型 | 数据集 | 日志文件 | PID |
|-----|------|--------|---------|-----|
| 0 | LPKT | EdNet | `/tmp/lpkt_ednet_safe.log` | 之前启动 |
| 1 | LPKT | ASSISTments2017 | `/tmp/lpkt_assist2017_safe.log` | 之前启动 |
| 2 | simpleKT | EdNet | `/tmp/kt_training_logs/ednet_simplekt.log` | 52858 |
| 3 | simpleKT | ASSISTments2017 | `/tmp/kt_training_logs/assist2017_simplekt.log` | 53003 |
| 4 | qikt | EdNet | `/tmp/kt_training_logs/ednet_qikt.log` | 53211 |
| 5 | qikt | ASSISTments2017 | `/tmp/kt_training_logs/assist2017_qikt.log` | 53420 |
| 6 | iekt | EdNet | `/tmp/kt_training_logs/ednet_iekt.log` | 53628 |
| 7 | iekt | ASSISTments2017 | `/tmp/kt_training_logs/assist2017_iekt.log` | 53830 |

## 🎯 模型简介

### 1. LPKT (Learning Process-consistent Knowledge Tracing)
- **特点**：考虑学习过程的一致性，使用时间间隔信息
- **输入**：问题ID、答题结果、时间间隔
- **参数**：learning_rate=3e-3

### 2. simpleKT
- **特点**：简化的知识追踪模型，基于Transformer
- **输入**：问题ID、答题结果
- **参数**：
  - learning_rate=1e-3
  - dropout=0.2
  - d_model=128
  - n_blocks=2

### 3. qikt (Question-aware Interaction Knowledge Tracing)
- **特点**：考虑问题特定的交互信息
- **输入**：问题ID、概念ID、答题结果
- **参数**：
  - learning_rate=1e-3
  - dropout=0.1
  - emb_size=128

### 4. iekt (Individual Estimation Knowledge Tracing)
- **特点**：个体化评估的知识追踪
- **输入**：问题ID、答题结果
- **参数**：
  - learning_rate=1e-3
  - dropout=0.2
  - d_model=128
  - n_blocks=2

## 📈 数据集信息

### EdNet-KT1
- **规模**：5000个学生
- **交互数**：~数百万次
- **知识点数**：~200个
- **问题数**：~13000个

### ASSISTments2017
- **规模**：完整数据集
- **交互数**：~数十万次
- **知识点数**：~100+个
- **问题数**：~3000+个

## 🔍 监控命令

### 查看所有训练状态
```bash
bash /mnt/localssd/monitor_all_training.sh
```

### 查看实时日志

**LPKT:**
```bash
# EdNet + LPKT
tail -f /tmp/lpkt_ednet_safe.log

# ASSISTments2017 + LPKT
tail -f /tmp/lpkt_assist2017_safe.log
```

**simpleKT:**
```bash
# EdNet + simpleKT
tail -f /tmp/kt_training_logs/ednet_simplekt.log

# ASSISTments2017 + simpleKT
tail -f /tmp/kt_training_logs/assist2017_simplekt.log
```

**qikt:**
```bash
# EdNet + qikt
tail -f /tmp/kt_training_logs/ednet_qikt.log

# ASSISTments2017 + qikt
tail -f /tmp/kt_training_logs/assist2017_qikt.log
```

**iekt:**
```bash
# EdNet + iekt
tail -f /tmp/kt_training_logs/ednet_iekt.log

# ASSISTments2017 + iekt
tail -f /tmp/kt_training_logs/assist2017_iekt.log
```

### 查看GPU使用情况
```bash
# 实时监控
watch -n 1 nvidia-smi

# 或一次性查看
nvidia-smi
```

### 查看训练进程
```bash
ps aux | grep "python.*wandb" | grep -v grep
```

## 💾 模型保存位置

所有训练好的模型将保存在：
```
/mnt/localssd/pykt-toolkit/examples/saved_model/
├── ednet_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_0_0/
├── assist2017_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_0_0/
├── ednet_simplekt_qid_saved_model_*/
├── assist2017_simplekt_qid_saved_model_*/
├── ednet_qikt_qid_saved_model_*/
├── assist2017_qikt_qid_saved_model_*/
├── ednet_iekt_qid_saved_model_*/
└── assist2017_iekt_qid_saved_model_*/
```

每个模型目录包含：
- `config.json`: 模型配置
- `qid_model.ckpt`: 最佳模型权重
- `qid_model_*.ckpt`: 各epoch的checkpoint

## 🌐 WandB监控

所有训练都启用了WandB（Weights & Biases）监控：

1. **访问**: https://wandb.ai
2. **查找项目**: 根据dataset_name命名
3. **查看指标**:
   - Training Loss
   - Validation AUC
   - Validation Accuracy
   - Learning Rate
   - GPU使用率

## ⚙️ 训练配置

### 通用配置
- **WandB**: 启用 (`--use_wandb=1`)
- **UUID**: 不添加 (`--add_uuid=0`)
- **Fold**: 0 (`--fold=0`)
- **保存目录**: `saved_model`
- **Embedding类型**: `qid` (question ID)

### 后台运行
所有训练都使用 `nohup` 在后台运行，特点：
- ✅ 不受terminal关闭影响
- ✅ 使用 `stdbuf -oL -eL` 实时输出日志
- ✅ 使用 `python -u` 禁用输出缓冲
- ✅ 日志重定向到文件

## 📝 训练进度追踪

### 检查点更新
```bash
# 查看最新的checkpoint文件
ls -lht /mnt/localssd/pykt-toolkit/examples/saved_model/*/
```

### 日志文件大小
```bash
# 查看日志文件增长
ls -lh /tmp/kt_training_logs/
ls -lh /tmp/lpkt_*_safe.log
```

### 进程CPU/内存使用
```bash
# 查看训练进程资源使用
top -u colligo | grep python
```

## 🛠️ 管理命令

### 停止特定训练
```bash
# 停止EdNet + simpleKT
kill <PID>  # 使用上面表格中的PID

# 或按模型名停止
pkill -f "wandb_train.py --dataset_name=ednet --model_name=simplekt"
```

### 停止所有训练
```bash
# 停止所有新训练（不包括LPKT）
pkill -f "wandb_train.py"

# 停止所有训练（包括LPKT）
pkill -f "wandb_lpkt_train.py"
pkill -f "wandb_train.py"
```

### 重启特定训练
如果某个训练失败，可以重新运行相应命令：

**示例：重启EdNet + simpleKT**
```bash
cd /mnt/localssd/pykt-toolkit/examples
source activate pykt
nohup bash -c "CUDA_VISIBLE_DEVICES=2 stdbuf -oL -eL python -u wandb_train.py --dataset_name=ednet --model_name=simplekt --emb_type=qid --save_dir=saved_model --use_wandb=1 --add_uuid=0 --fold=0 --learning_rate=1e-3 --dropout=0.2 --d_model=128 --n_blocks=2 --final_fc_dim=256" > /tmp/kt_training_logs/ednet_simplekt.log 2>&1 &
```

## 📊 预期训练时间

基于数据集大小和模型复杂度的估计：

| 模型 | EdNet (大) | ASSISTments2017 (中) |
|------|-----------|---------------------|
| LPKT | ~8-12小时 | ~4-6小时 |
| simpleKT | ~6-10小时 | ~3-5小时 |
| qikt | ~4-8小时 | ~2-4小时 |
| iekt | ~6-10小时 | ~3-5小时 |

*实际时间取决于GPU性能和训练参数*

## 🎯 训练完成后

### 模型评估
```bash
cd /mnt/localssd/pykt-toolkit/examples
source activate pykt

# 评估特定模型
python evaluate_model.py \
    --model_name=simplekt \
    --dataset_name=ednet \
    --model_dir=saved_model/ednet_simplekt_qid_saved_model_*
```

### 模型预测
使用训练好的模型进行预测：
```bash
python predict_new_data.py --mode demo
```

### 遗忘分数计算
使用任何训练好的模型计算forgetting score：
```bash
python forgetting_score_calculator.py --mode demo
```

## 🔔 注意事项

1. **磁盘空间**: 每个模型约占用几百MB到几GB，确保有足够空间
2. **内存使用**: 每个训练进程可能使用10-20GB内存
3. **GPU显存**: 每个进程使用约8-12GB GPU显存
4. **日志文件**: 会不断增长，定期清理旧日志
5. **WandB登录**: 确保已登录WandB账户

## ✅ 验证训练正在运行

运行以下命令确认：
```bash
# 1. 检查进程
ps aux | grep python | grep wandb

# 2. 检查GPU
nvidia-smi

# 3. 检查日志更新
ls -lht /tmp/kt_training_logs/

# 4. 运行综合监控
bash /mnt/localssd/monitor_all_training.sh
```

## 📞 故障排查

### 训练进程消失
```bash
# 检查日志末尾的错误信息
tail -50 /tmp/kt_training_logs/<model>.log
```

### GPU内存不足
```bash
# 查看GPU显存使用
nvidia-smi

# 如果OOM，考虑减小batch_size或模型大小
```

### 日志不更新
```bash
# 检查进程是否存在
ps aux | grep <PID>

# 检查是否有错误
tail -100 /tmp/kt_training_logs/<model>.log
```

---

**最后更新**: 2025-10-19
**总训练任务**: 8个
**GPU使用**: 8个GPU全部使用
**预计完成**: 8-12小时（取决于模型和数据集）

