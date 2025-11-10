#!/usr/bin/env python3
"""
Baseline评估脚本 - 支持不同Backbone
基于baseline_evaluation_conservative.py，添加backbone支持
"""

import argparse
import os
import sys
import time
import json
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# 导入baseline方法
from baseline_vanilla_icl import VanillaICLTutor
from baseline_mathchat import MathChatTutor
from baseline_tutorllm import TutorLLMTutor
from baseline_pssmv import PSSMVTutor
from student_roleplay_evaluation import build_student_system_prompt, load_session, grade_answers

# 全局锁
print_lock = Lock()

def safe_print(*args, **kwargs):
    """线程安全的打印"""
    with print_lock:
        print(*args, **kwargs)

def get_method_name(method, backbone):
    """根据method和backbone生成method名称"""
    if backbone == "gpt-oss-120b":
        return f"{method}-conservative"
    elif "llama" in backbone.lower():
        return f"{method}-llama-conservative"
    elif "qwen" in backbone.lower():
        return f"{method}-qwen-conservative"
    else:
        return f"{method}-{backbone}-conservative"

# 其余代码逻辑与baseline_evaluation_conservative.py相同
# 这里只需要修改保存路径

def main():
    parser = argparse.ArgumentParser(description='Baseline评估 - 支持不同Backbone')
    parser.add_argument('--method', type=str, required=True, 
                       choices=['Vanilla-ICL', 'MathChat', 'TutorLLM', 'PSS-MV'])
    parser.add_argument('--dataset', type=str, required=True)
    parser.add_argument('--backbone', type=str, default='gpt-oss-120b',
                       help='Backbone模型 (gpt-oss-120b, llama-3.1-8b, qwen3-4b)')
    parser.add_argument('--max-workers', type=int, default=10)
    
    args = parser.parse_args()
    
    method_name = get_method_name(args.method, args.backbone)
    
    safe_print("="*80)
    safe_print(f"🚀 {args.method} Baseline评估")
    safe_print("="*80)
    safe_print(f"   Dataset: {args.dataset}")
    safe_print(f"   Backbone: {args.backbone}")
    safe_print(f"   Method: {method_name}")
    safe_print(f"   Max Workers: {args.max_workers}")
    safe_print("="*80)
    
    # TODO: 实现完整的评估逻辑
    # 这里需要从baseline_evaluation_conservative.py复制完整代码
    # 并修改保存路径使用method_name

if __name__ == '__main__':
    main()

