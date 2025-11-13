#!/bin/bash

# TASA Project Reorganization Script
# This script:
# 1. Creates a 'code' directory
# 2. Moves all files except README and config files to 'code'
# 3. Removes GPT-related files

set -e  # Exit on error

echo "Starting TASA project reorganization..."

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create code directory if it doesn't exist
if [ ! -d "code" ]; then
    echo "Creating 'code' directory..."
    mkdir -p code
fi

# Files to keep in root directory (case-insensitive patterns)
KEEP_FILES=(
    "README.md"
    "readme.md"
    "requirements.txt"
    "environment.yml"
    "setup.py"
    "setup.cfg"
    "pyproject.toml"
    "quick_setup.sh"
    ".gitignore"
    ".gitattributes"
    "LICENSE"
    "license"
    "MANIFEST.in"
    "Dockerfile"
    "docker-compose.yml"
    "Makefile"
    "reorganize_project.sh"
)

# Directories to keep in root
KEEP_DIRS=(
    ".git"
    ".github"
    "code"
    "bank"  # Assuming this is data directory
)

echo ""
echo "Step 1: Moving files to code/ directory..."
echo "=========================================="

# Function to check if item should be kept in root
should_keep() {
    local item="$1"
    local basename=$(basename "$item")
    
    # Check if it's a kept directory
    for dir in "${KEEP_DIRS[@]}"; do
        if [ "$basename" = "$dir" ]; then
            return 0
        fi
    done
    
    # Check if it's a kept file
    for file in "${KEEP_FILES[@]}"; do
        if [ "$basename" = "$file" ]; then
            return 0
        fi
    done
    
    return 1
}

# Move files and directories to code/
moved_count=0
for item in *; do
    if [ "$item" = "code" ]; then
        continue
    fi
    
    if ! should_keep "$item"; then
        echo "Moving: $item"
        mv "$item" code/
        ((moved_count++))
    else
        echo "Keeping in root: $item"
    fi
done

echo ""
echo "Moved $moved_count items to code/ directory"

echo ""
echo "Step 2: Removing GPT-related files..."
echo "=========================================="

# Files related to GPT to remove
GPT_FILES=(
    "tasa_config.py"
    "baseline_evaluation_with_backbone.py"
    "run_all_baselines_gpt.py"
    "llm_client.py"
)

removed_count=0
for file in "${GPT_FILES[@]}"; do
    if [ -f "code/$file" ]; then
        echo "Removing: code/$file"
        rm -f "code/$file"
        ((removed_count++))
    fi
done

# Remove GPT-related configuration sections from other files
echo ""
echo "Cleaning GPT references from configuration files..."

# Check if tasa_config_llama.py exists and clean it
if [ -f "code/tasa_config_llama.py" ]; then
    echo "Cleaning code/tasa_config_llama.py..."
    # Backup original
    cp "code/tasa_config_llama.py" "code/tasa_config_llama.py.backup"
    
    # Remove GPT endpoint and API key (commented out approach - safer)
    sed -i.tmp 's/^GPT_ENDPOINT/#GPT_ENDPOINT/g' "code/tasa_config_llama.py" 2>/dev/null || true
    sed -i.tmp 's/^OPENAI_API_KEY/#OPENAI_API_KEY/g' "code/tasa_config_llama.py" 2>/dev/null || true
    rm -f "code/tasa_config_llama.py.tmp"
fi

# Check if tasa_config_qwen.py exists and clean it
if [ -f "code/tasa_config_qwen.py" ]; then
    echo "Cleaning code/tasa_config_qwen.py..."
    cp "code/tasa_config_qwen.py" "code/tasa_config_qwen.py.backup"
    
    sed -i.tmp 's/^GPT_ENDPOINT/#GPT_ENDPOINT/g' "code/tasa_config_qwen.py" 2>/dev/null || true
    sed -i.tmp 's/^OPENAI_API_KEY/#OPENAI_API_KEY/g' "code/tasa_config_qwen.py" 2>/dev/null || true
    rm -f "code/tasa_config_qwen.py.tmp"
fi

echo ""
echo "Removed $removed_count GPT-related files"

echo ""
echo "Step 3: Creating structure summary..."
echo "=========================================="

# Create a directory structure summary
cat > STRUCTURE.md << 'EOF'
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
EOF

echo "Created STRUCTURE.md"

echo ""
echo "=========================================="
echo "Reorganization complete!"
echo "=========================================="
echo ""
echo "Summary:"
echo "- Created 'code/' directory with all implementation files"
echo "- Kept in root: README.md, requirements.txt, quick_setup.sh, bank/"
echo "- Removed $removed_count GPT-related files"
echo "- Created STRUCTURE.md with project layout"
echo ""
echo "Root directory now contains:"
ls -la | grep -v "^d" | awk '{print "  - " $9}' | grep -v "^\s*-\s*$"
echo ""
echo "To verify the structure, run: ls -la"
echo ""

