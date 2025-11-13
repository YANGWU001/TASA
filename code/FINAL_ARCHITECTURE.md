# Student Bank 最终架构说明

## 🏗️ 并行处理架构

### 核心设计
```
主进程
  └─> 创建30个Worker进程
        └─> 每个Worker处理一个学生的完整流程：
              1. 调用LLM生成persona（GPT API）
              2. 调用LLM生成memory（GPT API）  
              3. 使用BGE模型生成embeddings
              4. 保存所有文件
```

### 关键特性

#### 1. 按学生并行
- **30个进程同时运行**
- 每个进程独立处理一个学生
- 进程间互不干扰

#### 2. BGE模型管理
- **每个Worker进程只加载一次BGE**
- 使用全局变量 + lazy initialization
- 第一次使用时加载，后续复用
- 总共最多30个BGE实例（每个进程一个）

#### 3. LLM并发
- GPT API支持高并发
- 30个进程可同时调用
- 无显存限制

#### 4. 资源使用
- **GPU显存**: 30个BGE实例，分布在8个GPU上（自动分配）
- **网络带宽**: 30个并发GPT API调用
- **CPU**: 30个Python进程

---

## ⚙️ 参数配置

```python
MAX_WORKERS = 30  # 可调整为10/20/30/40等
```

### 调整建议
- **显存充足**: 可以调到40-50
- **显存不足**: 降低到10-20
- **网络受限**: 降低到10-15

---

## 🚀 性能估算

### 单个学生处理时间
- LLM生成: ~2-5秒（网络API）
- BGE embedding: ~0.5秒（本地GPU）
- 保存文件: ~0.1秒
- **总计**: ~3-6秒/学生

### 总体时间
- 学生数: ~8,345
- 并行度: 30
- **预计时间**: 8345 ÷ 30 × 5秒 ≈ **23分钟**

---

## 📊 输出结构

每个学生产生5个文件：
```
bank/
├── persona/
│   └── {dataset}/
│       ├── data/{uid}.json              # Persona描述
│       ├── embeddings/{uid}_description.npz
│       ├── embeddings/{uid}_keywords.npz
│       └── last_interactions/{uid}.json
└── memory/
    └── {dataset}/
        ├── data/{uid}.json              # Memory描述
        ├── embeddings/{uid}_description.npz
        └── embeddings/{uid}_keywords.npz
```

---

## ✅ 优势

1. **真正的并行**: 按学生而非按阶段
2. **资源高效**: BGE只加载30次（不是每个学生都加载）
3. **容错性强**: 单个学生失败不影响其他
4. **可伸缩**: 轻松调整并行度

---

**现在的架构是最优的！** 🎯

