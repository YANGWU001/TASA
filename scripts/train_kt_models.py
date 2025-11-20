#!/usr/bin/env python
"""Train knowledge tracing models (LPKT, DKT, AKT, SimpleKT) for forgetting score calculation."""

import argparse
import os
import sys
import subprocess

# Add pykt-toolkit to path if installed
PYKT_PATH = os.path.expanduser("~/pykt-toolkit")
if os.path.exists(PYKT_PATH):
    sys.path.insert(0, PYKT_PATH)

def train_model(dataset, model, epochs=200, batch_size=32, save_dir="../data/kt_models"):
    """Train a single KT model on a dataset."""
    
    print(f"\n{'='*60}")
    print(f"Training {model.upper()} on {dataset}")
    print(f"{'='*60}\n")
    
    # Ensure save directory exists
    os.makedirs(save_dir, exist_ok=True)
    model_save_path = os.path.join(save_dir, f"{dataset}_{model}")
    
    # Construct pykt training command
    data_path = f"../data/{dataset}"
    
    cmd = [
        "python", "-m", "pykt.train",
        "--model_name", model,
        "--dataset_name", dataset,
        "--data_dir", data_path,
        "--train_file", "train_valid_sequences.csv",
        "--test_file", "test_sequences.csv",
        "--emb_type", "qid",
        "--save_dir", model_save_path,
        "--learning_rate", "0.001",
        "--batch_size", str(batch_size),
        "--num_epochs", str(epochs),
        "--use_wandb", "0",
    ]
    
    # Model-specific parameters
    if model == "lpkt":
        cmd.extend([
            "--d_model", "128",
            "--d_ff", "256",
            "--dropout", "0.2",
            "--n_heads", "8",
            "--n_know", "50",
        ])
    elif model == "dkt":
        cmd.extend([
            "--hidden_size", "200",
            "--num_layers", "1",
            "--dropout", "0.2",
        ])
    elif model == "akt":
        cmd.extend([
            "--d_model", "256",
            "--n_heads", "8",
            "--dropout", "0.2",
        ])
    elif model == "simplekt":
        cmd.extend([
            "--d_model", "128",
            "--n_heads", "8",
            "--dropout", "0.2",
        ])
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ Successfully trained {model} on {dataset}")
        print(f"   Model saved to: {model_save_path}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed to train {model} on {dataset}")
        print(f"   Error: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Train Knowledge Tracing Models')
    parser.add_argument('--dataset', type=str, required=True,
                       choices=['assist2017', 'nips_task34', 'algebra2005', 'bridge2006'],
                       help='Dataset to train on')
    parser.add_argument('--model', type=str, default='all',
                       choices=['lpkt', 'dkt', 'akt', 'simplekt', 'all'],
                       help='KT model to train (default: all)')
    parser.add_argument('--epochs', type=int, default=200,
                       help='Number of training epochs (default: 200)')
    parser.add_argument('--batch-size', type=int, default=32,
                       help='Batch size (default: 32)')
    parser.add_argument('--save-dir', type=str, default='../data/kt_models',
                       help='Directory to save trained models')
    
    args = parser.parse_args()
    
    # Determine which models to train
    if args.model == 'all':
        models = ['lpkt', 'dkt', 'akt', 'simplekt']
    else:
        models = [args.model]
    
    print(f"\n🎯 Training KT models on {args.dataset}")
    print(f"   Models: {', '.join(models)}")
    print(f"   Epochs: {args.epochs}")
    print(f"   Batch size: {args.batch_size}\n")
    
    # Train each model
    results = {}
    for model in models:
        success = train_model(
            dataset=args.dataset,
            model=model,
            epochs=args.epochs,
            batch_size=args.batch_size,
            save_dir=args.save_dir
        )
        results[model] = success
    
    # Summary
    print(f"\n{'='*60}")
    print("Training Summary")
    print(f"{'='*60}")
    for model, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"  {model.upper():12s} : {status}")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()

