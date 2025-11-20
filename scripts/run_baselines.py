#!/usr/bin/env python
"""Main script to run baseline methods."""

import argparse
import sys
sys.path.insert(0, '../src')

from baselines.vanilla_icl import run_vanilla_icl
from baselines.mathchat import run_mathchat
from baselines.tutorllm import run_tutorllm
from baselines.pssmv import run_pssmv

BASELINE_MAP = {
    'vanilla-icl': run_vanilla_icl,
    'mathchat': run_mathchat,
    'tutorllm': run_tutorllm,
    'pssmv': run_pssmv,
}

def main():
    parser = argparse.ArgumentParser(description='Run Baseline Methods')
    parser.add_argument('--dataset', type=str, required=True)
    parser.add_argument('--backbone', type=str, default='llama')
    parser.add_argument('--method', type=str, default='all',
                       choices=list(BASELINE_MAP.keys()) + ['all'])
    parser.add_argument('--num-students', type=int, default=10)
    
    args = parser.parse_args()
    
    if args.method == 'all':
        methods = BASELINE_MAP.keys()
    else:
        methods = [args.method]
    
    for method in methods:
        print(f"🚀 Running {method} on {args.dataset}")
        BASELINE_MAP[method](args)

if __name__ == '__main__':
    main()
