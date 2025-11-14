#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
创建学生Persona和Memory Bank
为每个数据集的每个学生生成persona和memory，使用LLM总结并用BGE-M3编码
"""

import os
import json
import pandas as pd
import numpy as np
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import torch
from FlagEmbedding import BGEM3FlagModel
from openai import OpenAI
import time

# LLM配置（从example.py）
ENDPOINT = ""  # Your API endpoint
KEY = ""  # Your API key
MODEL = "gpt-4o"

# 并行进程数
MAX_WORKERS = 10

# 数据集配置
DATASETS = {
    'assist2017': {
        'train_path': '/mnt/localssd/pykt-toolkit/data/assist2017/train_valid_sequences.csv',
        'concept_map_path': None,  # 需要从原始数据提取
        'has_concept_text': False
    },
    'nips_task34': {
        'train_path': '/mnt/localssd/pykt-toolkit/data/nips_task34/train_valid_sequences.csv',
        'concept_map_path': None,  # 需要从metadata提取
        'has_concept_text': False
    },
    'algebra2005': {
        'train_path': '/mnt/localssd/pykt-toolkit/data/algebra2005/train_valid_sequences.csv',
        'concept_map_path': None,
        'has_concept_text': False
    },
    'bridge2006': {
        'train_path': '/mnt/localssd/pykt-toolkit/data/bridge2algebra2006/train_valid_sequences.csv',
        'concept_map_path': None,
        'has_concept_text': False
    }
}

# BGE-M3模型
bge_model = None

def init_bge_model():
    """初始化BGE-M3模型"""
    global bge_model
    if bge_model is None:
        print("正在加载BGE-M3模型...")
        bge_model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
        print("BGE-M3模型加载完成")
    return bge_model

def init_llm_client():
    """初始化LLM客户端"""
    client = OpenAI(
        api_key="Bearer " + KEY,
        base_url=ENDPOINT,
    )
    return client

def parse_csv_field(field_str):
    """解析CSV字段"""
    if pd.isna(field_str) or field_str == 'NA' or field_str == '':
        return []
    
    try:
        values = str(field_str).strip().split(',')
        result = []
        for v in values:
            v = v.strip()
            if v and v != '-1' and v != 'NA':
                try:
                    result.append(int(v))
                except ValueError:
                    result.append(v)
        return result
    except Exception as e:
        print(f"警告: 解析字段失败 {field_str}: {e}")
        return []

def load_concept_mapping(dataset_name):
    """加载concept到文本的映射"""
    config = DATASETS.get(dataset_name, {})
    
    # 尝试加载concept映射
    if config.get('concept_map_path') and os.path.exists(config['concept_map_path']):
        with open(config['concept_map_path'], 'r') as f:
            return json.load(f)
    
    # 如果没有映射，返回空字典（使用数字ID）
    return {}

def get_concept_text(concept_id, concept_map, dataset_name):
    """获取concept的文本描述"""
    concept_str = str(concept_id)
    
    # 如果有映射，使用映射
    if concept_map and concept_str in concept_map:
        return concept_map[concept_str]
    
    # 否则返回格式化的ID
    return f"Concept {concept_id}"

def extract_student_data(student_row, dataset_name, concept_map):
    """提取单个学生的数据，排除每个concept的最后一次答题"""
    uid = student_row['uid']
    
    # 解析字段
    questions = parse_csv_field(student_row['questions'])
    concepts = parse_csv_field(student_row['concepts'])
    responses = parse_csv_field(student_row['responses'])
    timestamps = parse_csv_field(student_row['timestamps'])
    
    # 构建交互序列
    interactions = []
    for i in range(len(responses)):
        if i < len(questions) and i < len(concepts) and i < len(timestamps):
            interactions.append({
                'question_id': questions[i] if i < len(questions) else None,
                'concept_id': concepts[i],
                'response': responses[i],
                'timestamp': timestamps[i] if i < len(timestamps) else None,
                'index': i
            })
    
    # 按concept分组，找出每个concept的最后一次
    concept_interactions = defaultdict(list)
    for inter in interactions:
        concept_interactions[inter['concept_id']].append(inter)
    
    # 分离最后一次和历史记录
    history_interactions = []
    last_interactions = {}
    
    for concept_id, inters in concept_interactions.items():
        if len(inters) > 1:
            # 有多次交互，保留最后一次
            history_interactions.extend(inters[:-1])
            last_interactions[concept_id] = inters[-1]
        elif len(inters) == 1:
            # 只有一次交互，当作历史（不生成persona/memory）
            # 但保存为last_interaction
            last_interactions[concept_id] = inters[0]
    
    return {
        'uid': uid,
        'history_interactions': history_interactions,
        'last_interactions': last_interactions,
        'concept_map': concept_map,
        'dataset_name': dataset_name
    }

def generate_persona_prompt(student_data):
    """生成Persona提取的prompt"""
    uid = student_data['uid']
    history = student_data['history_interactions']
    concept_map = student_data['concept_map']
    dataset_name = student_data['dataset_name']
    
    # 按concept统计
    concept_stats = defaultdict(lambda: {'correct': 0, 'total': 0, 'interactions': []})
    for inter in history:
        cid = inter['concept_id']
        concept_stats[cid]['total'] += 1
        if inter['response'] == 1:
            concept_stats[cid]['correct'] += 1
        concept_stats[cid]['interactions'].append(inter)
    
    # 构建prompt
    system_prompt = """You are an educational data analyst. Your task is to summarize a student's long-term mastery level for each concept they have practiced, based on their historical performance data.

For each concept, analyze the student's answer history and create a concise summary that describes:
1. Their overall mastery level (e.g., "excellent mastery", "good understanding", "struggling", "needs improvement")
2. Their accuracy rate
3. Any notable patterns (e.g., "consistent performance", "improving over time", "declining performance")

Keep each summary to 2-3 sentences, focused and informative."""

    user_prompt = f"""Student ID: {uid}
Dataset: {dataset_name}

Below is the student's performance on each concept (excluding the most recent attempt on each concept):

"""
    
    for concept_id, stats in concept_stats.items():
        concept_text = get_concept_text(concept_id, concept_map, dataset_name)
        accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
        user_prompt += f"\nConcept: {concept_text}\n"
        user_prompt += f"- Total attempts: {stats['total']}\n"
        user_prompt += f"- Correct answers: {stats['correct']}\n"
        user_prompt += f"- Accuracy: {accuracy:.1%}\n"
    
    user_prompt += """\n\nPlease provide a JSON response with the following format:
{
  "personas": [
    {
      "concept_id": <concept_id>,
      "concept_text": "<concept_text>",
      "description": "<2-3 sentence summary of mastery level>",
      "keywords": "<concept_text as keywords>"
    },
    ...
  ]
}

Generate one persona entry for each concept listed above."""
    
    return system_prompt, user_prompt, concept_stats

def generate_memory_prompt(student_data):
    """生成Memory提取的prompt"""
    uid = student_data['uid']
    history = student_data['history_interactions']
    concept_map = student_data['concept_map']
    dataset_name = student_data['dataset_name']
    
    system_prompt = """You are an educational data analyst. Your task is to create event-based memory records for a student's learning activities.

For each question-answering event, create a concise description that includes:
1. What concept was being practiced
2. Whether the answer was correct or incorrect
3. The context (e.g., "attempted", "successfully solved", "struggled with")

Each memory should be a single sentence describing a specific event."""

    user_prompt = f"""Student ID: {uid}
Dataset: {dataset_name}

Below is the student's question-answering history (excluding the most recent attempt on each concept):

"""
    
    # 限制数量，避免prompt过长（取最多100个交互）
    sample_history = history[:100] if len(history) > 100 else history
    
    for i, inter in enumerate(sample_history, 1):
        concept_text = get_concept_text(inter['concept_id'], concept_map, dataset_name)
        result = "correctly" if inter['response'] == 1 else "incorrectly"
        user_prompt += f"\n{i}. Attempted {concept_text}, answered {result}"
    
    if len(history) > 100:
        user_prompt += f"\n... (showing first 100 of {len(history)} interactions)"
    
    user_prompt += """\n\nPlease provide a JSON response with the following format:
{
  "memories": [
    {
      "concept_id": <concept_id>,
      "concept_text": "<concept_text>",
      "description": "<one sentence describing this specific event>",
      "keywords": "<concept_text as keywords>"
    },
    ...
  ]
}

Generate one memory entry for each interaction listed above."""
    
    return system_prompt, user_prompt

def call_llm_with_retry(client, system_prompt, user_prompt, max_retries=3):
    """调用LLM，带重试机制"""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        
        except Exception as e:
            print(f"LLM调用失败 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
            else:
                return None

def generate_embeddings(texts, model):
    """使用BGE-M3生成embeddings"""
    try:
        embeddings = model.encode(texts, batch_size=32, max_length=512)['dense_vecs']
        return embeddings
    except Exception as e:
        print(f"Embedding生成失败: {e}")
        return None

def process_student(student_row, dataset_name, concept_map, client, bge_model):
    """处理单个学生的完整流程"""
    try:
        # 提取数据
        student_data = extract_student_data(student_row, dataset_name, concept_map)
        uid = student_data['uid']
        
        # 如果没有历史记录，跳过
        if len(student_data['history_interactions']) == 0:
            return {
                'uid': uid,
                'status': 'skipped',
                'reason': 'no_history',
                'personas': [],
                'memories': [],
                'last_interactions': student_data['last_interactions']
            }
        
        # 生成Persona
        system_prompt_p, user_prompt_p, concept_stats = generate_persona_prompt(student_data)
        persona_result = call_llm_with_retry(client, system_prompt_p, user_prompt_p)
        
        # 生成Memory
        system_prompt_m, user_prompt_m = generate_memory_prompt(student_data)
        memory_result = call_llm_with_retry(client, system_prompt_m, user_prompt_m)
        
        personas = []
        memories = []
        
        # 处理Persona结果
        if persona_result and 'personas' in persona_result:
            for p in persona_result['personas']:
                # 生成embeddings
                desc_text = p.get('description', '')
                key_text = p.get('keywords', '')
                
                if desc_text and key_text:
                    desc_emb = generate_embeddings([desc_text], bge_model)
                    key_emb = generate_embeddings([key_text], bge_model)
                    
                    personas.append({
                        'concept_id': p.get('concept_id'),
                        'concept_text': p.get('concept_text'),
                        'description': desc_text,
                        'keywords': key_text,
                        'description_embedding': desc_emb[0].tolist() if desc_emb is not None else None,
                        'keywords_embedding': key_emb[0].tolist() if key_emb is not None else None,
                        'stats': concept_stats.get(p.get('concept_id'), {})
                    })
        
        # 处理Memory结果
        if memory_result and 'memories' in memory_result:
            for m in memory_result['memories']:
                desc_text = m.get('description', '')
                key_text = m.get('keywords', '')
                
                if desc_text and key_text:
                    desc_emb = generate_embeddings([desc_text], bge_model)
                    key_emb = generate_embeddings([key_text], bge_model)
                    
                    memories.append({
                        'concept_id': m.get('concept_id'),
                        'concept_text': m.get('concept_text'),
                        'description': desc_text,
                        'keywords': key_text,
                        'description_embedding': desc_emb[0].tolist() if desc_emb is not None else None,
                        'keywords_embedding': key_emb[0].tolist() if key_emb is not None else None
                    })
        
        return {
            'uid': uid,
            'status': 'success',
            'personas': personas,
            'memories': memories,
            'last_interactions': student_data['last_interactions']
        }
    
    except Exception as e:
        print(f"处理学生失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            'uid': student_row.get('uid', 'unknown'),
            'status': 'error',
            'error': str(e),
            'personas': [],
            'memories': [],
            'last_interactions': {}
        }

def process_dataset(dataset_name, max_students=None):
    """处理单个数据集"""
    print(f"\n{'='*60}")
    print(f"处理数据集: {dataset_name}")
    print(f"{'='*60}\n")
    
    config = DATASETS[dataset_name]
    train_path = config['train_path']
    
    if not os.path.exists(train_path):
        print(f"❌ 数据文件不存在: {train_path}")
        return
    
    # 加载数据
    print(f"加载数据: {train_path}")
    df = pd.read_csv(train_path)
    
    if max_students:
        df = df.head(max_students)
    
    print(f"总学生数: {len(df)}")
    
    # 加载concept映射
    concept_map = load_concept_mapping(dataset_name)
    print(f"Concept映射: {len(concept_map)} 个")
    
    # 初始化模型
    client = init_llm_client()
    bge_model = init_bge_model()
    
    # 处理学生（并行）
    print(f"\n开始处理学生 (并行进程数: {MAX_WORKERS})...")
    
    results = []
    with ProcessPoolExecutor(max_workers=1) as executor:  # 暂时用1个进程测试
        # 注意：由于BGE模型和LLM client不能跨进程，需要在每个进程中初始化
        # 所以这里先用串行测试
        for idx, row in tqdm(df.iterrows(), total=len(df), desc=f"处理{dataset_name}"):
            result = process_student(row, dataset_name, concept_map, client, bge_model)
            results.append(result)
            
            # 每10个学生保存一次
            if len(results) % 10 == 0:
                save_results(results, dataset_name)
    
    # 最终保存
    save_results(results, dataset_name)
    
    print(f"\n✅ {dataset_name} 处理完成")
    print(f"  - 成功: {sum(1 for r in results if r['status'] == 'success')}")
    print(f"  - 跳过: {sum(1 for r in results if r['status'] == 'skipped')}")
    print(f"  - 错误: {sum(1 for r in results if r['status'] == 'error')}")

def save_results(results, dataset_name):
    """保存结果到文件"""
    base_dir = f"/mnt/localssd/bank"
    
    # 保存Persona
    persona_data = []
    for r in results:
        if r['personas']:
            persona_data.append({
                'uid': r['uid'],
                'personas': r['personas']
            })
    
    persona_file = f"{base_dir}/persona/{dataset_name}/data/personas.json"
    os.makedirs(os.path.dirname(persona_file), exist_ok=True)
    with open(persona_file, 'w') as f:
        json.dump(persona_data, f, indent=2)
    
    # 保存Memory
    memory_data = []
    for r in results:
        if r['memories']:
            memory_data.append({
                'uid': r['uid'],
                'memories': r['memories']
            })
    
    memory_file = f"{base_dir}/memory/{dataset_name}/data/memories.json"
    os.makedirs(os.path.dirname(memory_file), exist_ok=True)
    with open(memory_file, 'w') as f:
        json.dump(memory_data, f, indent=2)
    
    # 保存最后一次交互
    last_interactions = {}
    for r in results:
        if r.get('last_interactions'):
            last_interactions[r['uid']] = r['last_interactions']
    
    last_file = f"{base_dir}/persona/{dataset_name}/last_interactions/last_interactions.json"
    os.makedirs(os.path.dirname(last_file), exist_ok=True)
    with open(last_file, 'w') as f:
        json.dump(last_interactions, f, indent=2)

def main():
    """主函数"""
    print("="*60)
    print("  创建学生Persona和Memory Bank")
    print("="*60)
    
    # 测试模式：每个数据集只处理前5个学生
    TEST_MODE = True
    max_students = 5 if TEST_MODE else None
    
    if TEST_MODE:
        print("\n⚠️  测试模式：每个数据集只处理前5个学生")
    
    # 处理每个数据集
    for dataset_name in DATASETS.keys():
        try:
            process_dataset(dataset_name, max_students=max_students)
        except Exception as e:
            print(f"\n❌ 处理{dataset_name}失败: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "="*60)
    print("  ✅ 所有数据集处理完成！")
    print("="*60)

if __name__ == '__main__':
    main()

