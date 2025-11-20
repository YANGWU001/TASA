# 📦 Installation Guide

This document provides detailed instructions for setting up the TASA environment.

---

## System Requirements

### Hardware
- **CPU**: Multi-core processor (8+ cores recommended)
- **RAM**: 16GB minimum, 32GB+ recommended
- **GPU**: NVIDIA GPU with 16GB+ VRAM (for LLM inference and embedding generation)
  - Recommended: RTX 3090, RTX 4090, A100, or better
- **Storage**: ~100GB free disk space for datasets, models, and results

### Software
- **OS**: Linux (Ubuntu 20.04+), macOS (12.0+), or Windows 10/11 with WSL2
- **Python**: 3.10 or 3.11
- **CUDA**: 12.4+ (if using GPU)
- **Git**: For cloning repositories

---

## Installation Methods

### Method 1: Conda (Recommended)

#### Step 1: Install Conda/Miniconda

If you don't have Conda installed:

```bash
# Download Miniconda installer
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Install Miniconda
bash Miniconda3-latest-Linux-x86_64.sh

# Restart your terminal or source bashrc
source ~/.bashrc
```

#### Step 2: Create Environment

```bash
# Clone TASA repository
git clone https://github.com/YANGWU001/TASA.git
cd TASA

# Create conda environment
conda create -n tasa python=3.10 -y
conda activate tasa
```

#### Step 3: Install PyTorch

```bash
# For CUDA 12.4
pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 \
    --index-url https://download.pytorch.org/whl/cu124

# For CPU only (not recommended for production)
pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 \
    --index-url https://download.pytorch.org/whl/cpu
```

#### Step 4: Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Install pykt-toolkit for knowledge tracing
git clone https://github.com/pykt-team/pykt-toolkit.git
cd pykt-toolkit && pip install -e . && cd ..
```

#### Step 5: Verify Installation

```bash
# Run environment test
python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA Available: {torch.cuda.is_available()}')
print(f'CUDA Version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}')

from FlagEmbedding import BGEM3FlagModel
print('FlagEmbedding: OK')

from pykt.models import LPKT
print('PyKT: OK')
"
```

---

### Method 2: Docker (Coming Soon)

```bash
# Pull Docker image
docker pull yangwu001/tasa:latest

# Run container
docker run --gpus all -it -v $(pwd):/workspace yangwu001/tasa:latest
```

---

## Configuration

### 1. Environment Variables

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` with your API credentials:

```bash
# API Keys
API_KEY=your_api_key_here

# LLM Endpoints
GPT_ENDPOINT=https://api.openai.com/v1
LLAMA_URL=https://your_llama_endpoint/predict/
QWEN_URL=https://your_qwen_endpoint/predict/

# Optional: HuggingFace Mirror (for faster model downloads)
HF_ENDPOINT=https://hf-mirror.com
```

### 2. Download Pre-trained Models

```bash
# Download BGE-M3 embedding model
python -c "from FlagEmbedding import BGEM3FlagModel; \
           model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)"

# Download BGE reranker model
python -c "from FlagEmbedding import FlagReranker; \
           reranker = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True)"
```

---

## Dataset Setup

### Download Datasets

```bash
# Create data directory
mkdir -p data

# Download and prepare all datasets
bash scripts/download_datasets.sh
```

### Manual Dataset Download

If automatic download fails, manually download from:

1. **Assist2017**: [ASSISTments 2017 Dataset](https://sites.google.com/view/assistmentsdatamining)
2. **NIPS34**: [NeurIPS 2020 Education Challenge](https://eedi.com/projects/neurips-education-challenge)
3. **Algebra2005**: [KDD Cup 2010](https://pslcdatashop.web.cmu.edu/)
4. **Bridge2006**: [KDD Cup 2010](https://pslcdatashop.web.cmu.edu/)

Place downloaded files in:
```
data/
├── assist2017/train_valid_sequences.csv
├── nips_task34/train_task_3_4.csv
├── algebra2005/algebra_2005_2006_train.txt
└── bridge2006/bridge_to_algebra_2006_2007_train.txt
```

---

## Common Issues and Solutions

### Issue 1: CUDA Out of Memory

**Solution**: Reduce batch size or use gradient accumulation

```python
# In config file
BATCH_SIZE = 8  # Reduce from default 16
```

### Issue 2: PyKT Installation Fails

**Solution**: Install from source

```bash
git clone https://github.com/pykt-team/pykt-toolkit.git
cd pykt-toolkit
pip install -e . --no-deps
pip install -r requirements.txt
cd ..
```

### Issue 3: FlagEmbedding Model Download Slow

**Solution**: Use HuggingFace mirror

```bash
export HF_ENDPOINT=https://hf-mirror.com
python -c "from FlagEmbedding import BGEM3FlagModel; \
           BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)"
```

### Issue 4: OpenMP Error on macOS

**Solution**: Install libomp

```bash
brew install libomp
```

---

## Development Setup

### Install Development Dependencies

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Run Tests

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_tasa_tutoring.py

# Run with coverage
pytest --cov=src tests/
```

---

## Performance Optimization

### GPU Acceleration

```bash
# Set CUDA device
export CUDA_VISIBLE_DEVICES=0

# Enable TF32 for faster computation (on Ampere+ GPUs)
export TORCH_ALLOW_TF32_CUBLAS_OVERRIDE=1
```

### Multi-GPU Setup

```bash
# Use multiple GPUs for parallel processing
python scripts/run_tasa.py \
    --gpus 0,1,2,3 \
    --num-workers 40
```

### Memory Optimization

```bash
# Enable mixed precision training
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Use fp16 for embeddings
python scripts/create_student_bank.py --use-fp16
```

---

## Uninstallation

```bash
# Remove conda environment
conda deactivate
conda env remove -n tasa

# Remove cloned repository
rm -rf TASA/
```

---

## Next Steps

After installation, proceed to:

1. [Quick Start Guide](README.md#quick-start) - Run your first experiment
2. [Dataset Preparation](README.md#datasets) - Download and prepare datasets
3. [Usage Examples](README.md#usage) - Learn how to use TASA

---

## Support

If you encounter any issues during installation:

1. Check [Common Issues](#common-issues-and-solutions)
2. Search existing [GitHub Issues](https://github.com/YANGWU001/TASA/issues)
3. Open a new issue with:
   - OS and Python version
   - Complete error message
   - Steps to reproduce

---

<div align="center">
  <strong>✅ Installation complete! Ready to run TASA.</strong>
</div>

