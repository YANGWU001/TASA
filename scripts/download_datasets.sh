#!/bin/bash
# Download and preprocess all datasets for TASA

echo "=========================================="
echo "Downloading TASA Datasets"
echo "=========================================="

# Create data directory
mkdir -p ../data
cd ../data

# Download assist2017
echo ""
echo "📥 Downloading Assist2017..."
if [ ! -d "assist2017" ]; then
    wget https://sites.google.com/view/assistmentsdatamining/dataset -O assist2017.zip
    unzip assist2017.zip -d assist2017
    rm assist2017.zip
    echo "✅ Assist2017 downloaded"
else
    echo "⏭️  Assist2017 already exists, skipping"
fi

# Download NIPS Task 3&4
echo ""
echo "📥 Downloading NIPS Task 3&4..."
if [ ! -d "nips_task34" ]; then
    wget https://eedi.com/projects/neurips-education-challenge -O nips_task34.zip
    unzip nips_task34.zip -d nips_task34
    rm nips_task34.zip
    echo "✅ NIPS Task 3&4 downloaded"
else
    echo "⏭️  NIPS Task 3&4 already exists, skipping"
fi

# Download Algebra 2005
echo ""
echo "📥 Downloading Algebra 2005..."
if [ ! -d "algebra2005" ]; then
    wget https://pslcdatashop.web.cmu.edu/DatasetInfo?datasetId=195 -O algebra2005.zip
    unzip algebra2005.zip -d algebra2005
    rm algebra2005.zip
    echo "✅ Algebra 2005 downloaded"
else
    echo "⏭️  Algebra 2005 already exists, skipping"
fi

# Download Bridge to Algebra 2006
echo ""
echo "📥 Downloading Bridge to Algebra 2006..."
if [ ! -d "bridge2006" ]; then
    wget https://pslcdatashop.web.cmu.edu/DatasetInfo?datasetId=196 -O bridge2006.zip
    unzip bridge2006.zip -d bridge2006
    rm bridge2006.zip
    echo "✅ Bridge to Algebra 2006 downloaded"
else
    echo "⏭️  Bridge to Algebra 2006 already exists, skipping"
fi

cd ../scripts

echo ""
echo "=========================================="
echo "📦 Preprocessing Datasets"
echo "=========================================="

# Preprocess all datasets
for dataset in assist2017 nips_task34 algebra2005 bridge2006; do
    echo ""
    echo "🔄 Preprocessing $dataset..."
    python preprocess_dataset.py --dataset $dataset
done

echo ""
echo "=========================================="
echo "✅ All datasets downloaded and preprocessed!"
echo "=========================================="
echo ""
echo "📁 Data location: ../data/"
echo "📊 Available datasets:"
echo "   - assist2017    (1,708 students, 942K interactions)"
echo "   - nips_task34   (4,918 students, 1.38M interactions)"
echo "   - algebra2005   (574 students, 810K interactions)"
echo "   - bridge2006    (1,138 students, 3.68M interactions)"
echo ""
echo "Next steps:"
echo "  1. Train KT models: python train_kt_models.py --dataset assist2017 --model all"
echo "  2. Create student bank: python create_student_bank.py --dataset assist2017"
echo ""

