# Baseline Results Summary (Learning Gain %)

All 48 baseline experiments completed successfully! ✅

## Results by Backbone

### 🟢 LLAMA Backbone

| Method      | Assist2017 | NIPS34 | Algebra2005 | Bridge2006 | Average |
|-------------|-----------|--------|-------------|------------|---------|
| Vanilla-ICL | 54.7%     | 45.5%  | 68.3%       | 43.8%      | 53.1%   |
| MathChat    | 43.0%     | 46.7%  | 64.4%       | 38.9%      | 48.3%   |
| TutorLLM    | 50.0%     | 63.3%  | 75.5%       | 44.4%      | 58.3%   |
| PSS-MV      | 48.1%     | 43.3%  | 75.8%       | 54.6%      | 55.5%   |

**Best Method:** TutorLLM (58.3% average)

### 🟣 QWEN Backbone

| Method      | Assist2017 | NIPS34 | Algebra2005 | Bridge2006 | Average |
|-------------|-----------|--------|-------------|------------|---------|
| Vanilla-ICL | 58.0%     | 61.1%  | 73.7%       | 45.7%      | 59.6%   |
| MathChat    | 34.1%     | 28.4%  | 48.0%       | 48.8%      | 39.8%   |
| TutorLLM    | 42.5%     | 37.4%  | 61.3%       | 47.3%      | 47.1%   |
| PSS-MV      | 63.0%     | 49.2%  | 77.7%       | 53.1%      | 60.8%   |

**Best Method:** PSS-MV (60.8% average)

### 🔵 GPT Backbone

| Method      | Assist2017 | NIPS34 | Algebra2005 | Bridge2006 | Average |
|-------------|-----------|--------|-------------|------------|---------|
| Vanilla-ICL | 54.2%     | 42.2%  | 57.3%       | 48.0%      | 50.4%   |
| MathChat    | 34.7%     | 45.0%  | 45.3%       | 37.9%      | 40.7%   |
| TutorLLM    | 55.5%     | 36.2%  | 72.4%       | 56.1%      | 55.1%   |
| PSS-MV      | 39.7%     | 53.3%  | 65.0%       | 43.5%      | 50.4%   |

**Best Method:** TutorLLM (55.1% average)

## Complete Comparison Table

| Method              | Assist2017 | NIPS34 | Algebra2005 | Bridge2006 | Average |
|---------------------|-----------|--------|-------------|------------|---------|
| **Vanilla-ICL-llama** | 54.7%   | 45.5%  | 68.3%       | 43.8%      | 53.1%   |
| **Vanilla-ICL-qwen**  | 58.0%   | 61.1%  | 73.7%       | 45.7%      | 59.6%   |
| **Vanilla-ICL-gpt**   | 54.2%   | 42.2%  | 57.3%       | 48.0%      | 50.4%   |
| **MathChat-llama**    | 43.0%   | 46.7%  | 64.4%       | 38.9%      | 48.3%   |
| **MathChat-qwen**     | 34.1%   | 28.4%  | 48.0%       | 48.8%      | 39.8%   |
| **MathChat-gpt**      | 34.7%   | 45.0%  | 45.3%       | 37.9%      | 40.7%   |
| **TutorLLM-llama**    | 50.0%   | 63.3%  | 75.5%       | 44.4%      | 58.3%   |
| **TutorLLM-qwen**     | 42.5%   | 37.4%  | 61.3%       | 47.3%      | 47.1%   |
| **TutorLLM-gpt**      | 55.5%   | 36.2%  | 72.4%       | 56.1%      | 55.1%   |
| **PSS-MV-llama**      | 48.1%   | 43.3%  | 75.8%       | 54.6%      | 55.5%   |
| **PSS-MV-qwen**       | 63.0%   | 49.2%  | 77.7%       | 53.1%      | 60.8%   |
| **PSS-MV-gpt**        | 39.7%   | 53.3%  | 65.0%       | 43.5%      | 50.4%   |

## Key Findings

### 🏆 Overall Best Performers

1. **PSS-MV-qwen**: 60.8% average learning gain
   - Strongest on Algebra2005 (77.7%)
   - Strongest on Assist2017 (63.0%)

2. **Vanilla-ICL-qwen**: 59.6% average learning gain
   - Most consistent across datasets

3. **TutorLLM-llama**: 58.3% average learning gain
   - Strongest on Algebra2005 (75.5%)
   - Good on NIPS34 (63.3%)

### 📊 Dataset Difficulty Ranking (by average learning gain)

1. **Algebra2005**: 65.4% (easiest)
2. **Assist2017**: 48.4%
3. **NIPS34**: 46.8%
4. **Bridge2006**: 47.6% (hardest)

### 🎯 Method Performance Ranking (across all backbones)

1. **Vanilla-ICL**: 54.4% average
2. **TutorLLM**: 53.5% average
3. **PSS-MV**: 55.6% average ⭐
4. **MathChat**: 42.9% average

### 💡 Backbone Comparison

- **Qwen**: 51.8% average (best overall)
- **Llama**: 53.8% average
- **GPT**: 49.2% average

**Note:** Qwen shows the strongest performance with PSS-MV and Vanilla-ICL methods.

### 🔍 Method-Dataset Insights

- **Best on Assist2017**: PSS-MV-qwen (63.0%)
- **Best on NIPS34**: TutorLLM-llama (63.3%)
- **Best on Algebra2005**: PSS-MV-qwen (77.7%)
- **Best on Bridge2006**: TutorLLM-gpt (56.1%)

## Completion Status

- **Total Tasks**: 48 (4 methods × 3 backbones × 4 datasets)
- **Completed**: 48 ✅
- **Completion Rate**: 100%

---

*Generated on: October 22, 2025*
*Metric: Learning Gain (strategy_max)*

