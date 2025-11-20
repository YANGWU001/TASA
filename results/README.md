# 📊 Results Directory

This directory contains evaluation results from TASA and baseline experiments.

## Directory Structure

```
results/
├── tasa/                    # TASA method results
│   ├── assist2017/
│   ├── nips_task34/
│   ├── algebra2005/
│   └── bridge2006/
│
├── baselines/               # Baseline method results
│   ├── vanilla-icl/
│   ├── mathchat/
│   ├── tutorllm/
│   └── pssmv/
│
└── figures/                 # Result visualizations
    ├── learning_gains.png
    ├── win_rates.png
    └── forgetting_ablation.png
```

## File Formats

### Individual Student Results

Each student's result file contains:
```json
{
  "student_id": "123",
  "dataset": "assist2017",
  "method": "TASA",
  "backbone": "llama",
  "pre_test": {
    "score": 45.2,
    "questions": [...]
  },
  "post_test": {
    "attempt_1": {"score": 67.8, ...},
    "attempt_2": {"score": 72.3, ...},
    "best_score": 72.3
  },
  "learning_gain": 49.5,
  "dialogue": [...]
}
```

### Aggregated Results

Overall statistics per method/dataset:
```json
{
  "method": "TASA",
  "dataset": "assist2017",
  "num_students": 10,
  "avg_learning_gain": 53.8,
  "std_learning_gain": 1.3,
  "avg_post_test": 75.6,
  "success_rate": 100.0
}
```

## Reproducing Results

To reproduce the results in the paper:

```bash
# Run TASA on all datasets
python scripts/run_tasa.py --dataset all --forgetting-method lpkt

# Run all baselines
python scripts/run_baselines.py --dataset all --method all

# Generate comparison tables
python scripts/evaluate_results.py --compare --output results/comparison.csv
```

## Evaluation Metrics

- **Learning Gain**: `(post_test - pre_test) / (100 - pre_test)`
- **Post-test Score**: Best of 2 attempts after tutoring
- **Success Rate**: Percentage of students who completed all evaluations
- **Win Rate**: LLM-as-judge pairwise comparisons

## Notes

- All results use the "best-of-2" post-test strategy
- Pre-tests and post-tests contain 10 questions each
- Tutoring consists of 10 rounds of interaction
- Statistical significance tested with paired t-tests (p < 0.05)

