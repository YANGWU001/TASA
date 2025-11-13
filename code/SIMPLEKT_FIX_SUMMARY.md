# 🔧 SimpleKT 修复总结

## 📊 问题描述

用户请求使用SimpleKT模型生成Forgetting Score，但所有4个数据集都失败了。

## 🔍 根本原因分析

经过详细调查，发现SimpleKT失败的根本原因有**3个层次**：

### 1. 缺失依赖包 ❌

**问题：**
- 系统缺少 `einops` 模块
- 系统缺少 `matplotlib` 模块

**错误信息：**
```
ModuleNotFoundError: No module named 'einops'
ModuleNotFoundError: No module named 'matplotlib'
```

**解决：**
```bash
pip install einops matplotlib
```

---

### 2. PyKT版本不匹配 ❌

**问题：**
- 系统安装的pykt（在site-packages）是旧版本，**没有SimpleKT模块**
- 本地的pykt-toolkit有完整的SimpleKT实现

**错误信息：**
```
AttributeError: 'NoneType' object has no attribute 'load_state_dict'
The wrong model name was used...
```

**解决：**
```bash
cd /mnt/localssd/pykt-toolkit
pip uninstall pykt -y
pip install -e .
```

将pykt重新安装为本地开发版本（editable install）

---

### 3. CUDA设备序列化问题 ❌

**问题：**
- 预处理的pickle文件保存了错误的CUDA设备信息
- 使用`CUDA_VISIBLE_DEVICES`限制GPU时，反序列化失败

**错误信息：**
```
RuntimeError: Attempting to deserialize object on CUDA device 7 
but torch.cuda.device_count() is 1
```

**解决：**
```bash
# 删除所有预处理pickle文件
find ../data -name "*_-1.pkl" -o -name "*_-1_*.pkl" | xargs rm -f

# 顺序执行（避免并行CUDA冲突）
bash fix_simplekt_sequential.sh
```

---

### 4. 相对路径问题 ❌

**问题：**
- `calc_fs_all_data_simple.py`使用相对路径保存临时文件
- 当脚本不在`examples/`目录运行时，路径错误

**错误信息：**
```
[Errno 2] No such file or directory: 
'saved_model/.../temp_predictions_assist2017_simplekt.txt'
```

**解决：**
```python
# 修改为使用绝对路径
abs_save_dir = os.path.abspath(save_dir)
save_test_path = os.path.join(abs_save_dir, f"temp_predictions_{dataset}_{model_name}.txt")
```

---

## ✅ 最终解决方案

### 执行的修复步骤

1. **安装缺失依赖**
   ```bash
   pip install einops matplotlib
   ```

2. **重新安装PyKT为本地开发版**
   ```bash
   cd /mnt/localssd/pykt-toolkit
   pip uninstall pykt -y
   pip install -e .
   ```

3. **删除旧的预处理文件**
   ```bash
   find /mnt/localssd/pykt-toolkit/data -name "*_-1*.pkl" -delete
   ```

4. **修复脚本路径问题**
   - 在`calc_fs_all_data_simple.py`中使用绝对路径

5. **使用顺序执行脚本**
   ```bash
   cd /mnt/localssd/pykt-toolkit/examples
   bash fix_simplekt_sequential.sh
   ```

---

## 📝 创建的脚本和文件

1. `/mnt/localssd/test_simplekt_init.py`
   - 测试脚本，验证SimpleKT可以正常初始化

2. `/mnt/localssd/pykt-toolkit/examples/fix_simplekt_all.sh`
   - 并行执行脚本（有CUDA问题，已弃用）

3. `/mnt/localssd/pykt-toolkit/examples/fix_simplekt_sequential.sh`
   - **顺序执行脚本（最终版本）** ✅
   - 避免并行CUDA冲突
   - 使用4个不同的GPU顺序处理

4. `/mnt/localssd/monitor_simplekt.sh`
   - 监控脚本，实时查看进度

---

## 🎯 当前状态

**任务正在运行中...**

- 脚本: `fix_simplekt_sequential.sh`
- 日志: `/mnt/localssd/pykt-toolkit/examples/log_simplekt_all_v2.txt`
- 进度: 0/4完成

**预期生成的文件：**
1. `/mnt/localssd/bank/forgetting/assist2017/simplekt.json`
2. `/mnt/localssd/bank/forgetting/nips_task34/simplekt.json`
3. `/mnt/localssd/bank/forgetting/algebra2005/simplekt.json`
4. `/mnt/localssd/bank/forgetting/bridge2006/simplekt.json`

**监控命令：**
```bash
# 查看实时日志
tail -f /mnt/localssd/pykt-toolkit/examples/log_simplekt_all_v2.txt

# 运行监控脚本
bash /mnt/localssd/monitor_simplekt.sh

# 检查生成的文件
ls -lh /mnt/localssd/bank/forgetting/*/simplekt.json
```

---

## 📊 预期完成后的状态

完成后，所有数据集将有**完整的四模型预测**：

```
/mnt/localssd/bank/forgetting/
├── assist2017/
│   ├── lpkt.json       ✅
│   ├── dkt.json        ✅
│   ├── akt.json        ✅
│   └── simplekt.json   ⏳ (生成中)
│
├── nips_task34/
│   ├── lpkt.json       ✅
│   ├── dkt.json        ✅
│   ├── akt.json        ✅
│   └── simplekt.json   ⏳ (生成中)
│
├── algebra2005/
│   ├── lpkt.json       ✅
│   ├── dkt.json        ✅
│   ├── akt.json        ✅
│   └── simplekt.json   ⏳ (生成中)
│
└── bridge2006/
    ├── lpkt.json       ✅
    ├── dkt.json        ✅
    ├── akt.json        ✅
    └── simplekt.json   ⏳ (生成中)
```

**最终统计：**
- 总文件数: 16个
- 模型完成率: 4/4 (100%) ⭐⭐⭐⭐⭐
- 数据集完成率: 4/4 (100%)
- 总体完成率: **16/16 (100%)** 🎉

---

## 💡 经验教训

1. **依赖管理很重要**
   - 确保所有必需的Python包都已安装
   - 使用`pip install -e .`进行本地开发

2. **CUDA设备管理需谨慎**
   - 预处理文件会保存设备信息
   - 并行执行时要注意设备一致性
   - 必要时删除旧的预处理文件

3. **路径问题容易被忽视**
   - 使用绝对路径更安全
   - 确保脚本在正确的工作目录执行

4. **顺序执行更可靠**
   - 虽然慢，但避免了并行冲突
   - 对于复杂任务，稳定性>速度

---

## 🔧 故障排除指南

如果SimpleKT任务再次失败，按以下步骤检查：

### 1. 检查依赖
```bash
python -c "import einops; import matplotlib; print('✅ 依赖正常')"
```

### 2. 检查PyKT版本
```bash
python -c "from pykt.models.simplekt import simpleKT; print('✅ SimpleKT可用')"
```

### 3. 检查预处理文件
```bash
# 如果有CUDA设备错误，删除预处理文件
find /mnt/localssd/pykt-toolkit/data -name "*_-1*.pkl" -delete
```

### 4. 检查进程状态
```bash
ps aux | grep calc_fs_all_data_simple.py
```

### 5. 查看日志
```bash
tail -100 /mnt/localssd/pykt-toolkit/examples/log_simplekt_all_v2.txt
```

---

**生成时间:** 2025-10-19 16:25  
**状态:** 🟢 正在运行  
**预计完成时间:** 15-30分钟

