#!/usr/bin/env python3
"""
生成 overall.json - 整合所有方法的forgetting score
以 history.json 作为基准，包含所有模型的 s_tc 和 fs
"""

import os
import json
import argparse
from collections import defaultdict

def load_method_data(dataset, method):
    """加载某个方法的数据"""
    file_path = f'/mnt/localssd/bank/forgetting/{dataset}/{method}.json'
    
    if not os.path.exists(file_path):
        print(f"  ⚠️  {method}.json 不存在，跳过")
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
    print(f"📊 生成 Overall.json for {dataset.upper()}")
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
        print("❌ History.json 不存在，无法作为基准！")
        return
    
    print(f"\n✅ 成功加载 {len(method_data)} 个方法")
    print()
    
    # 2. 以history为基准，整合所有方法
    print("🔄 整合数据...")
    history_data = method_data['history']
    overall_data = {}
    
    total_students = len(history_data)
    total_concepts = 0
    missing_stats = defaultdict(int)
    
    for uid, concepts in history_data.items():
        overall_data[uid] = {}
        
        for concept_text, history_info in concepts.items():
            total_concepts += 1
            
            # 创建concept条目，包含所有方法的s_tc和fs
            concept_entry = {
                'methods': {}
            }
            
            # 添加所有方法的s_tc和fs
            for method in methods:
                if method not in method_data:
                    missing_stats[method] += 1
                    continue
                
                # 检查该学生的该concept在该方法中是否存在
                if uid in method_data[method] and concept_text in method_data[method][uid]:
                    method_info = method_data[method][uid][concept_text]
                    concept_entry['methods'][method] = {
                        's_tc': method_info.get('s_tc'),
                        'fs': method_info.get('fs')
                    }
                else:
                    missing_stats[method] += 1
            
            # 添加共同字段（来自history）
            concept_entry['delta_t'] = history_info.get('delta_t')
            concept_entry['tau'] = history_info.get('tau')
            concept_entry['last_response'] = history_info.get('last_response')
            concept_entry['num_attempts'] = history_info.get('num_attempts')
            concept_entry['level'] = history_info.get('level')  # 使用history的level
            
            overall_data[uid][concept_text] = concept_entry
    
    print(f"  ✅ 整合完成: {total_students} 学生, {total_concepts} concept条目")
    
    # 3. 统计缺失情况
    if missing_stats:
        print(f"\n📊 数据完整性统计:")
        for method in methods:
            if method in method_data:
                missing = missing_stats.get(method, 0)
                coverage = (total_concepts - missing) / total_concepts * 100
                print(f"  {method:10} - 覆盖率: {coverage:5.1f}% ({total_concepts - missing}/{total_concepts})")
    
    # 4. 保存
    print(f"\n💾 保存到Bank...")
    output_dir = f'/mnt/localssd/bank/forgetting/{dataset}'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'overall.json')
    
    with open(output_file, 'w') as f:
        json.dump(overall_data, f, indent=2)
    
    file_size = os.path.getsize(output_file) / 1024 / 1024
    print(f"  ✅ 已保存: {output_file}")
    print(f"  📊 文件大小: {file_size:.1f}MB")
    
    # 5. 示例数据
    print(f"\n📋 数据示例:")
    sample_uid = list(overall_data.keys())[0]
    sample_concept = list(overall_data[sample_uid].keys())[0]
    sample_data = overall_data[sample_uid][sample_concept]
    
    print(f"  学生ID: {sample_uid}")
    print(f"  Concept: {sample_concept}")
    print(f"  Methods:")
    for method, values in sample_data['methods'].items():
        print(f"    {method:10} - s_tc={values['s_tc']:.4f}, fs={values['fs']:.4f}")
    print(f"  共同字段:")
    print(f"    delta_t={sample_data['delta_t']}, tau={sample_data['tau']}")
    print(f"    last_response={sample_data['last_response']}, num_attempts={sample_data['num_attempts']}")
    print(f"    level={sample_data['level']}")

def main():
    parser = argparse.ArgumentParser(description='Generate overall.json with all methods')
    parser.add_argument('--dataset', type=str, required=True,
                       help='Dataset name')
    
    args = parser.parse_args()
    
    generate_overall(args.dataset)
    
    print("\n" + "="*100)
    print("✅ 完成！")
    print("="*100)

if __name__ == '__main__':
    main()

