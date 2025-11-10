#!/bin/bash
# Git LFS 快速配置脚本

set -e  # 遇到错误立即退出

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                    Git LFS 配置向导                                        ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Git LFS是否已安装
echo "📋 检查 Git LFS 安装状态..."
if command -v git-lfs &> /dev/null; then
    echo -e "${GREEN}✅ Git LFS 已安装${NC}"
    git lfs version
else
    echo -e "${RED}❌ Git LFS 未安装${NC}"
    echo ""
    echo "请先安装 Git LFS:"
    echo "  Ubuntu/Debian: sudo apt-get install git-lfs"
    echo "  或访问: https://git-lfs.github.com/"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 当前目录分析"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 统计.npz文件
NPZ_COUNT=$(find bank -name "*.npz" -type f 2>/dev/null | wc -l)
NPZ_SIZE=$(du -sh bank/*/embeddings 2>/dev/null | awk '{sum+=$1} END {print sum}' || echo "0")
TOTAL_SIZE=$(du -sh . --exclude=.git 2>/dev/null | awk '{print $1}')

echo "  总大小: $TOTAL_SIZE"
echo "  Embedding文件(.npz): $NPZ_COUNT 个"
echo "  Bank目录: $(du -sh bank 2>/dev/null | awk '{print $1}')"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "请选择上传策略:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  1) 🚀 使用Git LFS上传所有embeddings（推荐，但需要LFS额度）"
echo "     - 所有.npz文件使用LFS"
echo "     - 需要约4GB LFS存储空间"
echo "     - 克隆速度快，按需下载"
echo ""
echo "  2) 📦 只上传JSON数据，不上传embeddings（最安全）"
echo "     - 排除所有.npz文件"
echo "     - 仓库大小约800MB"
echo "     - 不需要LFS"
echo ""
echo "  3) ⚡ 混合方案：重要的用LFS，其他排除"
echo "     - 只保留dialogue和evaluation的embeddings"
echo "     - 需要约100MB LFS存储"
echo "     - 平衡方案"
echo ""
echo "  4) 📝 自定义配置"
echo ""
echo "  0) 退出"
echo ""
read -p "请选择 (0-4): " choice

case $choice in
    1)
        echo ""
        echo -e "${GREEN}选择了方案1: 完整LFS上传${NC}"
        echo ""
        
        # 初始化Git LFS
        git lfs install
        
        # 创建.gitattributes
        cat > .gitattributes << 'EOF'
# Git LFS 配置 - 完整方案
*.npz filter=lfs diff=lfs merge=lfs -text
*.pkl filter=lfs diff=lfs merge=lfs -text
EOF
        
        # 创建.gitignore
        cat > .gitignore << 'EOF'
# PyKT数据集（太大）
pykt-toolkit/data/
pykt-toolkit/examples/saved_model/
pykt-toolkit/examples/all_bestmodel/
pykt-toolkit/examples/pkls/
pykt-toolkit/examples/wandb/
pykt-toolkit/examples/pred_wandbs/
pykt-toolkit/build/
pykt-toolkit/dist/
pykt-toolkit/*.egg-info/

# 大型压缩包
*.tar.gz
*.zip
education.tar.gz

# Python缓存
__pycache__/
*.py[cod]
.ipynb_checkpoints/

# 日志
*.log
logs/
nohup.out

# 临时文件
*.swp
*.bak
*.tmp
tmp*/
.DS_Store

# IDE
.vscode/
.idea/

# Wandb
wandb/
*wandb*/

# 备份
llm_judge_results_backup_*/
EOF

        echo -e "${GREEN}✅ 已创建 .gitattributes 和 .gitignore${NC}"
        echo ""
        echo "⚠️  注意: 此方案需要约4GB Git LFS存储空间"
        echo "   GitHub免费账户只有2GB，需要升级或购买数据包"
        ;;
        
    2)
        echo ""
        echo -e "${GREEN}选择了方案2: 只上传JSON（不用LFS）${NC}"
        echo ""
        
        # 不需要LFS配置
        # 只创建.gitignore
        cat > .gitignore << 'EOF'
# PyKT数据集
pykt-toolkit/data/
pykt-toolkit/examples/saved_model/
pykt-toolkit/examples/all_bestmodel/
pykt-toolkit/examples/pkls/
pykt-toolkit/examples/wandb/
pykt-toolkit/examples/pred_wandbs/
pykt-toolkit/build/
pykt-toolkit/dist/
pykt-toolkit/*.egg-info/

# 排除所有embeddings
bank/*/embeddings/
*.npz

# 大型压缩包
*.tar.gz
*.zip
education.tar.gz

# Python缓存
__pycache__/
*.py[cod]
.ipynb_checkpoints/

# 日志
*.log
logs/
nohup.out

# 临时文件
*.swp
*.bak
*.tmp
tmp*/
.DS_Store

# IDE
.vscode/
.idea/

# Wandb
wandb/
*wandb*/

# 备份
llm_judge_results_backup_*/
EOF

        echo -e "${GREEN}✅ 已创建 .gitignore${NC}"
        echo ""
        echo "✅ 此方案不需要Git LFS，可以直接使用普通git push"
        ;;
        
    3)
        echo ""
        echo -e "${GREEN}选择了方案3: 混合方案${NC}"
        echo ""
        
        # 初始化Git LFS
        git lfs install
        
        # 创建.gitattributes - 只跟踪特定目录
        cat > .gitattributes << 'EOF'
# Git LFS 配置 - 混合方案
# 只对重要的embeddings使用LFS
bank/dialogue/**/embeddings/*.npz filter=lfs diff=lfs merge=lfs -text
bank/evaluation_results/**/embeddings/*.npz filter=lfs diff=lfs merge=lfs -text
EOF
        
        # 创建.gitignore - 排除其他embeddings
        cat > .gitignore << 'EOF'
# PyKT数据集
pykt-toolkit/data/
pykt-toolkit/examples/saved_model/
pykt-toolkit/examples/all_bestmodel/
pykt-toolkit/examples/pkls/
pykt-toolkit/examples/wandb/
pykt-toolkit/examples/pred_wandbs/
pykt-toolkit/build/
pykt-toolkit/dist/
pykt-toolkit/*.egg-info/

# 排除大部分embeddings，只保留dialogue和evaluation
bank/persona/*/embeddings/
bank/memory/*/embeddings/

# 大型压缩包
*.tar.gz
*.zip
education.tar.gz

# Python缓存
__pycache__/
*.py[cod]
.ipynb_checkpoints/

# 日志
*.log
logs/
nohup.out

# 临时文件
*.swp
*.bak
*.tmp
tmp*/
.DS_Store

# IDE
.vscode/
.idea/

# Wandb
wandb/
*wandb*/

# 备份
llm_judge_results_backup_*/
EOF

        echo -e "${GREEN}✅ 已创建 .gitattributes 和 .gitignore${NC}"
        echo ""
        echo "✅ 此方案只需要约100MB Git LFS存储，在免费额度内"
        ;;
        
    4)
        echo ""
        echo "请手动编辑 .gitattributes 和 .gitignore 文件"
        echo "参考文档: GIT_LFS_SETUP_GUIDE.md"
        exit 0
        ;;
        
    0)
        echo "退出"
        exit 0
        ;;
        
    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 下一步操作"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. 查看将要添加的文件:"
echo "   ${YELLOW}git status${NC}"
echo ""
echo "2. 添加所有文件:"
echo "   ${YELLOW}git add .${NC}"
echo ""
echo "3. 创建提交:"
echo "   ${YELLOW}git commit -m \"Initial commit: TASA project\"${NC}"
echo ""
echo "4. 添加远程仓库:"
echo "   ${YELLOW}git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git${NC}"
echo ""
echo "5. 推送到GitHub:"
echo "   ${YELLOW}git push -u origin main${NC}"
echo ""

if [ "$choice" == "1" ] || [ "$choice" == "3" ]; then
    echo -e "${YELLOW}⚠️  提示: 推送LFS文件可能需要较长时间${NC}"
    echo ""
    echo "可以使用以下命令查看LFS状态:"
    echo "   ${YELLOW}git lfs ls-files${NC}"
    echo "   ${YELLOW}git lfs status${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ 配置完成！${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "详细文档请查看: GIT_LFS_SETUP_GUIDE.md"
echo ""

