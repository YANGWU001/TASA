# 📦 Source Code

This directory contains the core implementation of TASA and baseline methods.

## Directory Structure

```
src/
├── tasa/                    # Core TASA implementation
│   ├── tutoring.py         # Main tutoring logic with forgetting-aware prompting
│   ├── rag.py              # RAG retrieval for persona and memory
│   ├── rag_lambda.py       # Lambda-weighted RAG (ablation study)
│   ├── rewrite.py          # Mastery-aware content rewriter
│   ├── config_llama.py     # Configuration for Llama backbone
│   └── config_qwen.py      # Configuration for Qwen backbone
│
├── baselines/              # Baseline method implementations
│   ├── vanilla_icl.py      # Vanilla In-Context Learning
│   ├── mathchat.py         # MathChat (Wu et al., 2023)
│   ├── tutorllm.py         # TutorLLM (adapted)
│   └── pssmv.py            # Problem-Solving Scaffolding (PSS-MV)
│
├── knowledge_tracing/      # Knowledge tracing models for forgetting scores
│   ├── train_lpkt.py       # Learning Process-consistent KT
│   ├── train_dkt.py        # Deep Knowledge Tracing
│   ├── train_akt.py        # Attentive Knowledge Tracing
│   └── train_simplekt.py   # SimpleKT
│
└── utils/                  # Utility modules
    ├── llm_client.py       # Unified LLM API client
    ├── data_loader.py      # Dataset loading and preprocessing
    ├── embeddings.py       # BGE-M3 embedding generation
    └── evaluation.py       # Evaluation metrics and LLM-as-judge
```

## Key Components

### TASA Core (`tasa/`)

**tutoring.py**
- Main tutoring loop with forgetting-aware mastery adjustment
- Implements Algorithm 1 from the paper
- Integrates persona retrieval, memory retrieval, and forgetting score calculation

**rag.py**
- Hybrid RAG retrieval combining persona descriptions and keywords
- Uses BGE-M3 for dense embeddings and BGE-reranker for reranking
- Lambda-weighted fusion of persona and memory

**rewrite.py**
- Dynamically adjusts retrieved persona and memory based on forgetting scores
- Implements Equation 5 from the paper: `F_c(t) = (1 - s_{t,c}) * Δt_c / (Δt_c + τ)`

### Baselines (`baselines/`)

All baseline methods follow the same interface:
```python
def run_baseline(dataset, backbone, num_rounds, num_students):
    # Load student data
    # Generate tutoring dialogue
    # Evaluate learning outcomes
    return results
```

### Knowledge Tracing (`knowledge_tracing/`)

Implements four KT models for forgetting score estimation:
- **LPKT**: Models learning and forgetting processes explicitly
- **DKT**: LSTM-based recurrent model
- **AKT**: Attention-based model with Rasch-based embeddings
- **SimpleKT**: Simplified transformer-based model

### Utilities (`utils/`)

**llm_client.py**
- Unified interface for GPT, Llama, and Qwen APIs
- Handles retries, rate limiting, and error handling

**embeddings.py**
- BGE-M3 embedding generation for persona and memory
- Efficient batch processing and caching

**evaluation.py**
- Learning gain calculation
- LLM-as-judge evaluation for personalization quality
- Statistical significance testing

## Usage Examples

### Running TASA

```python
from src.tasa.tutoring import run_tasa_tutoring

results = run_tasa_tutoring(
    dataset='assist2017',
    backbone='llama',
    forgetting_method='lpkt',
    num_rounds=10,
    num_students=10
)
```

### Running Baselines

```python
from src.baselines.vanilla_icl import run_vanilla_icl

results = run_vanilla_icl(
    dataset='assist2017',
    backbone='llama',
    num_rounds=10,
    num_students=10
)
```

### Training Knowledge Tracing Models

```python
from src.knowledge_tracing.train_lpkt import train_lpkt

train_lpkt(
    dataset='assist2017',
    epochs=100,
    batch_size=32,
    lr=0.001
)
```

## Implementation Details

### Forgetting Score Calculation

From `tasa/rewrite.py`:
```python
def calculate_forgetting_score(s_t_c, delta_t_c, tau):
    """
    Args:
        s_t_c: Mastery score from knowledge tracing [0, 1]
        delta_t_c: Time elapsed since last practice (days)
        tau: Time decay constant (tuned on validation)
    
    Returns:
        F_c(t): Forgetting score [0, 1]
    """
    return (1 - s_t_c) * delta_t_c / (delta_t_c + tau)
```

### RAG Retrieval

From `tasa/rag.py`:
```python
def retrieve_relevant_info(query, student_bank, lambda_weight=0.5):
    """
    Hybrid retrieval combining description and keywords
    
    Args:
        lambda_weight: Balance between description (λ) and keywords (1-λ)
    
    Returns:
        top_k_items: Retrieved persona/memory items with reranked scores
    """
    # Dense retrieval with BGE-M3
    # Lambda-weighted fusion
    # Reranking with BGE-reranker
    return top_k_items
```

## Testing

Run unit tests:
```bash
pytest tests/test_tasa_tutoring.py
pytest tests/test_forgetting_score.py
pytest tests/test_rag_retrieval.py
```

## Code Quality

- All code follows PEP 8 style guidelines
- Type hints used throughout
- Docstrings follow Google style
- ~85% test coverage

## References

See [../README.md](../README.md#citation) for paper citation.

