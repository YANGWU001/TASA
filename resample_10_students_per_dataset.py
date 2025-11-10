#!/opt/venv/bin/python3
"""
从每个数据集的现有qualified学生中随机抽取10个
用于后续所有实验
"""

import json
import random

# 设置随机种子以便复现
random.seed(42)

datasets = {
    'assist2017': '/mnt/localssd/qualified_students_assist2017_sampled40.json',
    'algebra2005': '/mnt/localssd/qualified_students_algebra2005_sampled40.json',
    'bridge2006': '/mnt/localssd/qualified_students_bridge2006_sampled40.json',
    'nips_task34': '/mnt/localssd/qualified_students_nips_task34_sampled40.json'
}

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("📊 重新采样：每个数据集随机选择10个学生")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

summary = {}

for dataset_name, file_path in datasets.items():
    print(f"📁 处理数据集: {dataset_name}")
    
    # 读取现有的qualified学生
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # 提取学生ID列表
    if 'sampled_students' in data:
        all_students = data['sampled_students']
    elif 'students' in data:
        if isinstance(data['students'][0], dict):
            all_students = [s['student_id'] for s in data['students']]
        else:
            all_students = data['students']
    else:
        print(f"   ❌ 无法读取学生数据")
        continue
    
    print(f"   • 现有学生数: {len(all_students)}")
    
    # 随机选择10个（如果不足10个则全选）
    sample_size = min(10, len(all_students))
    sampled_students = random.sample(all_students, sample_size)
    sampled_students.sort()  # 排序以便查看
    
    print(f"   • 采样学生数: {sample_size}")
    print(f"   • 学生IDs: {sampled_students}")
    
    # 保存到新文件
    output_file = f'/mnt/localssd/qualified_students_{dataset_name}_sampled10.json'
    output_data = {
        'dataset': dataset_name,
        'total_qualified': len(all_students),
        'sample_size': sample_size,
        'sampling_seed': 42,
        'sampled_students': sampled_students
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"   ✅ 已保存到: {output_file}\n")
    
    summary[dataset_name] = {
        'total': len(all_students),
        'sampled': sample_size,
        'reduction': f"{(1 - sample_size/len(all_students))*100:.1f}%"
    }

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("📈 采样汇总")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

for dataset_name, stats in summary.items():
    print(f"  {dataset_name:15s}: {stats['total']:3d} → {stats['sampled']:2d} 人 (减少 {stats['reduction']})")

total_before = sum(s['total'] for s in summary.values())
total_after = sum(s['sampled'] for s in summary.values())
print(f"\n  {'总计':15s}: {total_before:3d} → {total_after:2d} 人 (减少 {(1-total_after/total_before)*100:.1f}%)")
print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("✅ 所有数据集采样完成！")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

