# 🚀 Scripts

This directory contains executable scripts for running TASA experiments.

## Main Scripts

### `run_tasa.py`
Run TASA tutoring experiments

```bash
python scripts/run_tasa.py \
    --dataset assist2017 \
    --backbone llama \
    --forgetting-method lpkt \
    --num-rounds 10 \
    --num-students 10
```

**Arguments**:
- `--dataset`: Dataset name (`assist2017`, `nips_task34`, `algebra2005`, `bridge2006`)
- `--backbone`: LLM backbone (`gpt`, `llama`, `qwen`)
- `--forgetting-method`: Method for calculating forgetting scores
  - `lpkt`: Learning Process-consistent KT (best)
  - `dkt`: Deep Knowledge Tracing
  - `akt`: Attentive Knowledge Tracing
  - `simplekt`: SimpleKT
  - `history`: Historical performance-based
  - `simple_time`: Simple time decay
- `--num-rounds`: Number of tutoring rounds (default: 10)
- `--num-students`: Number of students to tutor (default: 10)

---

### `run_baselines.py`
Run baseline method experiments

```bash
python scripts/run_baselines.py \
    --dataset assist2017 \
    --backbone llama \
    --method all \
    --num-students 10
```

**Arguments**:
- `--dataset`: Dataset name
- `--backbone`: LLM backbone
- `--method`: Baseline method (`vanilla-icl`, `mathchat`, `tutorllm`, `pssmv`, `all`)
- `--num-students`: Number of students

---

### `create_student_bank.py`
Create student bank with persona, memory, and embeddings

```bash
python scripts/create_student_bank.py \
    --dataset assist2017 \
    --num-students 100 \
    --use-fp16
```

**Arguments**:
- `--dataset`: Dataset to process
- `--num-students`: Number of students (default: all)
- `--use-fp16`: Use FP16 for faster embedding generation

**Output**: Creates `bank/{persona,memory,session}/dataset/` directories

---

### `evaluate_tasa.py`
Evaluate TASA results

```bash
python scripts/evaluate_tasa.py \
    --method TASA \
    --dataset assist2017 \
    --forgetting-method lpkt
```

---

### `evaluate_baselines.py`
Evaluate baseline results

```bash
python scripts/evaluate_baselines.py \
    --dataset assist2017 \
    --method all
```

---

## Utility Scripts

### `download_datasets.sh`
Download and prepare all datasets

```bash
bash scripts/download_datasets.sh
```

### `train_kt_models.py`
Train knowledge tracing models

```bash
python scripts/train_kt_models.py \
    --dataset assist2017 \
    --model lpkt \
    --epochs 100
```

---

## Full Experiment Pipeline

To reproduce all results from the paper:

```bash
# 1. Download datasets
bash scripts/download_datasets.sh

# 2. Create student bank for all datasets
for dataset in assist2017 nips_task34 algebra2005 bridge2006; do
    python scripts/create_student_bank.py --dataset $dataset
done

# 3. Train knowledge tracing models
for dataset in assist2017 nips_task34 algebra2005 bridge2006; do
    python scripts/train_kt_models.py --dataset $dataset --model lpkt --epochs 100
done

# 4. Run TASA experiments
for dataset in assist2017 nips_task34 algebra2005 bridge2006; do
    python scripts/run_tasa.py \
        --dataset $dataset \
        --backbone llama \
        --forgetting-method lpkt \
        --num-students 40
done

# 5. Run baseline experiments
for dataset in assist2017 nips_task34 algebra2005 bridge2006; do
    python scripts/run_baselines.py \
        --dataset $dataset \
        --backbone llama \
        --method all \
        --num-students 40
done

# 6. Evaluate and compare
python scripts/evaluate_results.py --compare --output results/comparison.csv
```

---

## Parallel Execution

For faster experiments on multi-GPU systems:

```bash
# Run on multiple GPUs in parallel
CUDA_VISIBLE_DEVICES=0 python scripts/run_tasa.py --dataset assist2017 &
CUDA_VISIBLE_DEVICES=1 python scripts/run_tasa.py --dataset nips_task34 &
CUDA_VISIBLE_DEVICES=2 python scripts/run_tasa.py --dataset algebra2005 &
CUDA_VISIBLE_DEVICES=3 python scripts/run_tasa.py --dataset bridge2006 &
wait
```

---

## Expected Runtime

On a system with RTX 3090 GPU:

| Task | Time per Student | Total (40 students) |
|------|------------------|---------------------|
| Create Student Bank | ~2 min | ~1.5 hours |
| Train LPKT | ~30 min | ~30 min |
| Run TASA (10 rounds) | ~5 min | ~3.5 hours |
| Run Baseline | ~3 min | ~2 hours |

---

## Output Locations

- Student Bank: `bank/{persona,memory,session}/{dataset}/`
- KT Models: `models/{dataset}/{lpkt,dkt,akt,simplekt}/`
- Results: `results/{tasa,baselines}/{dataset}/`
- Logs: `logs/{timestamp}/`

