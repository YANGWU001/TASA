#!/usr/bin/env python
"""Main script to run TASA tutoring experiments."""

import argparse
import sys
sys.path.insert(0, '../src')

from tasa.tutoring import run_tasa_tutoring

def main():
    parser = argparse.ArgumentParser(description='Run TASA Tutoring')
    parser.add_argument('--dataset', type=str, required=True,
                       choices=['assist2017', 'nips_task34', 'algebra2005', 'bridge2006'])
    parser.add_argument('--backbone', type=str, default='llama',
                       choices=['gpt', 'llama', 'qwen'])
    parser.add_argument('--forgetting-method', type=str, default='lpkt',
                       choices=['lpkt', 'dkt', 'akt', 'simplekt', 'history', 'simple_time'])
    parser.add_argument('--num-rounds', type=int, default=10)
    parser.add_argument('--num-students', type=int, default=10)
    
    args = parser.parse_args()
    
    print(f"🎓 Running TASA with {args.backbone} backbone on {args.dataset}")
    print(f"   Forgetting method: {args.forgetting-method}")
    print(f"   Tutoring rounds: {args.num_rounds}")
    
    run_tasa_tutoring(args)

if __name__ == '__main__':
    main()
