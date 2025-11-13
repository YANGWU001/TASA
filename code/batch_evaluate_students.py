#!/usr/bin/env python3
"""
批量评估学生Role-Play系统
"""

import json
import argparse
from pathlib import Path
from student_roleplay_evaluation import (
    load_concept_questions, 
    evaluate_session, 
    client
)
from tqdm import tqdm
import pandas as pd

def batch_evaluate_dataset(dataset_name: str, num_students: int = None, sample_mode: str = 'first'):
    """
    批量评估整个数据集
    
    Args:
        dataset_name: 数据集名称 (assist2017, algebra2005, etc.)
        num_students: 要评估的学生数量（None = 全部）
        sample_mode: 'first', 'random', 'range'
    """
    print(f"\n{'='*80}")
    print(f"批量评估数据集: {dataset_name}")
    print(f"{'='*80}\n")
    
    # 路径设置
    session_dir = Path(f'/mnt/localssd/bank/session/{dataset_name}')
    concept_questions_file = f'/mnt/localssd/bank/test_data/{dataset_name}/concept_questions.json'
    output_dir = f'/mnt/localssd/bank/evaluation_results/{dataset_name}'
    
    # 加载题库
    print(f"📖 加载题库: {concept_questions_file}")
    try:
        concept_questions = load_concept_questions(concept_questions_file)
        print(f"   ✅ 加载了 {len(concept_questions)} 个concepts")
    except FileNotFoundError:
        print(f"   ❌ 题库文件不存在: {concept_questions_file}")
        return
    
    # 获取所有session文件
    session_files = sorted(list(session_dir.glob('*.json')))
    print(f"\n📂 找到 {len(session_files)} 个session文件")
    
    if not session_files:
        print("   ❌ 没有找到session文件")
        return
    
    # 采样
    if num_students:
        if sample_mode == 'first':
            session_files = session_files[:num_students]
        elif sample_mode == 'random':
            import random
            session_files = random.sample(session_files, min(num_students, len(session_files)))
        print(f"   🎯 选择了 {len(session_files)} 个session进行评估")
    
    # 批量评估
    results = []
    failed = []
    
    print(f"\n🚀 开始批量评估...\n")
    
    for session_file in tqdm(session_files, desc="评估进度", ncols=100):
        try:
            result = evaluate_session(str(session_file), concept_questions, output_dir)
            if result:
                results.append(result)
            else:
                failed.append(session_file.name)
        except Exception as e:
            print(f"\n❌ 评估失败 {session_file.name}: {e}")
            failed.append(session_file.name)
            continue
    
    # 生成统计报告
    generate_summary_report(results, dataset_name, output_dir, failed)

def generate_summary_report(results: list, dataset_name: str, output_dir: str, failed: list):
    """生成汇总报告"""
    print(f"\n{'='*80}")
    print(f"评估汇总报告")
    print(f"{'='*80}\n")
    
    if not results:
        print("❌ 没有成功的评估结果")
        return
    
    # 转换为DataFrame
    df_data = []
    for r in results:
        df_data.append({
            'student_id': r['student_id'],
            'concept_id': r['concept_id'],
            'concept_text': r['concept_text'],
            'original_accuracy': r['original_accuracy'],
            'roleplay_score': r['roleplay_score'],
            'roleplay_accuracy': r['roleplay_score'] / 10,
            'delta_t_minutes': r['session_info']['delta_t_minutes'],
            'num_attempts': r['session_info']['num_attempts']
        })
    
    df = pd.DataFrame(df_data)
    
    # 统计信息
    print(f"📊 评估统计:")
    print(f"   总评估数: {len(results)}")
    print(f"   成功: {len(results)}")
    print(f"   失败: {len(failed)}")
    print()
    
    print(f"📈 准确率分析:")
    print(f"   原始平均准确率: {df['original_accuracy'].mean()*100:.2f}%")
    print(f"   Role-play平均准确率: {df['roleplay_accuracy'].mean()*100:.2f}%")
    print(f"   准确率相关性: {df['original_accuracy'].corr(df['roleplay_accuracy']):.3f}")
    print()
    
    # 按原始准确率分组
    print(f"📊 按原始准确率分组的Role-play表现:")
    df['accuracy_group'] = pd.cut(df['original_accuracy'], 
                                   bins=[0, 0.3, 0.6, 1.0], 
                                   labels=['Low (<30%)', 'Medium (30-60%)', 'High (>60%)'])
    
    for group in ['Low (<30%)', 'Medium (30-60%)', 'High (>60%)']:
        group_df = df[df['accuracy_group'] == group]
        if len(group_df) > 0:
            print(f"   {group}: {len(group_df)} students")
            print(f"      原始: {group_df['original_accuracy'].mean()*100:.1f}%")
            print(f"      Role-play: {group_df['roleplay_accuracy'].mean()*100:.1f}%")
    
    # 保存汇总结果
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 保存DataFrame
    csv_file = output_path / 'summary_report.csv'
    df.to_csv(csv_file, index=False)
    print(f"\n💾 详细报告已保存至: {csv_file}")
    
    # 保存完整结果JSON
    json_file = output_path / 'all_results.json'
    with open(json_file, 'w') as f:
        json.dump({
            'dataset': dataset_name,
            'total_evaluated': len(results),
            'failed': failed,
            'results': results,
            'statistics': {
                'original_accuracy_mean': float(df['original_accuracy'].mean()),
                'roleplay_accuracy_mean': float(df['roleplay_accuracy'].mean()),
                'correlation': float(df['original_accuracy'].corr(df['roleplay_accuracy']))
            }
        }, f, indent=2, ensure_ascii=False)
    print(f"💾 完整结果已保存至: {json_file}")
    
    # 失败列表
    if failed:
        print(f"\n⚠️  失败的评估 ({len(failed)}):")
        for f in failed[:10]:  # 只显示前10个
            print(f"   - {f}")
        if len(failed) > 10:
            print(f"   ... 还有 {len(failed)-10} 个")

def main():
    parser = argparse.ArgumentParser(description='批量评估学生Role-Play系统')
    parser.add_argument('--dataset', type=str, required=True, 
                       help='数据集名称 (assist2017, algebra2005, etc.)')
    parser.add_argument('--num', type=int, default=None,
                       help='要评估的学生数量（默认全部）')
    parser.add_argument('--sample', type=str, default='first',
                       choices=['first', 'random'],
                       help='采样模式')
    
    args = parser.parse_args()
    
    batch_evaluate_dataset(args.dataset, args.num, args.sample)

if __name__ == '__main__':
    main()

