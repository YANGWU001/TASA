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
