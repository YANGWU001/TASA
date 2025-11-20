#!/usr/bin/env python
"""Preprocess raw dataset into pykt-toolkit format."""

import argparse
import os
import sys
import subprocess

def preprocess_dataset(dataset, data_dir="../data", min_seq_len=3, max_seq_len=200):
    """Preprocess a dataset using pykt-toolkit."""
    
    print(f"\n{'='*60}")
    print(f"Preprocessing {dataset}")
    print(f"{'='*60}\n")
    
    dataset_path = os.path.join(data_dir, dataset)
    os.makedirs(dataset_path, exist_ok=True)
    
    # Construct pykt preprocessing command
    cmd = [
        "python", "-m", "pykt.preprocess",
        "--dataset_name", dataset,
        "--data_dir", dataset_path,
        "--min_seq_len", str(min_seq_len),
        "--max_seq_len", str(max_seq_len),
        "--kfold", "5",
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ Successfully preprocessed {dataset}")
        print(f"   Data saved to: {dataset_path}")
        
        # List generated files
        print(f"\n📁 Generated files:")
        for file in os.listdir(dataset_path):
            if file.endswith('.csv') or file.endswith('.json'):
                file_path = os.path.join(dataset_path, file)
                size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                print(f"   - {file:40s} ({size:6.2f} MB)")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed to preprocess {dataset}")
        print(f"   Error: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Preprocess Datasets')
    parser.add_argument('--dataset', type=str, required=True,
                       choices=['assist2017', 'nips_task34', 'algebra2005', 'bridge2006', 'all'],
                       help='Dataset to preprocess')
    parser.add_argument('--data-dir', type=str, default='../data',
                       help='Root directory for data (default: ../data)')
    parser.add_argument('--min-seq-len', type=int, default=3,
                       help='Minimum sequence length (default: 3)')
    parser.add_argument('--max-seq-len', type=int, default=200,
                       help='Maximum sequence length (default: 200)')
    
    args = parser.parse_args()
    
    # Determine which datasets to process
    if args.dataset == 'all':
        datasets = ['assist2017', 'nips_task34', 'algebra2005', 'bridge2006']
    else:
        datasets = [args.dataset]
    
    print(f"\n🎯 Preprocessing datasets")
    print(f"   Datasets: {', '.join(datasets)}")
    print(f"   Data directory: {args.data_dir}")
    print(f"   Sequence length: [{args.min_seq_len}, {args.max_seq_len}]\n")
    
    # Preprocess each dataset
    results = {}
    for dataset in datasets:
        success = preprocess_dataset(
            dataset=dataset,
            data_dir=args.data_dir,
            min_seq_len=args.min_seq_len,
            max_seq_len=args.max_seq_len
        )
        results[dataset] = success
    
    # Summary
    print(f"\n{'='*60}")
    print("Preprocessing Summary")
    print(f"{'='*60}")
    for dataset, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"  {dataset:15s} : {status}")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()

