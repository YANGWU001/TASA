#!/usr/bin/env python
"""
重新生成Memory - 全量版本
不使用LLM，直接用模板+随机化生成
处理所有历史记录，不限制数量
"""

import os
import json
import numpy as np
import pandas as pd
from collections import defaultdict
from tqdm import tqdm
import argparse
import random

# BGE模型
try:
    from FlagEmbedding import BGEM3FlagModel
except ImportError:
    from FlagEmbedding import FlagModel as BGEM3FlagModel

# 数据集配置
DATASET_MAPPING = {
    'assist2017': 'assist2017',
    'nips_task34': 'nips_task34',
    'algebra2005': 'algebra2005',
    'bridge2006': 'bridge2algebra2006'
}

# 模板库 - 回答正确
TEMPLATES_CORRECT = [
    "The student successfully solved a {concept} problem.",
    "The student correctly answered a question on {concept}.",
    "The student demonstrated understanding of {concept} by answering correctly.",
    "The student tackled a {concept} question and got it right.",
    "The student showed mastery of {concept} in this attempt.",
    "The student nailed the {concept} concept.",
    "The student aced a problem involving {concept}.",
    "The student cracked a {concept} question successfully.",
    "The student confidently handled {concept}.",
    "The student skillfully worked through {concept}.",
    "The student demonstrated proficiency in {concept}.",
    "The student solved a {concept} problem with ease.",
    "The student correctly applied {concept} knowledge.",
    "The student answered a {concept} question accurately.",
    "The student mastered the {concept} task."
]

# 模板库 - 回答错误
TEMPLATES_INCORRECT = [
    "The student struggled with a {concept} question.",
    "The student made an error on a {concept} problem.",
    "The student found {concept} challenging in this attempt.",
    "The student attempted {concept} but answered incorrectly.",
    "The student had difficulty with a {concept} question.",
    "The student stumbled on {concept}.",
    "The student fumbled a {concept} problem.",
    "The student missed a {concept} question.",
    "The student struggled to apply {concept}.",
    "The student encountered challenges with {concept}.",
    "The student made a mistake on {concept}.",
    "The student answered a {concept} question incorrectly.",
    "The student faced difficulty understanding {concept}.",
    "The student got a {concept} problem wrong.",
    "The student had trouble with {concept} in this attempt."
]

def load_concept_mapping(dataset_name):
    """加载concept ID到文本的映射"""
    actual_dataset = DATASET_MAPPING.get(dataset_name, dataset_name)
    keyid_file = f'/mnt/localssd/pykt-toolkit/data/{actual_dataset}/keyid2idx.json'
    
    if not os.path.exists(keyid_file):
        return {}
    
    with open(keyid_file) as f:
        data = json.load(f)
    
    concepts_dict = data.get('concepts', {})
    idx2concept = {v: k for k, v in concepts_dict.items()}
    
    # 对于 nips_task34，concept 是数字 ID，需要映射到实际的 subject 名称
    if dataset_name == 'nips_task34':
        metadata_file = f'/mnt/localssd/pykt-toolkit/data/{actual_dataset}/metadata/subject_metadata.csv'
        if os.path.exists(metadata_file):
            df_subject = pd.read_csv(metadata_file)
            subject_map = {}
            for _, row in df_subject.iterrows():
                subject_id = str(row['SubjectId'])
                name = row['Name']
                subject_map[subject_id] = name
            
            # 将 idx2concept 中的数字 ID 替换为实际名称
            new_idx2concept = {}
            for idx, concept_id in idx2concept.items():
                if concept_id in subject_map:
                    new_idx2concept[idx] = subject_map[concept_id]
                else:
                    new_idx2concept[idx] = concept_id
            idx2concept = new_idx2concept
            
            print(f"  📋 为 nips_task34 加载了 {len(subject_map)} 个 Subject 映射")
    
    return idx2concept

def parse_csv_field(field_str):
    """解析CSV字段"""
    if pd.isna(field_str) or field_str == '':
        return []
    return [int(x) for x in str(field_str).split(',')]

def extract_student_data(row, idx2concept):
    """提取学生数据，排除每个concept的最后一次
    
    Args:
        row: 已合并的单行学生数据
        idx2concept: concept映射
    """
    uid = row['uid']
    
    # 解析字段（已经是合并后的数据）
    questions = parse_csv_field(row['questions'])
    concepts = parse_csv_field(row['concepts'])
    responses = parse_csv_field(row['responses'])
    timestamps = parse_csv_field(row['timestamps'])
    
    # 构建交互
    interactions = []
    for i in range(min(len(questions), len(concepts), len(responses), len(timestamps))):
        interactions.append({
            'question_id': questions[i],
            'concept_id': concepts[i],
            'concept_text': idx2concept.get(concepts[i], f'Concept {concepts[i]}'),
            'response': responses[i],
            'timestamp': timestamps[i]
        })
    
    # 按concept分组
    concept_groups = defaultdict(list)
    for inter in interactions:
        concept_groups[inter['concept_id']].append(inter)
    
    # 分离历史和最后一次
    history = []
    last_interactions = {}
    
    for cid, inters in concept_groups.items():
        concept_text = inters[0]['concept_text']
        if len(inters) > 1:
            history.extend(inters[:-1])
            last_interactions[str(cid)] = {
                'concept_id': cid,
                'concept_text': concept_text,
                'question_id': inters[-1]['question_id'],
                'response': inters[-1]['response'],
                'timestamp': inters[-1]['timestamp']
            }
        elif len(inters) == 1:
            last_interactions[str(cid)] = {
                'concept_id': cid,
                'concept_text': concept_text,
                'question_id': inters[0]['question_id'],
                'response': inters[0]['response'],
                'timestamp': inters[0]['timestamp']
            }
    
    return {
        'uid': uid,
        'history': history,
        'last_interactions': last_interactions
    }

def generate_memory_template(history):
    """使用模板生成memory - 处理所有历史记录"""
    memories = []
    
    # 按时间排序
    history_sorted = sorted(history, key=lambda x: x['timestamp'])
    
    # 为每条历史记录生成描述
    for inter in history_sorted:
        concept_text = inter['concept_text']
        
        # 根据response选择模板
        if inter['response'] == 1:
            templates = TEMPLATES_CORRECT
        else:
            templates = TEMPLATES_INCORRECT
        
        # 使用question_id和concept_id来"随机"选择模板（保证可复现）
        template_idx = (inter['question_id'] + inter['concept_id']) % len(templates)
        description = templates[template_idx].format(concept=concept_text)
        
        memories.append({
            'concept_id': int(inter['concept_id']),
            'concept_text': concept_text,
            'description': description,
            'keywords': concept_text,
            'question_id': inter['question_id'],
            'response': inter['response'],
            'timestamp': inter['timestamp']
        })
    
    return memories

def generate_embeddings_batch(texts, model):
    """批量生成embeddings"""
    if not texts:
        return []
    
    try:
        result = model.encode(texts, batch_size=min(32, len(texts)))
        return result
    except Exception as e:
        print(f"  Embedding生成失败: {e}")
        return None

def process_student(row, dataset_name, idx2concept, bge_model):
    """处理单个学生"""
    try:
        # 提取数据（row已经是合并后的数据）
        data = extract_student_data(row, idx2concept)
        uid = str(data['uid'])
        
        if len(data['history']) == 0:
            return {'uid': uid, 'status': 'skipped', 'reason': 'no_history', 'memory_count': 0, 'unique_concepts': 0}
        
        # 生成memory（全量，不限制数量）
        memories = generate_memory_template(data['history'])
        
        # 保存memory数据文件
        base_dir = f"/mnt/localssd/bank"
        memory_data_file = f"{base_dir}/memory/{dataset_name}/data/{uid}.json"
        os.makedirs(os.path.dirname(memory_data_file), exist_ok=True)
        with open(memory_data_file, 'w', encoding='utf-8') as f:
            json.dump(memories, f, ensure_ascii=False, indent=2)
        
        # 生成memory embeddings
        if memories and bge_model is not None:
            desc_texts = [m['description'] for m in memories]
            key_texts = [m['keywords'] for m in memories]
            
            desc_embs = generate_embeddings_batch(desc_texts, bge_model)
            key_embs = generate_embeddings_batch(key_texts, bge_model)
            
            emb_dir = f"{base_dir}/memory/{dataset_name}/embeddings"
            os.makedirs(emb_dir, exist_ok=True)
            
            if desc_embs is not None:
                desc_emb_file = f"{emb_dir}/{uid}_description.npz"
                np.savez_compressed(desc_emb_file, embeddings=desc_embs)
            
            if key_embs is not None:
                key_emb_file = f"{emb_dir}/{uid}_keywords.npz"
                np.savez_compressed(key_emb_file, embeddings=key_embs)
        
        # 统计信息
        unique_concepts = len(set(m['concept_id'] for m in memories))
        
        return {
            'uid': uid,
            'status': 'success',
            'memory_count': len(memories),
            'unique_concepts': unique_concepts
        }
    
    except Exception as e:
        return {'uid': str(row['uid']), 'status': 'error', 'error': str(e)}

def verify_memory_persona_consistency(dataset_name, student_ids):
    """验证memory和persona的concept一致性"""
    print(f"\n{'='*80}")
    print(f"验证 {dataset_name} 的Memory和Persona一致性")
    print(f"{'='*80}\n")
    
    for uid in student_ids:
        uid_str = str(uid)
        
        # 读取persona
        persona_file = f'/mnt/localssd/bank/persona/{dataset_name}/data/{uid_str}.json'
        if not os.path.exists(persona_file):
            print(f"  学生{uid}: Persona文件不存在")
            continue
        
        with open(persona_file) as f:
            persona = json.load(f)
        
        persona_concepts = set(p['concept_id'] for p in persona)
        
        # 读取memory
        memory_file = f'/mnt/localssd/bank/memory/{dataset_name}/data/{uid_str}.json'
        if not os.path.exists(memory_file):
            print(f"  学生{uid}: Memory文件不存在")
            continue
        
        with open(memory_file) as f:
            memory = json.load(f)
        
        memory_concepts = set(m['concept_id'] for m in memory)
        
        # 对比
        match = persona_concepts == memory_concepts
        status = '✅ 完全匹配' if match else '❌ 不匹配'
        
        print(f"  学生{uid}:")
        print(f"    Persona concepts: {len(persona_concepts)} 个")
        print(f"    Memory concepts:  {len(memory_concepts)} 个")
        print(f"    Memory records:   {len(memory)} 条")
        print(f"    状态: {status}")
        
        if not match:
            only_in_persona = persona_concepts - memory_concepts
            only_in_memory = memory_concepts - persona_concepts
            if only_in_persona:
                print(f"    只在Persona中: {sorted(only_in_persona)[:10]}...")
            if only_in_memory:
                print(f"    只在Memory中:  {sorted(only_in_memory)[:10]}...")
        print()

def main(dataset_name, test_mode=False, test_students=3):
    """主函数"""
    print("="*100)
    print(f"重新生成Memory - {dataset_name.upper()}")
    print(f"模式: {'测试模式 (前{}个学生)'.format(test_students) if test_mode else '全量模式'}")
    print("="*100)
    print()
    
    # 1. 加载concept映射
    print("📂 加载Concept映射...")
    idx2concept = load_concept_mapping(dataset_name)
    print(f"  ✅ 加载了 {len(idx2concept)} 个concept映射")
    print()
    
    # 2. 加载数据（train + test）并合并同一学生的多行数据
    actual_dataset = DATASET_MAPPING.get(dataset_name, dataset_name)
    train_file = f'/mnt/localssd/pykt-toolkit/data/{actual_dataset}/train_valid_sequences.csv'
    test_file = f'/mnt/localssd/pykt-toolkit/data/{actual_dataset}/test_sequences.csv'
    
    print(f"📂 加载数据:")
    print(f"  Train+Valid: {train_file}")
    df_train = pd.read_csv(train_file)
    print(f"    行数: {len(df_train)}, unique学生: {df_train['uid'].nunique()}")
    
    # 加载test数据（如果存在）
    if os.path.exists(test_file):
        print(f"  Test: {test_file}")
        df_test = pd.read_csv(test_file)
        print(f"    行数: {len(df_test)}, unique学生: {df_test['uid'].nunique()}")
        
        # 合并train和test
        df = pd.concat([df_train, df_test], ignore_index=True)
        print(f"  合并后总行数: {len(df)}, unique学生: {df['uid'].nunique()}")
    else:
        print(f"  ⚠️  Test文件不存在，只使用train+valid数据")
        df = df_train
    
    # 合并同一学生的多行数据（参考create_student_bank_final.py的逻辑）
    print(f"  合并同一学生的多个sequence...")
    grouped = df.groupby('uid')
    merged_data = []
    
    for uid, group in grouped:
        merged_row = {'uid': uid}
        # 合并questions, concepts, responses, timestamps字段
        for col in ['questions', 'concepts', 'responses', 'timestamps']:
            if col in group.columns:
                all_vals = []
                for val in group[col]:
                    if pd.notna(val) and val != '' and str(val) != '-1':
                        vals = [v.strip() for v in str(val).split(',') if v.strip() != '-1' and v.strip() != '']
                        all_vals.extend(vals)
                merged_row[col] = ','.join(all_vals) if all_vals else ''
        merged_data.append(merged_row)
    
    df = pd.DataFrame(merged_data)
    print(f"  合并后: {len(df)} 个unique学生")
    
    if test_mode:
        df = df.head(test_students)
        print(f"  ⚠️  测试模式: 只处理前{test_students}个学生")
    
    print(f"  ✅ 将处理 {len(df)} 个学生")
    print()
    
    # 3. 初始化BGE模型
    print("🤖 初始化BGE模型...")
    bge_model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
    print("  ✅ BGE模型加载完成")
    print()
    
    # 4. 处理学生（数据已经合并过了）
    print(f"🔄 处理学生 (共{len(df)}个)...")
    print()
    
    results = []
    for _, row in tqdm(df.iterrows(), total=len(df), desc="生成Memory", ncols=100):
        result = process_student(row, dataset_name, idx2concept, bge_model)
        results.append(result)
    
    # 5. 统计
    print()
    print("📊 处理结果:")
    success_count = sum(1 for r in results if r['status'] == 'success')
    skipped_count = sum(1 for r in results if r['status'] == 'skipped')
    error_count = sum(1 for r in results if r['status'] == 'error')
    
    print(f"  成功: {success_count}")
    print(f"  跳过: {skipped_count}")
    print(f"  错误: {error_count}")
    
    if success_count > 0:
        total_memories = sum(r.get('memory_count', 0) for r in results if r['status'] == 'success')
        avg_memories = total_memories / success_count
        total_concepts = sum(r.get('unique_concepts', 0) for r in results if r['status'] == 'success')
        avg_concepts = total_concepts / success_count
        
        print(f"\n  Memory统计:")
        print(f"    总记录数: {total_memories}")
        print(f"    平均每学生: {avg_memories:.1f} 条")
        print(f"    平均unique concepts: {avg_concepts:.1f} 个")
    
    print()
    
    # 6. 验证（测试模式下）
    if test_mode:
        test_uids = df['uid'].unique().tolist()
        verify_memory_persona_consistency(dataset_name, test_uids)
    
    print("="*100)
    print("✅ 完成！")
    print("="*100)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='重新生成Memory（全量）')
    parser.add_argument('--dataset', type=str, required=True, help='数据集名称')
    parser.add_argument('--test', action='store_true', help='测试模式（只处理前N个学生）')
    parser.add_argument('--test-students', type=int, default=3, help='测试模式下处理的学生数')
    
    args = parser.parse_args()
    main(args.dataset, test_mode=args.test, test_students=args.test_students)

