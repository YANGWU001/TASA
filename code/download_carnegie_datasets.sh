#!/bin/bash

# Carnegie Learning数据集下载脚本
# Algebra2005 和 Bridge2Algebra2006

echo "=========================================="
echo "Carnegie Learning数据集下载"
echo "=========================================="
echo ""

# 创建目录
mkdir -p /mnt/localssd/pykt-toolkit/data/algebra2005
mkdir -p /mnt/localssd/pykt-toolkit/data/bridge2algebra2006

echo "📁 已创建数据目录"
echo ""

# Algebra2005
echo "正在下载 Algebra 2005-2006..."
cd /mnt/localssd/pykt-toolkit/data/algebra2005

# 尝试从公开镜像下载
wget -O algebra_2005_2006_train.txt "https://pslcdatashop.web.cmu.edu/GetFile?datasetId=76&fileType=student_step" 2>&1 | tee algebra2005_download.log

if [ ! -f "algebra_2005_2006_train.txt" ] || [ ! -s "algebra_2005_2006_train.txt" ]; then
    echo "❌ Algebra2005自动下载失败"
    echo ""
    echo "📋 请手动下载："
    echo "1. 访问: https://pslcdatashop.web.cmu.edu/DatasetInfo?datasetId=76"
    echo "2. 点击 'Export' -> 'Student-Step Export'"
    echo "3. 下载为 'algebra_2005_2006_train.txt'"
    echo "4. 放置到: /mnt/localssd/pykt-toolkit/data/algebra2005/"
    echo ""
else
    echo "✅ Algebra2005下载成功"
fi

# Bridge2Algebra2006
echo ""
echo "正在下载 Bridge to Algebra 2006-2007..."
cd /mnt/localssd/pykt-toolkit/data/bridge2algebra2006

wget -O bridge_to_algebra_2006_2007_train.txt "https://pslcdatashop.web.cmu.edu/GetFile?datasetId=240&fileType=student_step" 2>&1 | tee bridge2006_download.log

if [ ! -f "bridge_to_algebra_2006_2007_train.txt" ] || [ ! -s "bridge_to_algebra_2006_2007_train.txt" ]; then
    echo "❌ Bridge2Algebra2006自动下载失败"
    echo ""
    echo "📋 请手动下载："
    echo "1. 访问: https://pslcdatashop.web.cmu.edu/DatasetInfo?datasetId=240"
    echo "2. 点击 'Export' -> 'Student-Step Export'"
    echo "3. 下载为 'bridge_to_algebra_2006_2007_train.txt'"
    echo "4. 放置到: /mnt/localssd/pykt-toolkit/data/bridge2algebra2006/"
    echo ""
else
    echo "✅ Bridge2Algebra2006下载成功"
fi

echo ""
echo "=========================================="
echo "下载完成检查"
echo "=========================================="
echo ""

if [ -f "/mnt/localssd/pykt-toolkit/data/algebra2005/algebra_2005_2006_train.txt" ] && [ -s "/mnt/localssd/pykt-toolkit/data/algebra2005/algebra_2005_2006_train.txt" ]; then
    echo "✅ Algebra2005: $(ls -lh /mnt/localssd/pykt-toolkit/data/algebra2005/algebra_2005_2006_train.txt | awk '{print $5}')"
else
    echo "❌ Algebra2005: 未找到或为空"
fi

if [ -f "/mnt/localssd/pykt-toolkit/data/bridge2algebra2006/bridge_to_algebra_2006_2007_train.txt" ] && [ -s "/mnt/localssd/pykt-toolkit/data/bridge2algebra2006/bridge_to_algebra_2006_2007_train.txt" ]; then
    echo "✅ Bridge2Algebra2006: $(ls -lh /mnt/localssd/pykt-toolkit/data/bridge2algebra2006/bridge_to_algebra_2006_2007_train.txt | awk '{print $5}')"
else
    echo "❌ Bridge2Algebra2006: 未找到或为空"
fi

echo ""
echo "=========================================="
echo "备用下载方案"
echo "=========================================="
echo ""
echo "如果自动下载失败，可以尝试："
echo ""
echo "方案1: 使用已有镜像"
echo "  wget https://github.com/pykt-team/pykt-toolkit/releases/download/v0.0.1/algebra2005.zip"
echo "  wget https://github.com/pykt-team/pykt-toolkit/releases/download/v0.0.1/bridge2algebra2006.zip"
echo ""
echo "方案2: 从DataShop申请"
echo "  1. 注册账号: https://pslcdatashop.web.cmu.edu/"
echo "  2. 申请访问权限"
echo "  3. 下载数据集"
echo ""
echo "方案3: 提供Google Drive或其他链接"
echo "  如果您有这些数据集的链接，可以使用gdown下载"
echo ""

