# 🎓 TASA: Teaching According to Students' Aptitude

[![Paper](https://img.shields.io/badge/Paper-arXiv-b31b1b)](https://arxiv.org/abs/2511.15163)
[![Conference](https://img.shields.io/badge/AAAI%202026-Workshop-blue)](https://aaai.org/conference/aaai/aaai-26/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Personalized Mathematics Tutoring via Persona-, Memory-, and Forgetting-Aware LLMs**

<div align="center">
  <img src="https://img.shields.io/badge/Status-AAAI%202026%20Workshop%20Accepted-success" alt="Status">
</div>

---

## 📖 Overview

TASA (Teaching According to Students' Aptitude) is a personalized mathematics tutoring framework that integrates three synergistic components into a unified LLM tutor:

- **🎭 Persona Modeling**: Constructs individualized student profiles capturing proficiency and traits across skills
- **💾 Event Memory**: Maintains records of recent problem-solving episodes
- **⏰ Forgetting-Aware Dynamics**: Continuously estimates knowledge retention using temporal decay models

Unlike existing personalization methods that treat retrieved student information as static snapshots, TASA dynamically adjusts tutoring responses by applying temporal decay to retrieved persona and memory, enabling instruction based on temporally decayed mastery estimates.

![TASA Framework](./assets/framework.png)
*Figure 1: Given the same query, TASA generates personalized tutoring responses for two students based on their forgetting-adjusted persona and memory.*

---

## 🏆 Key Features

- ✅ **Temporal Forgetting Modeling**: Integrates cognitive psychology principles with knowledge tracing
- ✅ **Multi-Dataset Support**: Evaluated on 4 mathematics tutoring benchmarks (Assist2017, NIPS34, Algebra2005, Bridge2006)
- ✅ **Multiple LLM Backbones**: Supports GPT-4, Llama-3.1-8B, Qwen3-4B
- ✅ **Comprehensive Baselines**: Includes Vanilla-ICL, MathChat, TutorLLM, PSS-MV
- ✅ **Knowledge Tracing Integration**: LPKT, DKT, AKT, SimpleKT for forgetting score estimation
- ✅ **RAG-Enhanced Retrieval**: Uses BGE-M3 for efficient persona and memory retrieval

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- CUDA 12.4+ (for GPU acceleration)
- 16GB+ RAM
- ~100GB disk space (for datasets and models)

### Installation

```bash
# Clone the repository
git clone https://github.com/YANGWU001/TASA.git
cd TASA

# Create conda environment
conda create -n tasa python=3.10 -y
conda activate tasa

# Install PyTorch with CUDA support
pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 \
    --index-url https://download.pytorch.org/whl/cu124

# Install dependencies
pip install -r requirements.txt

# Install pykt-toolkit for knowledge tracing
git clone https://github.com/pykt-team/pykt-toolkit.git
cd pykt-toolkit && pip install -e . && cd ..
```

For detailed installation instructions, see [INSTALL.md](./INSTALL.md).

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API credentials
nano .env
```

---

## 📊 Datasets

We evaluate TASA on four mathematics tutoring benchmarks:

| Dataset | Students | Questions | Knowledge Concepts | Interactions |
|---------|----------|-----------|-------------------|--------------|
| **Assist2017** | 1,708 | 3,162 | 102 | 942,816 |
| **NIPS34** | 4,918 | 948 | 57 | 1,382,727 |
| **Algebra2005** | 574 | 210,710 | 112 | 809,694 |
| **Bridge2006** | 1,138 | 207,856 | 493 | 3,679,199 |

### Download Datasets

```bash
# Download and prepare datasets
bash scripts/download_datasets.sh
```

Datasets will be automatically processed and placed in `data/`.

---

## 🎯 Usage

### 1. Create Student Bank

```bash
# Generate student persona, memory, and embeddings
python scripts/create_student_bank.py \
    --dataset assist2017 \
    --num-students 100
```

### 2. Train Knowledge Tracing Models

```bash
# Train LPKT model for forgetting score estimation
python scripts/train_kt_models.py \
    --dataset assist2017 \
    --model lpkt \
    --epochs 100
```

### 3. Run TASA Tutoring

```bash
# Run TASA with Llama backbone
python scripts/run_tasa.py \
    --dataset assist2017 \
    --backbone llama \
    --forgetting-method lpkt \
    --num-rounds 10
```

### 4. Run Baseline Methods

```bash
# Run all baselines (Vanilla-ICL, MathChat, TutorLLM, PSS-MV)
python scripts/run_baselines.py \
    --dataset assist2017 \
    --backbone llama
```

### 5. Evaluate Results

```bash
# Evaluate learning gains and win rates
python scripts/evaluate_results.py \
    --method TASA \
    --dataset assist2017
```

---

## 📈 Results

### Learning Gain Comparison (%)

| Method | Assist2017 | NIPS34 | Algebra2005 | Bridge2006 | Average |
|--------|-----------|---------|-------------|------------|---------|
| **Vanilla-ICL** | 42.3±1.5 | 45.8±1.2 | 40.1±0.9 | 43.7±1.1 | 43.0 |
| **MathChat** | 45.6±1.3 | 48.2±1.4 | 43.2±1.2 | 46.1±0.8 | 45.8 |
| **TutorLLM** | 47.8±1.1 | 50.5±1.6 | 45.4±1.3 | 48.3±1.4 | 48.0 |
| **PSS-MV** | 49.2±0.9 | 52.1±1.3 | 46.8±1.1 | 49.7±1.2 | 49.5 |
| **TASA (Ours)** | **53.8±1.3** | **57.9±1.1** | **51.2±1.7** | **55.8±1.2** | **54.7** |

### Forgetting Method Ablation (LPKT vs. Simple Time)

TASA with LPKT-based forgetting scores achieves **+5.6%** average learning gain improvement over simple time-based forgetting.

---

## 🔬 Project Structure

```
TASA/
├── README.md                    # This file
├── INSTALL.md                   # Detailed installation guide
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
│
├── src/                         # Source code
│   ├── tasa/                    # Core TASA implementation
│   │   ├── tutoring.py         # Main tutoring logic
│   │   ├── rag.py              # RAG retrieval
│   │   ├── rewrite.py          # Mastery rewriter
│   │   ├── forgetting.py       # Forgetting score calculation
│   │   └── config.py           # TASA configuration
│   │
│   ├── baselines/              # Baseline methods
│   │   ├── vanilla_icl.py     # Vanilla In-Context Learning
│   │   ├── mathchat.py        # MathChat
│   │   ├── tutorllm.py        # TutorLLM
│   │   └── pssmv.py           # PSS-MV
│   │
│   ├── knowledge_tracing/      # Knowledge tracing models
│   │   ├── lpkt.py            # Learning Process-consistent KT
│   │   ├── dkt.py             # Deep Knowledge Tracing
│   │   ├── akt.py             # Attentive Knowledge Tracing
│   │   └── simplekt.py        # SimpleKT
│   │
│   └── utils/                  # Utility functions
│       ├── data_loader.py     # Dataset loading
│       ├── llm_client.py      # LLM API client
│       ├── embeddings.py      # BGE-M3 embeddings
│       └── evaluation.py      # Evaluation metrics
│
├── scripts/                    # Executable scripts
│   ├── download_datasets.sh   # Download datasets
│   ├── create_student_bank.py # Create student bank
│   ├── train_kt_models.py     # Train KT models
│   ├── run_tasa.py            # Run TASA
│   ├── run_baselines.py       # Run baselines
│   └── evaluate_results.py    # Evaluate results
│
├── configs/                    # Configuration files
│   ├── tasa_config.yaml       # TASA configuration
│   ├── llama_config.yaml      # Llama backbone config
│   └── qwen_config.yaml       # Qwen backbone config
│
├── data/                       # Datasets (after download)
│   ├── assist2017/
│   ├── nips_task34/
│   ├── algebra2005/
│   └── bridge2006/
│
├── bank/                       # Student bank (generated)
│   ├── persona/               # Student profiles
│   ├── memory/                # Learning events
│   ├── session/               # Session data
│   └── forgetting/            # Forgetting scores
│
└── results/                    # Evaluation results
    ├── tasa/                  # TASA results
    ├── baselines/             # Baseline results
    └── figures/               # Result visualizations
```

---

## 📝 Citation

If you find this work useful, please cite our paper:

```bibtex
@inproceedings{wu2026tasa,
  title={Teaching According to Students' Aptitude: Personalized Mathematics Tutoring via Persona-, Memory-, and Forgetting-Aware LLMs},
  author={Wu, Yang and Yao, Rujing and Zhang, Tong and Shi, Yufei and Jiang, Zhuoren and Li, Zhushan and Liu, Xiaozhong},
  booktitle={AAAI 2026 Workshop},
  year={2026}
}
```

---

## 👥 Authors

- **Yang Wu** (Worcester Polytechnic Institute) - ywu19@wpi.edu
- **Rujing Yao** (Nankai University)
- **Tong Zhang** (Nankai University)
- **Yufei Shi** (The Hong Kong Polytechnic University)
- **Zhuoren Jiang** (Zhejiang University)
- **Zhushan Li** (Boston College)
- **Xiaozhong Liu** (Worcester Polytechnic Institute) - xliu14@wpi.edu

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

This work builds upon:
- [PyKT-Toolkit](https://github.com/pykt-team/pykt-toolkit) for knowledge tracing models
- [FlagEmbedding](https://github.com/FlagOpen/FlagEmbedding) for BGE-M3 embeddings
- [Transformers](https://github.com/huggingface/transformers) for LLM integration

---

## 📧 Contact

For questions or collaboration, please contact:
- Yang Wu: ywu19@wpi.edu
- Xiaozhong Liu: xliu14@wpi.edu

---

<div align="center">
  <strong>⭐ If you find this project helpful, please give it a star! ⭐</strong>
</div>
