#!/usr/bin/env python3
"""
重新生成overall.json - 使用最优tau（中位数）
1. 使用delta_t的中位数作为tau
2. 重新计算所有方法的FS
3. 为每个方法独立计算level
"""

import os
import json
import numpy as np
from collections import defaultdict
import argparse

def load_method_data(dataset, method):
    """加载某个方法的数据"""
    file_path = f'/mnt/localssd/bank/forgetting/{dataset}/{method}.json'
    
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path) as f:
            data = json.load(f)
        print(f"  ✅ {method:10} - {len(data)} 学生")
        return data
    except Exception as e:
        print(f"  ❌ {method:10} - 加载失败: {e}")
        return None

def generate_overall(dataset):
    """生成overall.json"""
    print("="*100)
    print(f"📊 生成 Overall.json (优化tau) for {dataset.upper()}")
    print("="*100)
    print()
    
    # 1. 加载所有方法的数据
    print("📂 加载数据...")
    methods = ['history', 'lpkt', 'dkt', 'akt', 'simplekt']
    method_data = {}
    
    for method in methods:
        data = load_method_data(dataset, method)
        if data is not None:
            method_data[method] = data
    
    if 'history' not in method_data:
        print("❌ History.json 不存在！")
        return
    
    print(f"\n✅ 成功加载 {len(method_data)} 个方法\n")
    
    # 2. 计算最优tau（使用中位数）
    print("🔧 计算最优tau...")
    history_data = method_data['history']
    
    all_delta_t = []
    for uid, concepts in history_data.items():
        for concept_text, concept_data in concepts.items():
            delta_t = concept_data.get('delta_t')
            if delta_t is not None and delta_t > 0:
                all_delta_t.append(delta_t)
    
    optimal_tau = np.median(all_delta_t)
    print(f"  Delta_t统计:")
    print(f"    中位数: {optimal_tau:.2f} 分钟")
    print(f"    平均值: {np.mean(all_delta_t):.2f} 分钟")
    print(f"    Q25: {np.percentile(all_delta_t, 25):.2f}, Q75: {np.percentile(all_delta_t, 75):.2f}")
    print(f"  ✅ 使用最优tau = {optimal_tau:.2f} 分钟\n")
    
    # 3. 为每个方法重新计算FS并收集
    print("🔄 重新计算所有FS...")
    overall_data = {}
    method_fs_collection = {m: [] for m in methods}
    
    for uid, concepts in history_data.items():
        overall_data[uid] = {}
        
        for concept_text, history_info in concepts.items():
            delta_t = history_info.get('delta_t', 0)
            
            concept_entry = {
                'methods': {}
            }
            
            # 为每个方法重新计算FS
            for method in methods:
                if method not in method_data:
                    continue
                
                if uid in method_data[method] and concept_text in method_data[method][uid]:
                    method_info = method_data[method][uid][concept_text]
                    s_tc = method_info.get('s_tc', 0)
                    
                    # 使用新的tau重新计算FS
                    if delta_t > 0:
                        time_factor = delta_t / (delta_t + optimal_tau)
                        fs = (1 - s_tc) * time_factor
                    else:
                        fs = 0.0
                    
                    concept_entry['methods'][method] = {
                        's_tc': float(s_tc),
                        'fs': float(fs),
                        'level': 'medium'  # 先占位
                    }
                    
                    method_fs_collection[method].append((uid, concept_text, fs))
            
            # 共同字段
            concept_entry['delta_t'] = float(delta_t)
            concept_entry['tau'] = float(optimal_tau)
            concept_entry['last_response'] = int(history_info.get('last_response', 0))
            concept_entry['num_attempts'] = int(history_info.get('num_attempts', 0))
            
            overall_data[uid][concept_text] = concept_entry
    
    print(f"  ✅ 重新计算完成\n")
    
    # 4. 为每个方法独立计算level
    print("📈 为每个方法独立计算Level...")
    
    for method in methods:
        if method not in method_data or len(method_fs_collection[method]) == 0:
            continue
        
        # 提取所有FS值
        fs_values = [fs for _, _, fs in method_fs_collection[method]]
        
        # 计算三分位数
        q33 = np.percentile(fs_values, 33)
        q67 = np.percentile(fs_values, 67)
        
        print(f"  {method:10} - FS: min={np.min(fs_values):.4f}, Q33={q33:.4f}, median={np.median(fs_values):.4f}, Q67={q67:.4f}, max={np.max(fs_values):.4f}")
        
        # 分配level
        for uid, concept_text, fs in method_fs_collection[method]:
            if fs < q33:
                level = 'low'
            elif fs < q67:
                level = 'medium'
            else:
                level = 'high'
            
            overall_data[uid][concept_text]['methods'][method]['level'] = level
    
    print()
    
    # 5. 统计
    total_students = len(overall_data)
    total_concepts = sum(len(concepts) for concepts in overall_data.values())
    
    print(f"📊 数据统计:")
    print(f"  学生数: {total_students}")
    print(f"  Concept条目: {total_concepts}")
    
    for method in methods:
        count = sum(1 for uid in overall_data for ct in overall_data[uid] if method in overall_data[uid][ct]['methods'])
        coverage = count / total_concepts * 100 if total_concepts > 0 else 0
        print(f"  {method:10} - 覆盖率: {coverage:5.1f}% ({count}/{total_concepts})")
    
    # 6. 保存
    print(f"\n💾 保存到Bank...")
    output_dir = f'/mnt/localssd/bank/forgetting/{dataset}'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'overall.json')
    
    with open(output_file, 'w') as f:
        json.dump(overall_data, f, indent=2)
    
    file_size = os.path.getsize(output_file) / 1024 / 1024
    print(f"  ✅ 已保存: {output_file}")
    print(f"  📊 文件大小: {file_size:.1f}MB")
    
    # 7. 示例数据
    print(f"\n📋 数据示例:")
    sample_uid = list(overall_data.keys())[0]
    sample_concept = list(overall_data[sample_uid].keys())[0]
    sample_data = overall_data[sample_uid][sample_concept]
    
    print(f"  学生ID: {sample_uid}")
    print(f"  Concept: {sample_concept}")
    print(f"  新tau: {sample_data['tau']:.2f} 分钟, delta_t: {sample_data['delta_t']:.2f} 分钟")
    print(f"  Methods:")
    for method, values in sample_data['methods'].items():
        print(f"    {method:10} - s_tc={values['s_tc']:.4f}, fs={values['fs']:.4f}, level={values['level']}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=str, required=True)
    
    args = parser.parse_args()
    
    generate_overall(args.dataset)
    
    print("\n" + "="*100)
    print("✅ 完成！")
    print("="*100)

if __name__ == '__main__':
    main()
