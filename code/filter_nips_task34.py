"""
筛选nips_task34数据集的学生
条件: 历史vs pre-test差距≤10%, pre-test在20%-60%
"""

import json
import os
import numpy as np

print("="*80)
print("📊 筛选nips_task34学生")
print("="*80)

# 1. 加载所有sessions
session_dir = "/mnt/localssd/bank/session/nips_task34"
sessions = []

for filename in os.listdir(session_dir):
    if filename.endswith('.json'):
        student_id = int(filename.replace('.json', ''))
        with open(os.path.join(session_dir, filename)) as f:
            session = json.load(f)
            session['student_id'] = student_id
            sessions.append(session)

print(f"✅ 加载了 {len(sessions)} 个session")

# 2. 对每个session，加载pre-test结果并筛选
qualified_students = []
total_with_pretest = 0
deviation_ok = 0

for session in sessions:
    student_id = session['student_id']
    concept_id = str(session['concept_id'])
    
    # 加载pre-test结果
    pretest_file = f"/mnt/localssd/bank/evaluation_results/pre-test/nips_task34/student_{student_id}_concept_{concept_id}.json"
    
    if os.path.exists(pretest_file):
        with open(pretest_file) as f:
            pretest_data = json.load(f)
        
        total_with_pretest += 1
        
        # 计算历史准确率
        original_accuracy = session['persona']['stats']['correct'] / session['persona']['stats']['total']
        pre_test_accuracy = pretest_data['roleplay_accuracy']
        
        # 筛选条件1: 历史vs pre-test差距≤10%
        deviation = abs(original_accuracy - pre_test_accuracy)
        
        if deviation <= 0.10:
            deviation_ok += 1
            # 筛选条件2: pre-test在20%-60%
            if 0.20 <= pre_test_accuracy <= 0.60:
                qualified_students.append({
                    'student_id': student_id,
                    'concept_id': concept_id,
                    'concept_text': session['concept_text'],
                    'original_accuracy': original_accuracy,
                    'pre_test_accuracy': pre_test_accuracy,
                    'deviation': deviation
                })

print(f"\n📈 筛选结果:")
print(f"   总学生数: {len(sessions)}")
print(f"   有Pre-test结果: {total_with_pretest}")
print(f"   差距≤10%: {deviation_ok}")
print(f"   最终符合条件 (差距≤10% 且 Pre-test 20-60%): {len(qualified_students)}个")

# 3. 保存筛选结果
output_file = '/mnt/localssd/qualified_students_nips_task34_20to60.json'

output_data = {
    'dataset': 'nips_task34',
    'total_students': len(sessions),
    'with_pretest': total_with_pretest,
    'filtered_count': len(qualified_students),
    'filter_criteria': {
        'deviation_threshold': '≤10%',
        'pretest_range': '20%-60%'
    },
    'students': qualified_students
}

with open(output_file, 'w') as f:
    json.dump(output_data, f, indent=2)

print(f"\n💾 筛选结果已保存: {output_file}")

# 统计信息
if qualified_students:
    orig_accs = [s['original_accuracy'] for s in qualified_students]
    pre_accs = [s['pre_test_accuracy'] for s in qualified_students]
    
    print(f"\n📊 统计信息:")
    print(f"   历史准确率: {np.mean(orig_accs)*100:.1f}% ± {np.std(orig_accs)*100:.1f}%")
    print(f"   Pre-test准确率: {np.mean(pre_accs)*100:.1f}% ± {np.std(pre_accs)*100:.1f}%")
    print(f"   平均偏差: {np.mean([s['deviation'] for s in qualified_students])*100:.1f}%")

print("\n" + "="*80)
print("✅ nips_task34筛选完成")
print("="*80)

