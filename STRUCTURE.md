# TASA Project Structure

## Root Directory

```
TASA/
├── README.md              # Main project documentation
├── requirements.txt       # Python dependencies
├── quick_setup.sh        # Quick installation script
├── STRUCTURE.md          # This file
├── bank/                 # Student bank data (preserved)
└── code/                 # All implementation code
    ├── baseline_*.py     # Baseline methods
    ├── tasa_*.py        # TASA methods
    ├── train_*.py       # KT model training
    ├── generate_*.py    # Data generation scripts
    ├── analyze_*.py     # Analysis scripts
    ├── evaluate_*.py    # Evaluation scripts
    └── ...
```

## Key Directories

- **code/**: All Python implementation files, shell scripts, and logs
- **bank/**: Student bank data including persona, memory, sessions, and embeddings
  - `bank/persona/[dataset]/` - Student persona files
  - `bank/memory/[dataset]/` - Student memory files
  - `bank/session/[dataset]/` - Learning sessions
  - `bank/evaluation_results/` - Evaluation outputs

## Removed Components

The following GPT-related files have been removed:
- `tasa_config.py` (GPT-only configuration)
- `llm_client.py` (GPT client)
- GPT-specific baseline runners

## Configuration Files

- **Llama**: `code/tasa_config_llama.py`
- **Qwen**: `code/tasa_config_qwen.py`
- **Unified Client**: `code/llm_client_unified.py`

Note: GPT endpoints and API keys have been commented out in configuration files.
