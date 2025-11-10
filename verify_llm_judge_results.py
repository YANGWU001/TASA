#!/usr/bin/env python3
"""
验证已完成的LLM judge结果
检查win rates、baseline匹配、common students等
"""

import json
import os
from collections import defaultdict

def verify_results():
    result_dir = '/mnt/localssd/llm_judge_results'
    
    # 按method和dataset分组
    results_by_method = defaultdict(lambda: defaultdict(dict))
    
    all_files = [f for f in os.listdir(result_dir) if f.endswith('.json')]
    
    print('='*100)
    print('🔍 验证LLM Judge结果')
    print('='*100)
    print(f'总文件数: {len(all_files)}\n')
    
    issues = []
    
    for fname in sorted(all_files):
        fpath = os.path.join(result_dir, fname)
        
        try:
            with open(fpath) as f:
                data = json.load(f)
            
            target_method = data.get('target_method', 'unknown')
            baseline_method = data.get('baseline_method', 'unknown')
            dataset = data.get('dataset', 'unknown')
            win_rate = data.get('win_rate', 0)
            tie_rate = data.get('tie_rate', 0)
            
            # 处理两种格式
            if 'results' in data:
                # 新格式
                common_students = data.get('common_students', 0)
                total_comparisons = data.get('results', {}).get('A_wins', 0) + data.get('results', {}).get('B_wins', 0) + data.get('results', {}).get('ties', 0)
            else:
                # 旧格式
                common_students = len(data.get('detailed_results', []))
                total_comparisons = data.get('total_comparisons', 0)
                win_rate = win_rate * 100 if win_rate < 1.5 else win_rate  # 转换为百分比
                tie_rate = tie_rate * 100 if 'ties' in data else 0
            
            # 检查1: Win rate过高
            if win_rate > 90:
                issues.append(f"⚠️  {fname}: Win rate过高 ({win_rate:.1f}%)")
            
            # 检查2: Baseline匹配
            if 'llama' in target_method.lower() and 'llama' not in baseline_method.lower():
                issues.append(f"⚠️  {fname}: Backbone不匹配 ({target_method} vs {baseline_method})")
            if 'qwen' in target_method.lower() and 'qwen' not in baseline_method.lower():
                issues.append(f"⚠️  {fname}: Backbone不匹配 ({target_method} vs {baseline_method})")
            if 'gpt' in target_method.lower() and target_method != 'TASA' and 'gpt' not in baseline_method.lower() and baseline_method != 'Vanilla-ICL':
                issues.append(f"⚠️  {fname}: Backbone不匹配 ({target_method} vs {baseline_method})")
            
            # 检查3: Common students数量
            if common_students == 0:
                issues.append(f"⚠️  {fname}: Common students为0")
            
            # 检查4: Total comparisons与common students的关系
            if total_comparisons < common_students:
                issues.append(f"⚠️  {fname}: Total comparisons({total_comparisons}) < common students({common_students})")
            
            # 存储结果
            results_by_method[target_method][dataset] = {
                'win_rate': win_rate,
                'tie_rate': tie_rate,
                'common_students': common_students,
                'total_comparisons': total_comparisons,
                'baseline': baseline_method
            }
            
        except Exception as e:
            issues.append(f"❌ {fname}: 读取失败 - {e}")
    
    # 打印结果表格
    print('\n' + '='*100)
    print('📊 Win Rate汇总（按Method分组）')
    print('='*100)
    print()
    
    for method in sorted(results_by_method.keys()):
        datasets_data = results_by_method[method]
        print(f"\n【{method}】")
        print(f"{'Dataset':<15} | {'Baseline':<25} | {'Win%':>6} | {'Tie%':>6} | {'Students':>8} | {'Comparisons':>12}")
        print(f"{'-'*15}-+-{'-'*25}-+-{'-'*6}-+-{'-'*6}-+-{'-'*8}-+-{'-'*12}")
        
        for dataset in sorted(datasets_data.keys()):
            d = datasets_data[dataset]
            print(f"{dataset:<15} | {d['baseline']:<25} | {d['win_rate']:>5.1f}% | {d['tie_rate']:>5.1f}% | {d['common_students']:>8} | {d['total_comparisons']:>12}")
    
    # 打印问题
    print('\n' + '='*100)
    print('🚨 发现的问题')
    print('='*100)
    if issues:
        for issue in issues:
            print(issue)
    else:
        print('✅ 没有发现问题！')
    print('='*100)
    
    # 按backbone分组的统计
    print('\n' + '='*100)
    print('📊 按Backbone分组的Win Rate统计')
    print('='*100)
    
    backbone_stats = defaultdict(lambda: {'methods': [], 'win_rates': []})
    
    for method, datasets_data in results_by_method.items():
        # 确定backbone
        if 'llama' in method.lower():
            backbone = 'Llama'
        elif 'qwen' in method.lower():
            backbone = 'Qwen'
        elif 'gpt' in method.lower() or method == 'TASA':
            backbone = 'GPT-OSS-120b'
        else:
            backbone = 'Unknown'
        
        # 计算平均win rate
        win_rates = [d['win_rate'] for d in datasets_data.values()]
        if win_rates:
            avg_win_rate = sum(win_rates) / len(win_rates)
            backbone_stats[backbone]['methods'].append(method)
            backbone_stats[backbone]['win_rates'].append(avg_win_rate)
    
    for backbone in sorted(backbone_stats.keys()):
        print(f"\n【{backbone}】")
        methods = backbone_stats[backbone]['methods']
        win_rates = backbone_stats[backbone]['win_rates']
        
        for method, win_rate in zip(methods, win_rates):
            print(f"  {method:<30s}: {win_rate:>5.1f}%")

if __name__ == '__main__':
    verify_results()

