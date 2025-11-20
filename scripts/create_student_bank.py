#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
创建学生Persona和Memory Bank - 最终版
- Temperature = 1.0
- 每个学生单独文件
- 使用真实concept文本描述
"""

import os
import json
import pandas as pd
import numpy as np
from collections import defaultdict
from tqdm import tqdm
try:
    from FlagEmbedding import BGEM3FlagModel
except ImportError:
    # Fallback for older FlagEmbedding versions (Python 3.7 compatibility)
    from FlagEmbedding import FlagModel as BGEM3FlagModel

import openai
import time

# LLM配置
ENDPOINT = ""  # Your API endpoint
KEY = ""  # Your API key
MODEL = "gpt-4o"
TEMPERATURE = 1.0  # 修改为1.0

# 配置旧版openai
openai.api_key = f"Bearer {KEY}"
openai.api_base = ENDPOINT

# 并行处理配置
MAX_WORKERS = 30  # 按学生并行的进程数（每个进程处理完整学生流程：LLM + BGE + 保存）

# 数据集配置 - 包含train_valid和test
DATASETS = {
    'assist2017': {
        'data_paths': [
            '/mnt/localssd/pykt-toolkit/data/assist2017/train_valid_sequences.csv',
            '/mnt/localssd/pykt-toolkit/data/assist2017/test_sequences.csv'
        ],
        'keyid2idx_path': '/mnt/localssd/pykt-toolkit/data/assist2017/keyid2idx.json',
    },
    'nips_task34': {
        'data_paths': [
            '/mnt/localssd/pykt-toolkit/data/nips_task34/train_valid_sequences.csv',
            '/mnt/localssd/pykt-toolkit/data/nips_task34/test_sequences.csv'
        ],
        'keyid2idx_path': '/mnt/localssd/pykt-toolkit/data/nips_task34/keyid2idx.json',
    },
    'algebra2005': {
        'data_paths': [
            '/mnt/localssd/pykt-toolkit/data/algebra2005/train_valid_sequences.csv',
            '/mnt/localssd/pykt-toolkit/data/algebra2005/test_sequences.csv'
        ],
        'keyid2idx_path': '/mnt/localssd/pykt-toolkit/data/algebra2005/keyid2idx.json',
    },
    'bridge2006': {
        'data_paths': [
            '/mnt/localssd/pykt-toolkit/data/bridge2algebra2006/train_valid_sequences.csv',
            '/mnt/localssd/pykt-toolkit/data/bridge2algebra2006/test_sequences.csv'
        ],
        'keyid2idx_path': '/mnt/localssd/pykt-toolkit/data/bridge2algebra2006/keyid2idx.json',
    }
}

# 全局变量
bge_model = None
llm_client = None

def init_models():
    """初始化模型"""
    global bge_model, llm_client
    
    if bge_model is None:
        print("加载BGE-M3模型...")
        # 旧版FlagModel (v1.1.6) 不接受device/devices参数，自动使用CUDA
        bge_model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
        print("BGE-M3加载完成")
    
    if llm_client is None:
        print("初始化LLM客户端...")
        # 旧版openai不需要创建client，直接使用模块级API
        llm_client = True  # 标记已初始化
        print("LLM客户端就绪")
    
    return bge_model, llm_client

def load_concept_mapping(dataset_name, keyid2idx_path):
    """加载concept ID到文本的映射"""
    try:
        with open(keyid2idx_path, 'r') as f:
            keyid2idx = json.load(f)
        
        # 创建从idx到concept文本的反向映射
        if 'concepts' in keyid2idx:
            idx2concept = {v: k for k, v in keyid2idx['concepts'].items()}
            
            # 对于 nips_task34，concept 是数字 ID，需要映射到实际的 subject 名称
            if dataset_name == 'nips_task34':
                metadata_file = '/mnt/localssd/pykt-toolkit/data/nips_task34/metadata/subject_metadata.csv'
                if os.path.exists(metadata_file):
                    import pandas as pd
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
                    
                    print(f"  {dataset_name}: 📋 加载了 {len(subject_map)} 个 Subject 映射")
            
            print(f"  {dataset_name}: 加载了 {len(idx2concept)} 个concept映射")
            return idx2concept
        else:
            print(f"  {dataset_name}: 未找到concept映射")
            return {}
    except Exception as e:
        print(f"  {dataset_name}: 加载映射失败 - {e}")
        return {}

def get_concept_text(concept_id, idx2concept):
    """获取concept的文本描述"""
    if concept_id in idx2concept:
        return idx2concept[concept_id]
    else:
        return f"Concept {concept_id}"

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
    except:
        return []

def extract_student_data(row, dataset_name, idx2concept):
    """提取学生数据，排除最后一次答题"""
    uid = row['uid']
    
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
            'concept_text': get_concept_text(concepts[i], idx2concept),
            'response': responses[i],
            'timestamp': timestamps[i],
            'index': i
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
            # 只有一次，保存为last但不用于persona/memory
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

def generate_persona_llm(uid, history, dataset_name):
    """使用LLM生成persona"""
    # 按concept统计
    stats = defaultdict(lambda: {'correct': 0, 'total': 0, 'concept_text': ''})
    for inter in history:
        cid = inter['concept_id']
        stats[cid]['total'] += 1
        stats[cid]['concept_text'] = inter['concept_text']
        if inter['response'] == 1:
            stats[cid]['correct'] += 1
    
    if not stats:
        return []
    
    # 构建prompt（使用真实concept文本）
    system_prompt = """You are an educational analyst. Summarize each concept's mastery level in 2 sentences based on performance data. Be concise and specific."""
    
    user_prompt = f"Student {uid} ({dataset_name}):\n\n"
    for cid, s in list(stats.items())[:20]:  # 限制20个concept
        acc = s['correct'] / s['total'] if s['total'] > 0 else 0
        user_prompt += f"{s['concept_text']}: {s['correct']}/{s['total']} ({acc:.0%})\n"
    
    user_prompt += "\nFor each concept above, provide: 1) Overall mastery (excellent/good/struggling), 2) One insight. Format: 'Concept name: [2 sentences]'"
    
    try:
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=TEMPERATURE,  # 使用1.0
            max_tokens=800
        )
        
        content = response['choices'][0]['message']['content']
        
        # 检查content是否为空
        if not content or content.strip() == "":
            raise ValueError(f"LLM返回空响应。Response对象: {response}")
        
        # 解析响应，创建persona
        personas = []
        for cid, s in stats.items():
            acc = s['correct'] / s['total'] if s['total'] > 0 else 0
            if acc >= 0.8:
                level = "excellent mastery"
            elif acc >= 0.6:
                level = "good understanding"
            else:
                level = "needs improvement"
            
            concept_text = s['concept_text']
            desc = f"Student shows {level} of '{concept_text}' with {acc:.0%} accuracy over {s['total']} attempts."
            
            personas.append({
                'concept_id': int(cid),
                'concept_text': concept_text,
                'description': desc,
                'keywords': concept_text,
                'stats': {
                    'correct': s['correct'],
                    'total': s['total']
                }
            })
        
        return personas
    
    except Exception as e:
        print(f"  LLM生成persona失败: {e}")
        return []

def generate_memory_llm(uid, history, dataset_name):
    """使用LLM生成更自然的memory描述"""
    memories = []
    
    # 限制数量，分批处理
    max_memories = 50
    sample_history = history[:max_memories]
    
    if not sample_history:
        return []
    
    # 构建prompt，让LLM生成自然的事件描述
    system_prompt = """You are creating natural event descriptions for a student's learning journey. 

For each learning event, write a brief, natural description (one sentence) that varies in style. Include:
- What concept was practiced
- Whether they succeeded or struggled
- Use varied phrasing (e.g., "tackled", "worked on", "attempted", "solved", "struggled with", "mastered")
- Be concise but natural

IMPORTANT: Always use "The student" as the subject. Do NOT use pronouns like "They", "He", "She", or "Their".

Examples:
- "The student tackled an equation-solving problem."
- "The student demonstrated understanding of proportion."
- "The student struggled with geometry basics."

Vary your language - don't repeat the same patterns."""

    # 分批处理（每次10个事件）
    batch_size = 10
    
    # 不同的风格提示，为每批随机选择
    style_hints = [
        "Use active voice and action verbs like 'tackled', 'mastered', 'struggled with'.",
        "Focus on the learning process: 'attempted', 'worked through', 'practiced'.",
        "Emphasize outcomes: 'succeeded in', 'got right', 'missed', 'nailed'.",
        "Use casual academic tone: 'answered correctly', 'made an error on', 'solved'.",
        "Be descriptive: 'demonstrated understanding', 'showed proficiency', 'had difficulty'.",
        "Mix metaphors: 'cracked', 'fumbled', 'aced', 'stumbled on'."
    ]
    
    for batch_idx, batch_start in enumerate(range(0, len(sample_history), batch_size)):
        batch = sample_history[batch_start:batch_start + batch_size]
        
        # 为这批选择一个风格（使用批次索引和学生ID来"随机"选择）
        style_idx = (batch_idx + hash(uid)) % len(style_hints)
        current_style = style_hints[style_idx]
        
        user_prompt = f"Student {uid} ({dataset_name}) learning events:\n\n"
        for i, inter in enumerate(batch, 1):
            concept_text = inter['concept_text']
            result = "correctly" if inter['response'] == 1 else "incorrectly"
            user_prompt += f"{i}. Concept: '{concept_text}', Result: {result}\n"
        
        user_prompt += f"""\nFor each event above, write ONE natural sentence describing what happened. 
{current_style}
Return JSON format:
{{
  "memories": [
    {{"index": 1, "description": "<natural sentence>"}},
    {{"index": 2, "description": "<natural sentence>"}},
    ...
  ]
}}"""
        
        try:
            response = openai.ChatCompletion.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,  # 使用0.7以获得更自然的变化
                max_tokens=500
            )
            
            content = response['choices'][0]['message']['content']
            
            # 检查content是否为空
            if not content or content.strip() == "":
                raise ValueError(f"LLM返回空响应。Response对象: {response}")
            
            # 去除可能的markdown代码块标记（GPT-4o在使用json_object格式时会添加）
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]  # 移除 ```json
            if content.startswith("```"):
                content = content[3:]  # 移除 ```
            if content.endswith("```"):
                content = content[:-3]  # 移除结尾的 ```
            content = content.strip()
            
            result = json.loads(content)
            
            # 匹配LLM生成的描述到原始交互
            if 'memories' in result:
                for mem in result['memories']:
                    idx = mem.get('index', 1) - 1
                    if idx < len(batch):
                        inter = batch[idx]
                        memories.append({
                            'concept_id': int(inter['concept_id']),
                            'concept_text': inter['concept_text'],
                            'description': mem.get('description', ''),
                            'keywords': inter['concept_text'],
                            'question_id': inter['question_id'],
                            'response': inter['response'],
                            'timestamp': inter['timestamp']
                        })
        
        except Exception as e:
            print(f"  LLM生成memory失败，使用后备方案: {e}")
            # 后备方案：使用变化的模板
            templates_correct = [
                "Successfully solved a {} problem.",
                "Correctly answered a question on {}.",
                "Demonstrated understanding of {} by answering correctly.",
                "Tackled a {} question and got it right.",
                "Showed mastery of {} in this attempt."
            ]
            templates_incorrect = [
                "Struggled with a {} question.",
                "Made an error on a {} problem.",
                "Found {} challenging in this attempt.",
                "Attempted {} but answered incorrectly.",
                "Had difficulty with a {} question."
            ]
            
            for inter in batch:
                concept_text = inter['concept_text']
                if inter['response'] == 1:
                    templates = templates_correct
                else:
                    templates = templates_incorrect
                
                # 使用交互索引来"随机"选择模板
                template_idx = (inter['question_id'] + inter['concept_id']) % len(templates)
                desc = templates[template_idx].format(concept_text)
                
                memories.append({
                    'concept_id': int(inter['concept_id']),
                    'concept_text': concept_text,
                    'description': desc,
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
        # 旧版FlagModel (v1.1.6) 的encode()方法不接受return_dense等参数
        # 直接调用encode会返回dense embeddings
        result = model.encode(texts, batch_size=min(32, len(texts)))
        return result
    except Exception as e:
        print(f"  Embedding生成失败: {e}")
        return None

def save_student_files(uid, personas, memories, last_interactions, dataset_name, bge_model):
    """保存单个学生的所有文件"""
    base_dir = f"/mnt/localssd/bank"
    
    # Persona数据文件
    persona_data_file = f"{base_dir}/persona/{dataset_name}/data/{uid}.json"
    os.makedirs(os.path.dirname(persona_data_file), exist_ok=True)
    with open(persona_data_file, 'w') as f:
        json.dump(personas, f, indent=2)
    
    # Persona embeddings - 分别保存description和keywords
    if personas:
        desc_texts = [p['description'] for p in personas]
        key_texts = [p['keywords'] for p in personas]
        
        desc_embs = generate_embeddings_batch(desc_texts, bge_model)
        key_embs = generate_embeddings_batch(key_texts, bge_model)
        
        emb_dir = f"{base_dir}/persona/{dataset_name}/embeddings"
        os.makedirs(emb_dir, exist_ok=True)
        
        if desc_embs is not None:
            desc_emb_file = f"{emb_dir}/{uid}_description.npz"
            np.savez_compressed(desc_emb_file, embeddings=desc_embs)
        
        if key_embs is not None:
            key_emb_file = f"{emb_dir}/{uid}_keywords.npz"
            np.savez_compressed(key_emb_file, embeddings=key_embs)
    
    # Memory数据文件
    memory_data_file = f"{base_dir}/memory/{dataset_name}/data/{uid}.json"
    os.makedirs(os.path.dirname(memory_data_file), exist_ok=True)
    with open(memory_data_file, 'w') as f:
        json.dump(memories, f, indent=2)
    
    # Memory embeddings - 分别保存description和keywords
    if memories:
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
    
    # Last interactions
    last_file = f"{base_dir}/persona/{dataset_name}/last_interactions/{uid}.json"
    os.makedirs(os.path.dirname(last_file), exist_ok=True)
    with open(last_file, 'w') as f:
        json.dump(last_interactions, f, indent=2)

# 全局BGE模型（每个worker进程lazy初始化一次）
_worker_bge_model = None

def get_worker_bge_model():
    """获取当前worker进程的BGE模型（lazy initialization）"""
    global _worker_bge_model
    if _worker_bge_model is None:
        print(f"  [Worker {os.getpid()}] 初始化BGE模型...")
        _worker_bge_model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
    return _worker_bge_model

def process_student_complete(row, dataset_name, idx2concept):
    """处理单个学生的完整流程：LLM生成 + BGE embedding + 保存"""
    try:
        # 提取数据
        data = extract_student_data(row, dataset_name, idx2concept)
        uid = str(data['uid'])
        
        if len(data['history']) == 0:
            # 获取BGE模型（只用于保存空文件）
            bge_model = get_worker_bge_model()
            save_student_files(uid, [], [], data['last_interactions'], dataset_name, bge_model)
            return {'uid': uid, 'status': 'skipped', 'reason': 'no_history'}
        
        # 1. 生成persona（LLM调用）
        personas = generate_persona_llm(uid, data['history'], dataset_name)
        
        # 2. 生成memory（LLM调用）
        memories = generate_memory_llm(uid, data['history'], dataset_name)
        
        # 3. 获取BGE模型并生成embeddings + 保存
        bge_model = get_worker_bge_model()
        save_student_files(uid, personas, memories, data['last_interactions'], dataset_name, bge_model)
        
        return {'uid': uid, 'status': 'success'}
    
    except Exception as e:
        print(f"  处理学生失败: {e}")
        import traceback
        traceback.print_exc()
        return {'uid': row.get('uid', 'unknown'), 'status': 'error', 'error': str(e)}

def process_dataset(dataset_name, config, max_students=None):
    """处理单个数据集（包含train_valid和test）"""
    print(f"\n{'='*60}")
    print(f"处理数据集: {dataset_name}")
    print(f"{'='*60}\n")
    
    data_paths = config['data_paths']
    keyid2idx_path = config['keyid2idx_path']
    
    # 加载所有数据文件（train_valid和test）
    all_dfs = []
    for data_path in data_paths:
        if os.path.exists(data_path):
            print(f"加载数据: {data_path}")
            df_part = pd.read_csv(data_path)
            all_dfs.append(df_part)
            print(f"  学生数: {len(df_part)}")
        else:
            print(f"⚠️  文件不存在: {data_path}")
    
    if not all_dfs:
        print(f"❌ 没有找到数据文件")
        return
    
    # 合并所有数据
    df = pd.concat(all_dfs, ignore_index=True)
    print(f"\n总记录数（train_valid + test）: {len(df)}")
    
    # 统计唯一学生数
    unique_students = df['uid'].nunique()
    print(f"唯一学生数: {unique_students}")
    
    # 如果同一个学生有多条记录，需要合并
    if len(df) > unique_students:
        print(f"检测到同一学生有多条记录，正在合并... ({len(df)}条记录 → {unique_students}个学生)")
        
        # 按学生ID分组并合并数据
        merged_data = []
        for uid, group in df.groupby('uid'):
            # 合并concepts, responses, timestamps等字段
            merged_row = {}
            merged_row['uid'] = uid
            merged_row['fold'] = group.iloc[0]['fold']  # 使用第一条的fold
            
            # 合并所有序列字段
            for col in ['questions', 'concepts', 'responses', 'timestamps', 'usetimes', 'selectmasks', 'is_repeat']:
                if col in group.columns:
                    # 合并所有行的该字段（去除-1的占位符）
                    all_vals = []
                    for val in group[col]:
                        if pd.notna(val) and val != '' and str(val) != '-1':
                            vals = [v.strip() for v in str(val).split(',') if v.strip() != '-1' and v.strip() != '']
                            all_vals.extend(vals)
                    merged_row[col] = ','.join(all_vals) if all_vals else ''
            
            merged_data.append(merged_row)
        
        df = pd.DataFrame(merged_data)
        print(f"合并完成: {len(df)}个学生")
    
    if max_students:
        df = df.head(max_students)
        print(f"测试模式：只处理前{max_students}个学生")
    
    # 加载concept映射
    idx2concept = load_concept_mapping(dataset_name, keyid2idx_path)
    
    # 按学生并行处理（每个进程处理完整流程：LLM + BGE + 保存）
    print(f"\n开始并行处理学生（{MAX_WORKERS}个进程）...")
    print(f"  - 每个进程独立处理：LLM生成 → BGE embedding → 保存文件")
    print(f"  - BGE模型：每个worker进程初始化一次，然后复用")
    
    from multiprocessing import Pool
    from functools import partial
    
    process_func = partial(process_student_complete, 
                          dataset_name=dataset_name, 
                          idx2concept=idx2concept)
    
    results = []
    with Pool(processes=MAX_WORKERS) as pool:
        for result in tqdm(pool.imap_unordered(process_func, [row for _, row in df.iterrows()]), 
                          total=len(df), 
                          desc=f"{dataset_name}"):
            results.append(result)
    
    # 统计
    success = sum(1 for r in results if r['status'] == 'success')
    skipped = sum(1 for r in results if r['status'] == 'skipped')
    errors = sum(1 for r in results if r['status'] == 'error')
    
    print(f"\n✅ {dataset_name} 完成: 成功{success}, 跳过{skipped}, 错误{errors}")

def main():
    """主函数"""
    print("="*60)
    print("  创建学生Persona和Memory Bank - 最终版")
    print("="*60)
    print(f"\n配置:")
    print(f"  - Temperature: {TEMPERATURE}")
    print(f"  - 存储: 每个学生单独文件")
    print(f"  - Concept: 使用真实文本描述")
    
    # 测试模式
    TEST_MODE = False
    max_students = None if TEST_MODE else None
    
    if TEST_MODE:
        print(f"\n⚠️  测试模式：每个数据集处理{max_students}个学生\n")
    
    for dataset_name, config in DATASETS.items():
        try:
            process_dataset(dataset_name, config, max_students)
        except Exception as e:
            print(f"\n❌ {dataset_name}失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("  ✅ 所有数据集处理完成！")
    print("="*60)

if __name__ == '__main__':
    main()

