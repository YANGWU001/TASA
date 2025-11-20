#!/usr/bin/env python
"""Evaluate and compare experimental results across methods and datasets."""

import argparse
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path

def load_results(results_dir, method, dataset):
    """Load results for a specific method and dataset."""
    result_path = Path(results_dir) / method / dataset / "overall.json"
    
    if not result_path.exists():
        print(f"⚠️  Results not found: {result_path}")
        return None
    
    with open(result_path, 'r') as f:
        data = json.load(f)
    
    return data

def calculate_learning_gain(pre_score, post_score):
    """Calculate normalized learning gain."""
    if post_score >= pre_score:
        return (post_score - pre_score) / (100 - pre_score) * 100
    else:
        return (post_score - pre_score) / pre_score * 100

def evaluate_method(results_dir, method, dataset):
    """Evaluate a single method on a dataset."""
    data = load_results(results_dir, method, dataset)
    
    if data is None:
        return None
    
    # Extract metrics
    students = data.get('students', [])
    if not students:
        return None
    
    learning_gains = []
    pre_scores = []
    post_scores = []
    
    for student in students:
        pre = student.get('pre_test_score', 0)
        post = student.get('post_test_score', 0)
        
        pre_scores.append(pre)
        post_scores.append(post)
        learning_gains.append(calculate_learning_gain(pre, post))
    
    return {
        'method': method,
        'dataset': dataset,
        'num_students': len(students),
        'mean_learning_gain': np.mean(learning_gains),
        'std_learning_gain': np.std(learning_gains),
        'mean_pre_score': np.mean(pre_scores),
        'mean_post_score': np.mean(post_scores),
    }

def main():
    parser = argparse.ArgumentParser(description='Evaluate Experimental Results')
    parser.add_argument('--method', type=str, default='all',
                       help='Method to evaluate (default: all)')
    parser.add_argument('--dataset', type=str, required=True,
                       help='Dataset to evaluate')
    parser.add_argument('--results-dir', type=str, default='../results',
                       help='Results directory (default: ../results)')
    parser.add_argument('--compare-all', action='store_true',
                       help='Compare all methods')
    
    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    
    # Determine which methods to evaluate
    if args.method == 'all' or args.compare_all:
        # Find all methods in results directory
        if results_dir.exists():
            methods = [d.name for d in results_dir.iterdir() if d.is_dir()]
        else:
            print(f"❌ Results directory not found: {results_dir}")
            return
    else:
        methods = [args.method]
    
    print(f"\n{'='*80}")
    print(f"Evaluating Results: {args.dataset}")
    print(f"{'='*80}\n")
    
    # Evaluate each method
    all_results = []
    for method in methods:
        print(f"📊 Evaluating {method}...")
        result = evaluate_method(results_dir, method, args.dataset)
        if result:
            all_results.append(result)
    
    if not all_results:
        print("\n❌ No results found to evaluate.")
        return
    
    # Create DataFrame for comparison
    df = pd.DataFrame(all_results)
    df = df.sort_values('mean_learning_gain', ascending=False)
    
    # Print results table
    print(f"\n{'='*80}")
    print("Results Summary")
    print(f"{'='*80}\n")
    
    print(f"{'Method':<20} {'Students':>10} {'Pre-Test':>10} {'Post-Test':>10} {'Learning Gain':>15}")
    print(f"{'-'*80}")
    
    for _, row in df.iterrows():
        print(f"{row['method']:<20} "
              f"{row['num_students']:>10} "
              f"{row['mean_pre_score']:>9.1f}% "
              f"{row['mean_post_score']:>9.1f}% "
              f"{row['mean_learning_gain']:>9.1f}±{row['std_learning_gain']:.1f}%")
    
    print(f"{'-'*80}\n")
    
    # Save results to CSV
    output_file = results_dir / f"{args.dataset}_evaluation.csv"
    df.to_csv(output_file, index=False)
    print(f"💾 Results saved to: {output_file}\n")
    
    # Highlight best method
    best_method = df.iloc[0]
    print(f"🏆 Best Method: {best_method['method']}")
    print(f"   Learning Gain: {best_method['mean_learning_gain']:.1f}±{best_method['std_learning_gain']:.1f}%")
    print(f"   Post-Test Score: {best_method['mean_post_score']:.1f}%\n")

if __name__ == '__main__':
    main()

