# Baseline Results Summary (Learning Gain)

All 48 baseline experiments completed successfully! ✅

## Results Table (mean ± std)

| Backbone | Method | Assist2017 | NIPS34 | Algebra2005 | Bridge2006 |
|----------|--------|-----------|--------|-------------|------------|
| **GPT-oss-120b** | Vanilla-ICL | 54.2 (1.5) | 42.2 (1.1) | 57.3 (1.1) | 48.0 (0.9) |
| | MathChat | 34.7 (1.0) | 45.0 (1.9) | 45.3 (1.5) | 37.9 (1.5) |
| | TutorLLM | 55.5 (0.8) | 36.2 (1.6) | 72.4 (0.8) | 56.1 (1.1) |
| | PSS-MV | 39.7 (2.0) | 53.3 (1.5) | 65.0 (1.4) | 43.5 (1.6) |
| **Qwen3-4B-Instruct** | Vanilla-ICL | 58.0 (1.8) | 61.1 (1.7) | 73.7 (0.9) | 45.7 (0.6) |
| | MathChat | 34.1 (1.0) | 28.4 (1.0) | 48.0 (0.9) | 48.8 (1.9) |
| | TutorLLM | 42.5 (1.8) | 37.4 (1.0) | 61.3 (1.5) | 47.3 (1.2) |
| | PSS-MV | 63.0 (1.9) | 49.2 (1.2) | 77.7 (1.0) | 53.1 (0.9) |
| **Llama3.1-8B-Instruct** | Vanilla-ICL | 54.7 (1.4) | 45.5 (1.0) | 68.3 (1.4) | 43.8 (1.9) |
| | MathChat | 43.0 (1.2) | 46.7 (0.9) | 64.4 (2.0) | 38.9 (1.3) |
| | TutorLLM | 50.0 (0.7) | 63.3 (0.7) | 75.5 (0.8) | 44.4 (1.5) |
| | PSS-MV | 48.1 (1.7) | 43.3 (1.2) | 75.8 (0.7) | 54.6 (1.1) |

## Key Findings

### 🏆 Top 3 Best Performers

1. **PSS-MV + Qwen3-4B-Instruct**: 60.8 average
   - Best on Algebra2005: 77.7 (1.0)
   - Best on Assist2017: 63.0 (1.9)

2. **Vanilla-ICL + Qwen3-4B-Instruct**: 59.6 average
   - Consistent across datasets
   - Strong on Algebra2005: 73.7 (0.9)

3. **TutorLLM + Llama3.1-8B-Instruct**: 58.3 average
   - Best on NIPS34: 63.3 (0.7)
   - Strong on Algebra2005: 75.5 (0.8)

### 📊 Method Performance (across all backbones)

1. **PSS-MV**: 55.6 average ⭐
2. **Vanilla-ICL**: 54.4 average
3. **TutorLLM**: 53.5 average
4. **MathChat**: 42.9 average

### 🎯 Backbone Performance

1. **Llama3.1-8B-Instruct**: 53.8 average
2. **Qwen3-4B-Instruct**: 51.8 average
3. **GPT-oss-120b**: 49.2 average

### 📈 Dataset Difficulty (by average learning gain)

1. **Algebra2005**: 65.4 (easiest)
2. **Bridge2006**: 47.6
3. **NIPS34**: 46.8
4. **Assist2017**: 48.4

---

*Generated on: October 22, 2025*  
*Metric: Learning Gain (Best of Two Runs)*  
*Format: mean (std)*

