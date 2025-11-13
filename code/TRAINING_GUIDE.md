# 🎯 LPKT训练实时监控指南

## ✅ 训练已重启成功！

两个LPKT模型现在正在训练中，**已启用实时日志输出和WandB**！

### 📊 当前训练状态

| 数据集 | GPU | 进程PID | 状态 | 配置 |
|--------|-----|---------|------|------|
| **EdNet** | GPU 0 | 31617 | ✅ Epoch 1完成 | WandB启用 |
| **ASSISTments2017** | GPU 1 | 31927 | ✅ 初始化中 | WandB启用 |

---

## 📺 查看实时训练进度（4种方法）

### 方法1: 实时查看EdNet训练（推荐）
```bash
tail -f /tmp/lpkt_ednet_live.log
```

### 方法2: 实时查看ASSISTments2017训练
```bash
tail -f /tmp/lpkt_assist2017_live.log
```

### 方法3: 同时查看两个训练
```bash
tail -f /tmp/lpkt_ednet_live.log /tmp/lpkt_assist2017_live.log
```

### 方法4: 交互式菜单（推荐新手）
```bash
bash /mnt/localssd/watch_training_live.sh
```

---

## 📈 训练进度说明

训练过程中您会看到：

### 每个Epoch结束时显示：
```
Epoch: 1, validauc: 0.7147, validacc: 0.6982, best epoch: 1, best auc: 0.7147, train loss: 3388.81...
            testauc: -1, testacc: -1, window_testauc: -1, window_testacc: -1
```

**指标说明：**
- `Epoch`: 当前训练轮次（总共200轮）
- `validauc`: 验证集AUC（越高越好）
- `validacc`: 验证集准确率
- `best epoch`: 最佳模型的epoch
- `train loss`: 训练损失（越低越好）

### 进度条：
虽然后台运行看不到tqdm进度条，但您可以：
1. **看到每个epoch的结果**（最直观）
2. **观察日志行数增长**
3. **通过GPU使用率判断**（高使用率=训练中）

---

## 🌐 WandB可视化

由于启用了`--use_wandb=1`，训练数据会上传到WandB。

### 查找WandB链接：
```bash
# 在日志中搜索wandb链接
grep -i "wandb" /tmp/lpkt_ednet_live.log /tmp/lpkt_assist2017_live.log
```

**注意**: 如果是第一次使用WandB，可能需要登录：
1. 日志中会显示登录链接
2. 访问 https://wandb.ai 查看训练可视化

---

## 🔍 快速检查训练状态

```bash
# 运行此脚本查看摘要
bash /mnt/localssd/show_progress.sh
```

或手动检查：
```bash
# 查看最新进度
tail -20 /tmp/lpkt_ednet_live.log
tail -20 /tmp/lpkt_assist2017_live.log

# 查看GPU使用
nvidia-smi

# 查看进程
ps aux | grep wandb_lpkt_train
```

---

## 💾 模型保存位置

训练会自动保存最佳模型：

**EdNet模型：**
```
/mnt/localssd/pykt-toolkit/examples/saved_model/ednet_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_1_0/
```

**ASSISTments2017模型：**
```
/mnt/localssd/pykt-toolkit/examples/saved_model/assist2017_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_1_0/
```

每个模型目录包含：
- `qid_model.ckpt` - 最佳模型checkpoint
- `config.json` - 模型配置

---

## 📝 日志文件位置

| 训练 | 日志文件 |
|------|----------|
| EdNet | `/tmp/lpkt_ednet_live.log` |
| ASSISTments2017 | `/tmp/lpkt_assist2017_live.log` |

---

## 🛑 如何停止训练

如果需要停止训练：
```bash
# 停止EdNet训练
pkill -f "wandb_lpkt_train.py --dataset_name=ednet"

# 停止ASSISTments2017训练
pkill -f "wandb_lpkt_train.py --dataset_name=assist2017"

# 停止所有训练
pkill -f "wandb_lpkt_train"
```

---

## ⏱️ 预计训练时间

- **总Epochs**: 200
- **每Epoch时间**: 约2-5分钟（取决于数据集大小）
- **预计总时间**: 7-17小时

**提示**: 训练会自动进行，无需人工干预。最佳模型会自动保存！

---

## 🎓 训练完成后

训练完成后，可以评估模型：

```bash
cd /mnt/localssd/pykt-toolkit/examples

# 评估EdNet模型
python wandb_predict.py \
    --dataset_name=ednet \
    --model_name=lpkt \
    --save_dir=saved_model \
    --use_wandb=0

# 评估ASSISTments2017模型  
python wandb_predict.py \
    --dataset_name=assist2017 \
    --model_name=lpkt \
    --save_dir=saved_model \
    --use_wandb=0
```

---

## 💡 常用命令速查

```bash
# 查看训练摘要
bash /mnt/localssd/show_progress.sh

# 实时查看EdNet
tail -f /tmp/lpkt_ednet_live.log

# 实时查看ASSISTments2017
tail -f /tmp/lpkt_assist2017_live.log

# 检查GPU
nvidia-smi

# 查看进程
ps aux | grep wandb_lpkt_train
```

---

## 🎉 现在开始监控吧！

推荐运行：
```bash
tail -f /tmp/lpkt_ednet_live.log
```

按 `Ctrl+C` 退出实时查看（训练会继续在后台运行）

---
创建时间: $(date)

