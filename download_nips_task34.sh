#!/bin/bash
# NIPS Task 3&4 数据集下载脚本

echo "🔍 正在尝试下载NIPS Task 3&4数据集..."

DATA_DIR="/mnt/localssd/pykt-toolkit/data/nips_task34"
mkdir -p "$DATA_DIR/metadata"

# 尝试方法1: 从Google Drive下载（如果有分享链接）
echo "📥 尝试方法1: Google Drive..."
# Note: 需要替换为实际的Google Drive链接
# gdown --id "YOUR_FILE_ID" -O "$DATA_DIR/train_task_3_4.csv"

# 尝试方法2: 从Kaggle下载（如果数据在Kaggle上）
echo "📥 尝试方法2: Kaggle..."
# kaggle competitions download -c neurips-2020-education-challenge

# 尝试方法3: 手动下载指引
echo ""
echo "⚠️  自动下载不可用，请手动下载数据集："
echo ""
echo "📋 手动下载步骤："
echo "1. 访问: https://competitions.codalab.org/competitions/25449"
echo "2. 注册账号（如果还没有）"
echo "3. 进入 'Participate' -> 'Get Data' 下载以下文件："
echo "   - train_task_3_4.csv"
echo "   - answer_metadata_task_3_4.csv"
echo "   - question_metadata_task_3_4.csv"
echo "   - student_metadata_task_3_4.csv"
echo "   - subject_metadata.csv"
echo ""
echo "4. 将下载的文件放置到以下位置："
echo "   主数据: $DATA_DIR/train_task_3_4.csv"
echo "   元数据: $DATA_DIR/metadata/*.csv"
echo ""
echo "5. 运行预处理: cd /mnt/localssd/pykt-toolkit/examples && python data_preprocess.py --dataset_name nips_task34"
echo ""

# 检查文件是否已存在
if [ -f "$DATA_DIR/train_task_3_4.csv" ]; then
    echo "✅ 找到主数据文件!"
    
    # 检查metadata
    if [ -f "$DATA_DIR/metadata/subject_metadata.csv" ]; then
        echo "✅ 找到元数据文件!"
        echo ""
        echo "🎉 数据集已准备就绪，可以开始预处理和训练！"
        exit 0
    else
        echo "⚠️  缺少元数据文件"
    fi
else
    echo "⚠️  未找到数据文件，请按照上述步骤手动下载"
fi

exit 1

