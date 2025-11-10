#!/usr/bin/env python3
"""
从现有的 Vanilla-ICL-llama dialogue 创建 Vanilla-ICL-turns28-llama 结构
参考 TutorLLM-turns28-llama 的格式
"""

import json
import os
import shutil

def create_turns_structure():
    dataset = 'assist2017'
    
    # 源目录
    source_dir = f'/mnt/localssd/bank/dialogue/Vanilla-ICL-llama/{dataset}'
    
    # 目标目录 - 参考 TutorLLM-turns28-llama 的结构
    target_base = f'/mnt/localssd/bank/dialogue/Vanilla-ICL-turns28-llama/{dataset}'
    
    # 创建dkt子目录（与TutorLLM-turns28-llama保持一致）
    target_dir = f'{target_base}/dkt'
    os.makedirs(target_dir, exist_ok=True)
    
    print('='*80)
    print('📝 创建 Vanilla-ICL-turns28-llama 结构')
    print('='*80)
    print(f'源目录: {source_dir}')
    print(f'目标目录: {target_dir}')
    print('='*80)
    print()
    
    source_files = [f for f in os.listdir(source_dir) if f.endswith('.json')]
    
    for fname in source_files:
        source_file = os.path.join(source_dir, fname)
        
        # 读取源文件
        with open(source_file, 'r') as f:
            data = json.load(f)
        
        # 提取dialogue部分（只保存list格式，与TutorLLM-turns28-llama一致）
        dialogue_list = data.get('dialogue', [])
        
        # 保存为新格式
        target_file = os.path.join(target_dir, fname)
        with open(target_file, 'w') as f:
            json.dump(dialogue_list, f, indent=2)
        
        student_id = data.get('student_id')
        print(f'✅ 学生{student_id:4d} | {len(dialogue_list)} turns | {fname}')
    
    print()
    print('='*80)
    print(f'✅ 完成！共处理 {len(source_files)} 个文件')
    print(f'📁 目标目录: {target_dir}')
    print('='*80)
    
    # 验证格式
    print()
    print('验证格式：')
    sample_file = os.path.join(target_dir, source_files[0])
    with open(sample_file, 'r') as f:
        sample_data = json.load(f)
    print(f'  类型: {type(sample_data)}')
    print(f'  长度: {len(sample_data)}')
    print(f'  第1个元素keys: {list(sample_data[0].keys())}')
    print(f'  ✅ 格式正确（与TutorLLM-turns28-llama一致）')

if __name__ == '__main__':
    create_turns_structure()

