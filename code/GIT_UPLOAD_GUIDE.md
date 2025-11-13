# Git上传指南

生成时间: 2025-11-10

---

## ✅ 检查结果

### 📊 文件统计

使用 `.gitignore` 过滤后：

- **总文件数**: 383 个
- **总大小**: 8.40 MB ✅ 适合上传
- **大于1MB的文件**: 4 个

### 📋 文件类型分布

| 文件类型 | 数量 | 大小 |
|---------|------|------|
| `.txt` | 18 个 | 4.73 MB |
| `.py` | 167 个 | 1.22 MB |
| `.csv` | 8 个 | 1.03 MB |
| `.json` | 23 个 | 0.67 MB |
| `.md` | 87 个 | 0.55 MB |
| `.sh` | 76 个 | 0.20 MB |

### ⚠️ 大文件列表（需要注意）

这些文件大于1MB，但仍然可以上传：

1. **bridge_to_algebra_2006_2007_master.txt** (1.68 MB) - 数据集元数据
2. **algebra_2005_2006_master.txt** (1.04 MB) - 数据集元数据
3. **bridge_to_algebra_2006_2007_test.txt** (1.02 MB) - 测试数据
4. **fs_results_assist2017_test.csv** (1.00 MB) - 结果文件

---

## 🚫 已排除的大文件

以下文件已被 `.gitignore` 排除（**不会上传**）：

### 超大文件
- `education.tar.gz` (10G) - 原始数据压缩包
- `pykt-toolkit/data/` (48G) - 所有训练数据集
- `bank/*/embeddings/` (3.9G) - Embedding向量文件
- `bank/memory/*/data/` - Memory原始数据

### 日志和临时文件
- `logs/` (39M) - 所有日志文件
- `*.log` - 单独的日志文件
- `*.pkl` - Pickle文件
- `*.npz` - NumPy压缩数组

### 备份文件
- `llm_judge_results_backup_*/` - 旧版本结果

---

## 📝 上传步骤

### 1. 初始化Git仓库（已完成）

```bash
cd /mnt/localssd
git init
```

### 2. 添加文件

```bash
# 添加所有文件（.gitignore会自动过滤）
git add .

# 检查要提交的文件
git status
```

### 3. 创建第一次提交

```bash
git commit -m "Initial commit: TASA project complete implementation

- Core TASA implementation with Forgetting Score, Memory, and Persona
- Ablation studies (woForgetting, woMemory, woPersona)
- Four baselines: MathChat, PSS-MV, TutorLLM, Vanilla-ICL
- Complete evaluation system with LLM as Judge
- Documentation and analysis reports"
```

### 4. 添加远程仓库

**方法1: 使用HTTPS**
```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
```

**方法2: 使用SSH（推荐）**
```bash
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO.git
```

### 5. 推送到GitHub

```bash
# 推送到main分支
git push -u origin main

# 或者推送到master分支
git push -u origin master
```

---

## 🔧 可选：进一步压缩

如果您还想进一步减小仓库大小，可以考虑排除以下文件：

### 可选排除的文件

添加到 `.gitignore`：

```bash
# 大的数据集文本文件（如果不需要）
*_master.txt
*_test.txt

# 中间结果CSV（如果不需要）
fs_results_*.csv
fs_all_students_*.csv

# 旧的备份结果
llm_judge_results_backup_*/
```

添加后执行：

```bash
git rm --cached bridge_to_algebra_2006_2007_master.txt
git rm --cached algebra_2005_2006_master.txt
git rm --cached bridge_to_algebra_2006_2007_test.txt
git rm --cached fs_results_assist2017_test.csv
git commit -m "Remove large data files"
```

这样可以将大小降到约 **6 MB**。

---

## 📦 重要文件（已包含）

以下重要文件会被上传：

### 文档
- ✅ README.md - 项目主文档
- ✅ TASA_COMPLETE_GUIDE.md - TASA完整指南
- ✅ EXPERIMENT_PLAN.md - 实验计划
- ✅ LLM_JUDGE_COMPLETE_SUMMARY.md - LLM Judge结果
- ✅ TASA_ABLATION_COMPLETE_RESULTS.md - 消融实验结果
- ✅ BASELINE_RESULTS_*.md - Baseline结果

### 代码
- ✅ 所有 `.py` 文件（167个）
- ✅ 所有 `.sh` 脚本（76个）

### 配置和数据
- ✅ qualified_students_*.json - 筛选的学生
- ✅ llm_judge_results/*.json - LLM评判结果
- ✅ bank/配置文件（不含embeddings）

### PyKT Toolkit
- ✅ pykt-toolkit/源代码
- ✅ pykt-toolkit/examples/脚本
- ❌ pykt-toolkit/data/（已排除，太大）

---

## ⚙️ Git配置建议

### 设置用户信息

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 设置默认分支名

```bash
git config --global init.defaultBranch main
```

### 配置大文件提示

```bash
# 警告大于5MB的文件
git config --global core.bigFileThreshold 5m
```

---

## 🚀 GitHub仓库创建

### 1. 在GitHub上创建新仓库

访问：https://github.com/new

设置：
- Repository name: `TASA` 或 `adaptive-tutoring-system`
- Description: "TASA: Time-Aware Student-Adaptive Tutoring System with Forgetting Score"
- Public/Private: 根据需要选择
- ❌ 不要选择 "Initialize with README"（本地已有）

### 2. 推荐的仓库描述

```
TASA: Time-Aware Student-Adaptive Tutoring System

A personalized intelligent tutoring system that adapts to individual student needs using:
- Forgetting Score for identifying knowledge gaps
- Memory bank for storing student interactions
- Persona modeling for personalized teaching styles
- Multiple backbone LLMs (GPT, Llama, Qwen)

Includes complete implementation, baselines, and evaluation with LLM as Judge.
```

### 3. 推荐的Topics (标签)

```
intelligent-tutoring-system
education-ai
personalization
knowledge-tracing
llm
adaptive-learning
forgetting-curve
```

---

## 📊 上传后的文件结构

```
/
├── README.md                          # 项目总览
├── .gitignore                        # Git忽略规则
├── TASA_COMPLETE_GUIDE.md            # TASA指南
├── EXPERIMENT_PLAN.md                # 实验计划
├── LLM_JUDGE_COMPLETE_SUMMARY.md     # LLM Judge结果
├── TASA_ABLATION_COMPLETE_RESULTS.md # 消融实验
│
├── *.py                              # 167个Python文件
├── *.sh                              # 76个Shell脚本
├── *.md                              # 87个Markdown文档
│
├── bank/                             # 学生bank
│   ├── persona/                      # 学生画像
│   ├── memory/                       # 记忆bank
│   └── forgetting_scores/            # 遗忘分数
│
├── llm_judge_results/                # LLM评判结果
│   └── *.json                        # 23个结果文件
│
├── pykt-toolkit/                     # PyKT工具包
│   ├── pykt/                         # 核心代码
│   ├── examples/                     # 示例脚本
│   └── configs/                      # 配置文件
│
└── qualified_students_*.json         # 筛选的学生数据
```

---

## ✅ 检查清单

上传前请确认：

- [ ] `.gitignore` 已创建并生效
- [ ] 没有包含 `education.tar.gz` (10G)
- [ ] 没有包含 `pykt-toolkit/data/` (48G)
- [ ] 没有包含 `bank/*/embeddings/*.npz` (3.9G)
- [ ] 总大小约 8-10 MB ✅
- [ ] 所有重要的 `.py` 和 `.md` 文件都包含
- [ ] Git用户信息已配置
- [ ] 远程仓库已创建

---

## 🆘 常见问题

### Q: 推送时提示文件太大怎么办？

A: GitHub单个文件限制100MB。如果遇到：
```bash
# 找出大文件
find . -type f -size +50M -not -path "./.git/*"

# 添加到.gitignore并移除
echo "large_file.bin" >> .gitignore
git rm --cached large_file.bin
git commit --amend
```

### Q: 如何更新已上传的仓库？

A: 正常的git流程：
```bash
# 修改文件后
git add .
git commit -m "Update: description of changes"
git push
```

### Q: 如何撤销某个文件的提交？

A: 
```bash
# 从Git跟踪中移除但保留本地文件
git rm --cached filename

# 提交更改
git commit -m "Remove filename from tracking"
```

---

## 📞 需要帮助？

- Git官方文档: https://git-scm.com/doc
- GitHub文档: https://docs.github.com
- Git教程: https://www.atlassian.com/git/tutorials

---

生成者: AI Assistant  
最后更新: 2025-11-10

