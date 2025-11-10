# Git LFS 上传指南

生成时间: 2025-11-10

---

## 📊 当前目录扫描结果

### 总体情况
- **总大小**: 4.0 GB
- **大于100MB的文件**: 0 个 ✅
- **50-100MB的文件**: 2 个
- **10-50MB的文件**: 25 个

### Bank目录详情
| 子目录 | 大小 | 文件数 | 说明 |
|--------|------|--------|------|
| **dialogue** | 69 MB | 2,527 | 对话记录 |
| **evaluation_results** | 66 MB | 8,223 | 评估结果 |
| **forgetting** | 689 MB | 33 | 遗忘分数 |
| **persona** | 1.5 GB | 39,526 | 学生画像（含embeddings） |
| **memory** | 1.6 GB | 8,425 | 记忆数据（含embeddings） |

### Embeddings统计
- **总数**: 16,756 个 .npz 文件
- **总大小**: ~3.9 GB
- **平均大小**: ~0.24 MB
- **最大单文件**: <10 MB

### ✅ 好消息：所有单个文件都 < 100MB！

这意味着您可以直接上传，但使用Git LFS会更好地管理这些二进制文件。

---

## 🚀 方案选择

### 方案1：不使用Git LFS（简单但不推荐）

**优点**:
- 配置简单，直接git push即可

**缺点**:
- ❌ 4GB仓库太大，clone很慢
- ❌ 每次pull都要下载所有embeddings
- ❌ GitHub仓库总大小限制（推荐<5GB）

### 方案2：使用Git LFS（推荐）✅

**优点**:
- ✅ Embeddings按需下载
- ✅ 仓库克隆速度快
- ✅ 更好的版本管理
- ✅ GitHub官方支持（免费2GB存储+带宽）

**缺点**:
- 需要额外配置
- 超出免费额度后需要付费（$5/月 50GB）

### 方案3：混合方案（最佳折衷）🌟

**保留重要数据，使用Git LFS管理大文件**:
- 核心JSON数据：正常git
- Embeddings (.npz)：Git LFS
- 总仓库大小：~1GB（不含LFS）
- LFS存储：~3.9GB

---

## 📝 Git LFS 完整配置步骤

### Step 1: 安装 Git LFS

```bash
# Ubuntu/Debian
sudo apt-get install git-lfs

# 或者下载安装
curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash
sudo apt-get install git-lfs

# 初始化Git LFS
git lfs install
```

### Step 2: 配置 .gitattributes

创建`.gitattributes`文件来指定哪些文件使用LFS：

```bash
cd /mnt/localssd

# 创建.gitattributes
cat > .gitattributes << 'EOF'
# Git LFS 配置
# 所有 .npz embedding 文件使用 LFS
*.npz filter=lfs diff=lfs merge=lfs -text

# 可选：其他大文件类型
*.pkl filter=lfs diff=lfs merge=lfs -text
*.h5 filter=lfs diff=lfs merge=lfs -text
*.model filter=lfs diff=lfs merge=lfs -text
EOF
```

### Step 3: 配置 .gitignore

```bash
cat > .gitignore << 'EOF'
# ============================================
# Git ignore - 配合Git LFS使用
# ============================================

# 大型压缩包（不需要上传）
*.tar.gz
*.zip
education.tar.gz

# PyKT数据集（太大，不需要）
pykt-toolkit/data/
pykt-toolkit/examples/saved_model/
pykt-toolkit/examples/all_bestmodel/
pykt-toolkit/examples/pkls/
pykt-toolkit/examples/wandb/
pykt-toolkit/examples/pred_wandbs/
pykt-toolkit/build/
pykt-toolkit/dist/
pykt-toolkit/*.egg-info/

# Python缓存
__pycache__/
*.py[cod]
*.so
.Python
*.egg-info/
.ipynb_checkpoints/

# 日志文件
*.log
logs/
nohup.out

# 临时文件
*.swp
*.bak
*.tmp
tmp*/
*~
.DS_Store

# IDE
.vscode/
.idea/

# Wandb
wandb/
*wandb*/
configs/wandb.json

# 备份
llm_judge_results_backup_*/
*_backup/

# 其他
dev_tools/
archive/
prediction.csv
EOF
```

### Step 4: 初始化仓库并添加文件

```bash
cd /mnt/localssd

# 如果还没有初始化git（已初始化的可以跳过）
git init

# 添加.gitattributes（必须先添加）
git add .gitattributes
git commit -m "Add Git LFS configuration"

# 添加所有文件
git add .

# 查看哪些文件会被LFS跟踪
git lfs ls-files

# 创建提交
git commit -m "Initial commit: TASA project with Git LFS

- Core TASA implementation
- Bank data (persona, memory, forgetting, dialogue, evaluation)
- Embeddings managed with Git LFS
- Complete documentation"
```

### Step 5: 连接到GitHub并推送

```bash
# 添加远程仓库
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# 或使用SSH
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO.git

# 推送（LFS文件会自动上传到LFS服务器）
git push -u origin main
```

---

## 💰 GitHub LFS 配额说明

### 免费账户
- **存储**: 2 GB
- **带宽**: 1 GB/月
- 您的embeddings约3.9GB，**超出免费额度**

### 解决方案

#### 选项1：升级到GitHub Pro ($4/月)
- 存储: 2 GB
- 带宽: 50 GB/月
- 可购买额外数据包：$5/月 50GB

#### 选项2：减少LFS文件
只将最大的embeddings放入LFS：

```bash
# .gitattributes 只跟踪大于1MB的npz文件
# 需要手动筛选，或者：
*.npz filter=lfs diff=lfs merge=lfs -text

# 然后在.gitignore中排除部分embeddings
# bank/persona/*/embeddings/ 
```

#### 选项3：使用其他LFS服务
- GitLab: 免费10GB存储
- Bitbucket: 免费1GB存储
- 自建LFS服务器

---

## 🔍 检查和验证

### 查看LFS文件

```bash
# 查看被LFS跟踪的文件
git lfs ls-files

# 查看LFS状态
git lfs status

# 查看LFS使用的存储空间
git lfs env
```

### 测试克隆

```bash
# 克隆仓库（会自动下载LFS文件）
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git

# 或者只克隆元数据，不下载LFS文件
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git

# 之后按需下载特定文件
cd YOUR_REPO
git lfs pull --include="bank/persona/assist2017/embeddings/*"
```

---

## 📊 不同方案的对比

| 方案 | 仓库大小 | LFS存储 | 克隆时间 | GitHub免费 | 推荐度 |
|------|---------|---------|----------|-----------|--------|
| **完全不用LFS** | 4.0 GB | 0 | 慢 | ⚠️ 接近限制 | ⭐ |
| **LFS所有.npz** | ~1.0 GB | 3.9 GB | 快 | ❌ 超出免费 | ⭐⭐ |
| **排除embeddings** | ~800 MB | 0 | 最快 | ✅ | ⭐⭐⭐ |
| **LFS+精简** | ~1.0 GB | <2 GB | 快 | ✅ | ⭐⭐⭐⭐ |

---

## 💡 我的建议

### 推荐方案：精简LFS策略

1. **不上传的内容**:
   - `pykt-toolkit/data/` - 原始数据集（48GB）
   - `logs/` - 日志文件
   - `*.log`, `*.pkl` - 临时文件

2. **正常Git管理**（约1GB）:
   - 所有代码 (.py, .sh)
   - 所有文档 (.md)
   - Bank JSON数据
   - 小的配置文件

3. **Git LFS管理**（约2GB，选择性）:
   - 只保留重要的embeddings
   - 或者标记但不实际上传（.gitattributes配置）

### 具体操作

```bash
# 1. 先创建一个小的.gitignore，排除部分embeddings
cat > .gitignore << 'EOF'
# ... 基本配置 ...

# 可选：排除部分embeddings以减小LFS用量
# bank/persona/*/embeddings/
# 或保留重要的，排除测试的
bank/test_data/
bank/session/
EOF

# 2. 配置LFS只跟踪必要文件
cat > .gitattributes << 'EOF'
# 只跟踪bank目录下的npz
bank/**/*.npz filter=lfs diff=lfs merge=lfs -text
EOF

# 3. 提交并推送
git add .gitattributes .gitignore
git commit -m "Configure Git LFS"
git add .
git commit -m "Initial commit"
git push
```

---

## 🆘 常见问题

### Q: LFS推送失败怎么办？

```bash
# 检查LFS状态
git lfs status

# 重新推送LFS对象
git lfs push origin main --all
```

### Q: 如何移除已经在LFS中的文件？

```bash
# 从LFS移除但保留在git
git lfs untrack "*.npz"
git rm --cached -r bank/persona/*/embeddings/
git add .
git commit -m "Remove embeddings from LFS"
```

### Q: 如何迁移已有仓库到LFS？

```bash
# 安装Git LFS
git lfs install

# 配置要跟踪的文件
git lfs track "*.npz"

# 迁移历史（可选）
git lfs migrate import --include="*.npz"
```

---

## 📞 资源链接

- Git LFS官网: https://git-lfs.github.com/
- GitHub LFS文档: https://docs.github.com/en/repositories/working-with-files/managing-large-files
- Git LFS教程: https://www.atlassian.com/git/tutorials/git-lfs

---

生成者: AI Assistant  
最后更新: 2025-11-10

