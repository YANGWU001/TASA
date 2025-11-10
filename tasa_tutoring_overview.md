# TASA Tutoring 系统实现概览

## 已完成模块

### 1. tasa_config.py ✅
- API配置（模型、endpoint、key）
- RAG配置（lambda权重、top-K参数）
- 对话配置（轮数、温度参数）
- Forgetting curve配置

### 2. tasa_rag.py ✅  
- 加载学生persona和memory
- 计算相似度（lambda加权）
- 初步检索top-10
- Reranker精排top-3

### 3. tasa_rewrite.py ✅
- 加载forgetting信息
- 使用LLM重写描述
- 生成forgetting-adjusted的persona/memory

## 待实现模块

### 4. tasa_tutoring.py (核心)
- 对话管理
- 生成初始问题
- 每轮：讲解+生成问题
- 整合RAG和重写结果
- 保存对话历史

### 5. tasa_evaluation.py
- Post-test评估
- 计算learning gain
- 对比pre-test和post-test

### 6. tasa_main.py
- 单个学生完整流程
- 批量学生评估
- 生成最终统计

## 系统流程

```
Student: "I want to learn [concept]"
    ↓
[RAG检索 + Rerank]
    ↓
[Mastery重写]
    ↓
[生成第1个问题] ← Round 1
    ↓
Student: [回答]
    ↓
[RAG检索当前query]
    ↓
[讲解上一轮 + 生成问题] ← Round 2-10
    ↓
... 重复10轮 ...
    ↓
[保存dialogue]
    ↓
[Post-test评估]
    ↓
[计算learning gain]
```

## 目录结构

```
bank/
├── dialogue/TASA/              # 对话记录
│   └── {student_id}-{concept}.json
├── evaluation_results/TASA/    # 评估结果
│   └── {dataset}/
│       ├── overall.json
│       └── student_*.json
├── persona/{dataset}/          # Persona数据
├── memory/{dataset}/           # Memory数据
└── session/{dataset}/          # Session数据
```
