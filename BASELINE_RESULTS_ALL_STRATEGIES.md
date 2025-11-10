# Baseline Results - All Three Strategies

All 48 baseline experiments completed successfully! ✅

This document presents results under three different evaluation strategies:
- **Best**: Maximum score across two post-test runs
- **Average**: Mean score across two post-test runs  
- **Worst**: Minimum score across two post-test runs

---

## Strategy 1: Best (Max of Two Runs)

| Backbone | Method | Assist2017 | NIPS34 | Algebra2005 | Bridge2006 |
|----------|--------|-----------|--------|-------------|------------|
| **GPT-oss-120b** | Vanilla-ICL | 54.2 (1.5) | 42.2 (0.6) | 57.3 (1.0) | 48.0 (0.9) |
| | MathChat | 34.7 (1.6) | 45.0 (1.5) | 45.3 (1.8) | 37.9 (0.7) |
| | TutorLLM | 55.5 (1.2) | 36.2 (0.6) | 72.4 (0.9) | 56.1 (1.3) |
| | PSS-MV | 39.7 (0.6) | 53.3 (0.9) | 65.0 (1.5) | 43.5 (1.4) |
| **Qwen3-4B-Instruct** | Vanilla-ICL | 58.0 (0.9) | 61.1 (1.4) | 73.7 (1.7) | 45.7 (0.6) |
| | MathChat | 34.1 (1.7) | 28.4 (1.6) | 48.0 (1.1) | 48.8 (0.8) |
| | TutorLLM | 42.5 (1.9) | 37.4 (1.1) | 61.3 (0.7) | 47.3 (0.7) |
| | PSS-MV | 63.0 (1.8) | 49.2 (1.4) | 77.7 (1.7) | 53.1 (1.6) |
| **Llama3.1-8B-Instruct** | Vanilla-ICL | 54.7 (1.4) | 45.5 (2.0) | 68.3 (1.1) | 43.8 (1.4) |
| | MathChat | 43.0 (1.8) | 46.7 (1.5) | 64.4 (1.8) | 38.9 (1.4) |
| | TutorLLM | 50.0 (1.6) | 63.3 (0.7) | 75.5 (0.9) | 44.4 (1.0) |
| | PSS-MV | 48.1 (0.7) | 43.3 (0.9) | 75.8 (0.7) | 54.6 (1.0) |

**Best Performer:** PSS-MV + Qwen3-4B-Instruct on Algebra2005: **77.7 (1.7)**

---

## Strategy 2: Average (Mean of Two Runs)

| Backbone | Method | Assist2017 | NIPS34 | Algebra2005 | Bridge2006 |
|----------|--------|-----------|--------|-------------|------------|
| **GPT-oss-120b** | Vanilla-ICL | 44.8 (1.5) | 35.2 (1.1) | 46.1 (1.1) | 36.0 (0.9) |
| | MathChat | 23.0 (1.0) | 34.9 (1.9) | 36.8 (1.5) | 23.7 (1.5) |
| | TutorLLM | 43.6 (0.8) | 25.1 (1.6) | 62.1 (0.8) | 40.3 (1.1) |
| | PSS-MV | 23.6 (2.0) | 43.5 (1.5) | 50.5 (1.4) | 31.1 (1.6) |
| **Qwen3-4B-Instruct** | Vanilla-ICL | 47.6 (1.8) | 43.8 (1.7) | 61.9 (0.9) | 35.4 (0.6) |
| | MathChat | 25.5 (1.0) | 22.2 (1.0) | 41.7 (0.9) | 36.6 (1.9) |
| | TutorLLM | 38.0 (1.8) | 16.3 (1.0) | 51.8 (1.5) | 39.5 (1.2) |
| | PSS-MV | 53.0 (1.9) | 38.1 (1.2) | 68.4 (1.0) | 37.9 (0.9) |
| **Llama3.1-8B-Instruct** | Vanilla-ICL | 45.2 (1.4) | 33.4 (1.0) | 58.1 (1.4) | 35.5 (1.9) |
| | MathChat | 33.9 (1.2) | 31.1 (0.9) | 56.6 (2.0) | 31.8 (1.3) |
| | TutorLLM | 45.8 (0.7) | 50.1 (0.7) | 62.1 (0.8) | 36.5 (1.5) |
| | PSS-MV | 41.6 (1.7) | 26.3 (1.2) | 64.9 (0.7) | 43.9 (1.1) |

**Best Performer:** PSS-MV + Qwen3-4B-Instruct on Algebra2005: **68.4 (1.0)**

---

## Strategy 3: Worst (Min of Two Runs)

| Backbone | Method | Assist2017 | NIPS34 | Algebra2005 | Bridge2006 |
|----------|--------|-----------|--------|-------------|------------|
| **GPT-oss-120b** | Vanilla-ICL | 35.4 (2.0) | 28.2 (1.3) | 34.9 (2.0) | 24.0 (1.8) |
| | MathChat | 11.2 (0.6) | 24.8 (1.6) | 28.3 (1.6) | 9.4 (1.4) |
| | TutorLLM | 31.7 (1.0) | 14.1 (1.5) | 51.9 (0.8) | 24.4 (1.2) |
| | PSS-MV | 7.6 (1.2) | 33.6 (1.9) | 36.1 (1.8) | 18.8 (1.0) |
| **Qwen3-4B-Instruct** | Vanilla-ICL | 37.2 (1.3) | 26.6 (0.9) | 50.1 (1.9) | 25.0 (1.8) |
| | MathChat | 16.9 (1.0) | 16.0 (1.5) | 35.4 (1.5) | 24.4 (0.8) |
| | TutorLLM | 33.5 (1.7) | -4.8 (1.4) | 42.4 (1.7) | 31.7 (1.3) |
| | PSS-MV | 43.0 (0.6) | 27.1 (1.1) | 59.0 (0.6) | 22.7 (1.9) |
| **Llama3.1-8B-Instruct** | Vanilla-ICL | 35.8 (1.8) | 21.3 (1.8) | 47.8 (1.0) | 27.3 (0.7) |
| | MathChat | 24.8 (1.8) | 15.5 (1.9) | 48.7 (0.7) | 24.6 (1.3) |
| | TutorLLM | 41.7 (0.7) | 37.0 (1.7) | 48.8 (1.7) | 28.7 (0.8) |
| | PSS-MV | 35.1 (1.3) | 9.4 (1.4) | 54.0 (1.0) | 33.2 (1.8) |

**Best Performer:** PSS-MV + Qwen3-4B-Instruct on Algebra2005: **59.0 (0.6)**

---

## Key Insights

### Strategy Comparison

The three strategies show significantly different performance levels:

- **Best (Max)**: Most optimistic view, showing potential peak performance (avg ~50-55%)
- **Average (Mean)**: Realistic expected performance (avg ~35-40%)
- **Worst (Min)**: Conservative lower bound, reveals stability issues (avg ~25-30%)

### Variability Analysis

Large gaps between Best and Worst strategies indicate:
- High variance in model performance across runs
- Need for multiple evaluation runs
- Some methods/datasets are less stable

### Most Stable Combinations (smallest Best-Worst gap)

Looking at the data, methods with smaller gaps between max and min are more reliable.

---

*Generated on: October 22, 2025*  
*Metric: Learning Gain*  
*Format: mean (std)*  
*Note: Each student was evaluated with 2 post-test runs; strategies aggregate these differently*

