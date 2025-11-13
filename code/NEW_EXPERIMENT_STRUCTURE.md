# 新的实验结构说明

## 🔄 核心改进

### 1. Loop顺序改变
```
旧方案：
  for method in ['simple_time', 'history', ...]:    # 外层
      for dataset in ['assist2017', ...]:           # 内层
          运行实验
          
新方案：
  for dataset in ['algebra2005', 'assist2017', ...]: # 外层（优先最小数据集）
      for method in ['simple_time', 'history', ...]: # 内层
          运行实验
```

**优势**：
- 快速确定每个dataset的最佳method
- algebra2005只需~2.5小时就能得出6个method的对比结果
- 不需要等全部24个实验完成就能看到初步结论

### 2. 独立子文件夹保存

**旧方案问题**：
- 同一个dataset，不同method会相互覆盖
- 只保留最后一个method的详细结果

**新方案**：
```
Dialogue保存：
  /bank/dialogue/TASA-llama/
    ├─ algebra2005/
    │   ├─ simple_time/
    │   │   └─ {student_id}-{concept}.json
    │   ├─ history/
    │   │   └─ {student_id}-{concept}.json
    │   └─ ... (6个method子目录)
    ├─ assist2017/
    │   ├─ simple_time/
    │   └─ ... (6个method子目录)
    └─ ...

Results保存：
  /bank/evaluation_results/TASA-llama-best-of-2/
    ├─ algebra2005/
    │   ├─ simple_time/
    │   │   ├─ overall.json
    │   │   └─ student_*.json
    │   ├─ history/
    │   │   ├─ overall.json
    │   │   └─ student_*.json
    │   └─ ... (6个method子目录)
    ├─ assist2017/
    │   └─ ... (6个method子目录)
    └─ ...
```

**优势**：
- 所有中间结果都保留
- 每个method都有完整的overall.json
- 方便后续分析和对比

## 📊 实验执行顺序

```
Step  Dataset      Method       学生数  预计时间
──────────────────────────────────────────────────
 1    algebra2005  simple_time   29     ~25分钟
 2    algebra2005  history       29     ~25分钟
 3    algebra2005  lpkt          29     ~25分钟
 4    algebra2005  dkt           29     ~25分钟
 5    algebra2005  akt           29     ~25分钟
 6    algebra2005  simplekt      29     ~25分钟
      → algebra2005完成，得出最佳method！

 7    assist2017   simple_time   40     ~35分钟
 8    assist2017   history       40     ~35分钟
 ... (6个method)
      → assist2017完成，得出最佳method！

13    bridge2006   simple_time   40     ~35分钟
... (6个method)
      → bridge2006完成，得出最佳method！

19    nips_task34  simple_time   40     ~35分钟
... (6个method)
      → nips_task34完成，得出最佳method！
```

总计：24个实验，~13小时

## 📈 结果分析

最终生成文件：
```json
forgetting_method_comparison_llama-3.1-8B-Instruct.json
{
  "all_results": {
    "algebra2005": {
      "simple_time": 0.38,
      "history": 0.42,
      "lpkt": 0.45,
      ...
    },
    "assist2017": { ... },
    ...
  },
  "dataset_best_methods": {
    "algebra2005": {"method": "lpkt", "gain": 0.45},
    "assist2017": {"method": "history", "gain": 0.43},
    ...
  },
  "overall_best_method": "lpkt"
}
```

## 🎯 优势总结

1. **快速验证**：第一个数据集2.5小时就能看到所有method对比
2. **完整保存**：所有dialogue和results都保留，不覆盖
3. **灵活分析**：每个dataset独立分析，也可以跨dataset对比
4. **易于扩展**：新增method只需加到内层循环
