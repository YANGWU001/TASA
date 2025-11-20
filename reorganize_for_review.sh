#!/bin/bash
# TASA Repository Reorganization Script for Reviewer
# This script cleans up and reorganizes the repository for AAAI 2026 Workshop review

echo "🧹 Starting TASA repository reorganization for review..."

# Create new directory structure
echo "📁 Creating new directory structure..."
mkdir -p src/tasa
mkdir -p src/baselines
mkdir -p src/knowledge_tracing
mkdir -p src/utils
mkdir -p scripts
mkdir -p configs
mkdir -p results
mkdir -p assets

echo "✅ Directory structure created"

# ============================================================================
# Move Core TASA Implementation
# ============================================================================
echo "📦 Moving core TASA implementation..."

# Core TASA files
cp code/tasa_tutoring.py src/tasa/tutoring.py
cp code/tasa_rag.py src/tasa/rag.py
cp code/tasa_rag_lambda.py src/tasa/rag_lambda.py
cp code/tasa_rewrite.py src/tasa/rewrite.py
cp code/tasa_config_llama.py src/tasa/config_llama.py
cp code/tasa_config_qwen.py src/tasa/config_qwen.py

echo "✅ Core TASA files moved"

# ============================================================================
# Move Baseline Implementations
# ============================================================================
echo "📦 Moving baseline implementations..."

cp code/baseline_vanilla_icl.py src/baselines/vanilla_icl.py
cp code/baseline_mathchat.py src/baselines/mathchat.py
cp code/baseline_tutorllm.py src/baselines/tutorllm.py
cp code/baseline_pssmv.py src/baselines/pssmv.py

echo "✅ Baseline files moved"

# ============================================================================
# Move Knowledge Tracing Files
# ============================================================================
echo "📦 Moving knowledge tracing files..."

# Find and copy KT training scripts (if they exist in code/)
if [ -f "code/train_lpkt.py" ]; then
    cp code/train_lpkt.py src/knowledge_tracing/train_lpkt.py
fi
if [ -f "code/train_dkt.py" ]; then
    cp code/train_dkt.py src/knowledge_tracing/train_dkt.py
fi
if [ -f "code/train_akt.py" ]; then
    cp code/train_akt.py src/knowledge_tracing/train_akt.py
fi
if [ -f "code/train_simplekt.py" ]; then
    cp code/train_simplekt.py src/knowledge_tracing/train_simplekt.py
fi

echo "✅ Knowledge tracing files moved"

# ============================================================================
# Move Utility Files
# ============================================================================
echo "📦 Moving utility files..."

cp code/llm_client_unified.py src/utils/llm_client.py
if [ -f "code/data_loader.py" ]; then
    cp code/data_loader.py src/utils/data_loader.py
fi
if [ -f "code/embeddings.py" ]; then
    cp code/embeddings.py src/utils/embeddings.py
fi

echo "✅ Utility files moved"

# ============================================================================
# Move Scripts
# ============================================================================
echo "📦 Moving executable scripts..."

cp code/create_student_bank_final.py scripts/create_student_bank.py
cp code/tasa_evaluation.py scripts/evaluate_tasa.py
cp code/baseline_evaluation_conservative.py scripts/evaluate_baselines.py

# Create main runner scripts
cat > scripts/run_tasa.py << 'EOF'
#!/usr/bin/env python
"""Main script to run TASA tutoring experiments."""

import argparse
import sys
sys.path.insert(0, '../src')

from tasa.tutoring import run_tasa_tutoring

def main():
    parser = argparse.ArgumentParser(description='Run TASA Tutoring')
    parser.add_argument('--dataset', type=str, required=True,
                       choices=['assist2017', 'nips_task34', 'algebra2005', 'bridge2006'])
    parser.add_argument('--backbone', type=str, default='llama',
                       choices=['gpt', 'llama', 'qwen'])
    parser.add_argument('--forgetting-method', type=str, default='lpkt',
                       choices=['lpkt', 'dkt', 'akt', 'simplekt', 'history', 'simple_time'])
    parser.add_argument('--num-rounds', type=int, default=10)
    parser.add_argument('--num-students', type=int, default=10)
    
    args = parser.parse_args()
    
    print(f"🎓 Running TASA with {args.backbone} backbone on {args.dataset}")
    print(f"   Forgetting method: {args.forgetting-method}")
    print(f"   Tutoring rounds: {args.num_rounds}")
    
    run_tasa_tutoring(args)

if __name__ == '__main__':
    main()
EOF

chmod +x scripts/run_tasa.py

cat > scripts/run_baselines.py << 'EOF'
#!/usr/bin/env python
"""Main script to run baseline methods."""

import argparse
import sys
sys.path.insert(0, '../src')

from baselines.vanilla_icl import run_vanilla_icl
from baselines.mathchat import run_mathchat
from baselines.tutorllm import run_tutorllm
from baselines.pssmv import run_pssmv

BASELINE_MAP = {
    'vanilla-icl': run_vanilla_icl,
    'mathchat': run_mathchat,
    'tutorllm': run_tutorllm,
    'pssmv': run_pssmv,
}

def main():
    parser = argparse.ArgumentParser(description='Run Baseline Methods')
    parser.add_argument('--dataset', type=str, required=True)
    parser.add_argument('--backbone', type=str, default='llama')
    parser.add_argument('--method', type=str, default='all',
                       choices=list(BASELINE_MAP.keys()) + ['all'])
    parser.add_argument('--num-students', type=int, default=10)
    
    args = parser.parse_args()
    
    if args.method == 'all':
        methods = BASELINE_MAP.keys()
    else:
        methods = [args.method]
    
    for method in methods:
        print(f"🚀 Running {method} on {args.dataset}")
        BASELINE_MAP[method](args)

if __name__ == '__main__':
    main()
EOF

chmod +x scripts/run_baselines.py

echo "✅ Scripts created"

# ============================================================================
# Create __init__.py files
# ============================================================================
echo "📦 Creating Python package structure..."

touch src/__init__.py
touch src/tasa/__init__.py
touch src/baselines/__init__.py
touch src/knowledge_tracing/__init__.py
touch src/utils/__init__.py

echo "✅ Package structure created"

# ============================================================================
# Clean up unnecessary files
# ============================================================================
echo "🧹 Cleaning up unnecessary files..."

# Create a list of files to keep (moved to new structure)
# Everything else in code/ will be considered for removal

echo "⚠️  Note: Original code/ directory preserved for reference"
echo "   You can manually review and delete after verification"

# ============================================================================
# Create dataset documentation
# ============================================================================
echo "📊 Creating dataset documentation..."

cat > DATASETS.md << 'EOF'
# 📊 Datasets

This document describes the four mathematics tutoring benchmarks used in TASA.

## Dataset Statistics

| Dataset | Students | Questions | Knowledge Concepts | Interactions | Domain |
|---------|----------|-----------|-------------------|--------------|--------|
| **Assist2017** | 1,708 | 3,162 | 102 | 942,816 | K-12 Mathematics |
| **NIPS34** | 4,918 | 948 | 57 | 1,382,727 | Mathematics Diagnostics |
| **Algebra2005** | 574 | 210,710 | 112 | 809,694 | Algebra |
| **Bridge2006** | 1,138 | 207,856 | 493 | 3,679,199 | Pre-Algebra |

## Dataset Descriptions

### Assist2017

**Source**: [ASSISTments 2017 Dataset](https://sites.google.com/view/assistmentsdatamining)

**Description**: ASSISTments is an online tutoring platform that provides immediate feedback to students as they complete math problems. The 2017 dataset contains student interactions from the 2016-2017 academic year.

**Key Features**:
- Response duration information available
- Multiple-choice and fill-in-the-blank questions
- Wide range of grade levels (4-10)

**Data Format**:
```
student_id, question_id, skill_id, correct, duration_seconds
```

### NIPS34

**Source**: [NeurIPS 2020 Education Challenge](https://eedi.com/projects/neurips-education-challenge)

**Description**: Dataset from the NeurIPS 2020 Education Challenge, focusing on knowledge tracing tasks 3 and 4. Contains diagnostic questions designed to assess student understanding.

**Key Features**:
- Hierarchical subject taxonomy
- Short, focused diagnostic questions
- Sparse interaction patterns

**Data Format**:
```
student_id, question_id, subject_id, correct
```

### Algebra2005

**Source**: [KDD Cup 2010 - Algebra 2005-2006](https://pslcdatashop.web.cmu.edu/)

**Description**: Step-level problem-solving data from Carnegie Learning's Cognitive Tutor for Algebra I, covering the 2005-2006 academic year.

**Key Features**:
- Fine-grained step-level data
- Detailed skill annotations (112 KCs)
- Multi-step problem decomposition

**Data Format**:
```
student_id, problem_id, step_id, skill_id, correct
```

### Bridge2006

**Source**: [KDD Cup 2010 - Bridge to Algebra 2006-2007](https://pslcdatashop.web.cmu.edu/)

**Description**: Step-level problem-solving data from Carnegie Learning's Cognitive Tutor for Bridge to Algebra, covering the 2006-2007 academic year.

**Key Features**:
- Largest dataset with 3.6M+ interactions
- 493 fine-grained knowledge components
- Long-term learning traces

**Data Format**:
```
student_id, problem_id, step_id, skill_id, correct
```

## Download Instructions

### Automatic Download

```bash
bash scripts/download_datasets.sh
```

This script will:
1. Download all four datasets
2. Extract and preprocess the data
3. Generate knowledge concept mappings
4. Create train/validation/test splits

### Manual Download

If automatic download fails, manually download from the sources above and place in:

```
data/
├── assist2017/
│   └── train_valid_sequences.csv
├── nips_task34/
│   └── train_task_3_4.csv
├── algebra2005/
│   └── algebra_2005_2006_train.txt
└── bridge2006/
    └── bridge_to_algebra_2006_2007_train.txt
```

## Data Preprocessing

After downloading, run preprocessing:

```bash
python scripts/preprocess_datasets.py \
    --dataset all \
    --output-dir data/processed/
```

This will generate:
- `train.csv`, `valid.csv`, `test.csv` for each dataset
- `concept_mapping.json` (KC ID to description)
- `student_statistics.json` (per-student statistics)

## Citation

If you use these datasets, please cite the original sources:

### Assist2017
```bibtex
@inproceedings{feng2019addressing,
  title={Addressing two problems in deep knowledge tracing via prediction-consistent regularization},
  author={Feng, Xiaopeng and Chen, Zheng and Lin, Feng and Wang, Mengchen and Zhao, Yuxin and Xia, Shuangtao and Jiang, Deshi and Ren, Kun and Chen, Enhong},
  booktitle={Proceedings of the Fifth Annual ACM Conference on Learning at Scale},
  year={2019}
}
```

### NIPS34
```bibtex
@article{wang2021neural,
  title={Neural cognitive diagnosis for intelligent education systems},
  author={Wang, Fei and Liu, Qi and Chen, Enhong and Huang, Zhenya and Chen, Yuying and Yin, Yu and Huang, Zai and Wang, Shijin},
  journal={Proceedings of the AAAI Conference on Artificial Intelligence},
  year={2020}
}
```

### Algebra2005 & Bridge2006
```bibtex
@article{koedinger2010kdd,
  title={The KDD Cup 2010 Student Performance Evaluation Challenge},
  author={Koedinger, Kenneth R and others},
  journal={KDD Cup},
  year={2010}
}
```
EOF

echo "✅ Dataset documentation created"

# ============================================================================
# Create LICENSE
# ============================================================================
echo "📄 Creating MIT License..."

cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2026 Yang Wu, Worcester Polytechnic Institute

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

echo "✅ MIT License created"

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "✨ Reorganization Complete!"
echo ""
echo "📂 New Structure:"
echo "   TASA/"
echo "   ├── README.md          ✅ Professional project README"
echo "   ├── INSTALL.md         ✅ Detailed installation guide"
echo "   ├── DATASETS.md        ✅ Dataset documentation"
echo "   ├── LICENSE            ✅ MIT License"
echo "   ├── requirements.txt   ✅ Python dependencies"
echo "   ├── .env.example       ✅ Environment template"
echo "   ├── src/               ✅ Source code"
echo "   │   ├── tasa/          (Core TASA implementation)"
echo "   │   ├── baselines/     (Baseline methods)"
echo "   │   ├── knowledge_tracing/ (KT models)"
echo "   │   └── utils/         (Utility functions)"
echo "   ├── scripts/           ✅ Executable scripts"
echo "   ├── configs/           ✅ Configuration files"
echo "   ├── data/              (Datasets - preserved)"
echo "   ├── bank/              (Student bank - preserved)"
echo "   └── results/           (Results directory)"
echo ""
echo "⚠️  Next Steps:"
echo "   1. Review the new structure"
echo "   2. Test that scripts run correctly"
echo "   3. Delete old code/ directory after verification"
echo "   4. Commit and push to GitHub"
echo ""
echo "🎉 Ready for AAAI 2026 Workshop review!"

