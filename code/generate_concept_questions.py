#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
为每个数据集的concepts生成测试问题集
- 使用GPT-4o生成问题
- 每个concept生成10个问题
- 30个线程并行处理
"""

import os
import json
import argparse
from openai import OpenAI
import concurrent.futures
from tqdm import tqdm
import time

# LLM配置
ENDPOINT = ""  # Your API endpoint
KEY = ""  # Your API key
MODEL = "gpt-4o"
TEMPERATURE = 0.7  # 生成问题使用0.7，保持多样性但不会太随机

# 初始化OpenAI客户端
client = OpenAI(
    api_key="Bearer " + KEY,
    base_url=ENDPOINT,
)

# 数据集配置
DATASET_MAPPING = {
    'assist2017': 'assist2017',
    'nips_task34': 'nips_task34',
    'algebra2005': 'algebra2005',
    'bridge2006': 'bridge2algebra2006'
}

def load_concepts(dataset_name):
    """加载数据集的concept列表"""
    # 映射到实际的数据集目录名
    actual_dataset = DATASET_MAPPING.get(dataset_name, dataset_name)
    
    keyid_file = f'/mnt/localssd/pykt-toolkit/data/{actual_dataset}/keyid2idx.json'
    
    if not os.path.exists(keyid_file):
        print(f"❌ Keyid文件不存在: {keyid_file}")
        return {}
    
    with open(keyid_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # concepts字段：{concept_text: concept_id}
    concepts_dict = data.get('concepts', {})
    
    # 转换为 {concept_id: concept_text}
    concepts = {
        concept_id: concept_text 
        for concept_text, concept_id in concepts_dict.items()
    }
    
    print(f"  ✅ 加载了 {len(concepts)} 个concepts")
    return concepts

def generate_questions_for_concept(concept_id, concept_text, retry=3):
    """为单个concept生成10个问题"""
    
    system_prompt = """You are an expert educational content creator. Your task is to generate 10 diverse and high-quality test questions based on the given concept description.

Requirements:
1. Generate exactly 10 questions
2. Questions should test understanding of the concept at different difficulty levels
3. Include a mix of question types (factual, conceptual, application)
4. Make questions clear, specific, and answerable
5. Return ONLY a JSON array of 10 questions, no other text

Example output format:
["Question 1 text here", "Question 2 text here", ..., "Question 10 text here"]"""

    user_prompt = f"""Generate 10 test questions for the following concept:

Concept: {concept_text}

Generate questions that assess students' understanding of this concept. Return ONLY a JSON array of 10 question strings."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    for attempt in range(retry):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=TEMPERATURE
            )
            
            content = response.choices[0].message.content.strip()
            
            # 尝试解析JSON
            # 如果response被包在markdown代码块中，先提取
            if content.startswith('```'):
                # 提取JSON部分
                start = content.find('[')
                end = content.rfind(']') + 1
                if start != -1 and end > start:
                    content = content[start:end]
            
            questions = json.loads(content)
            
            # 验证格式
            if isinstance(questions, list) and len(questions) == 10:
                return {
                    'concept_id': concept_id,
                    'concept_description': concept_text,
                    'questions': questions
                }
            else:
                print(f"  ⚠️  Concept {concept_id}: 返回的问题数量不对 ({len(questions)}), 重试...")
                
        except json.JSONDecodeError as e:
            print(f"  ⚠️  Concept {concept_id}: JSON解析失败, 重试 {attempt+1}/{retry}...")
            time.sleep(1)
            
        except Exception as e:
            print(f"  ❌ Concept {concept_id}: 错误 - {e}, 重试 {attempt+1}/{retry}...")
            time.sleep(1)
    
    # 如果所有重试都失败，返回空问题
    print(f"  ❌ Concept {concept_id}: 所有重试失败，使用占位符")
    return {
        'concept_id': concept_id,
        'concept_description': concept_text,
        'questions': [f"Question {i+1} for {concept_text}" for i in range(10)]
    }

def generate_questions_for_dataset(dataset_name, max_workers=30):
    """为整个数据集生成问题"""
    print("="*100)
    print(f"📚 为 {dataset_name.upper()} 生成Concept问题集")
    print("="*100)
    print()
    
    # 1. 加载concepts
    print("📂 加载Concepts...")
    concepts = load_concepts(dataset_name)
    
    if not concepts:
        print("❌ 没有找到concepts，退出")
        return
    
    print()
    
    # 2. 使用多线程生成问题
    print(f"🤖 使用GPT-4o生成问题 (温度={TEMPERATURE}, 线程={max_workers})...")
    print()
    
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        futures = {
            executor.submit(generate_questions_for_concept, concept_id, concept_text): (concept_id, concept_text)
            for concept_id, concept_text in concepts.items()
        }
        
        # 使用tqdm显示进度
        for future in tqdm(concurrent.futures.as_completed(futures), 
                          total=len(futures), 
                          desc="生成问题", 
                          ncols=100):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                concept_id, concept_text = futures[future]
                print(f"  ❌ Concept {concept_id} 失败: {e}")
    
    # 3. 按concept_id排序
    results.sort(key=lambda x: x['concept_id'])
    
    # 4. 转换为目标格式
    output_data = {
        str(item['concept_id']): {
            'concept_description': item['concept_description'],
            'questions': item['questions']
        }
        for item in results
    }
    
    print()
    print(f"✅ 成功生成 {len(output_data)} 个concepts的问题集")
    print()
    
    # 5. 统计
    total_questions = sum(len(item['questions']) for item in output_data.values())
    print("📊 统计信息:")
    print(f"  Concepts总数: {len(output_data)}")
    print(f"  问题总数: {total_questions}")
    print(f"  平均每个concept: {total_questions / len(output_data):.1f} 个问题")
    print()
    
    # 6. 保存
    output_dir = f'/mnt/localssd/bank/test_data/{dataset_name}'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'concept_questions.json')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    file_size = os.path.getsize(output_file) / 1024 / 1024
    print("💾 保存结果:")
    print(f"  文件: {output_file}")
    print(f"  大小: {file_size:.2f}MB")
    print()
    
    # 7. 显示示例
    if output_data:
        sample_id = list(output_data.keys())[0]
        sample_data = output_data[sample_id]
        
        print("📋 示例数据:")
        print(f"  Concept ID: {sample_id}")
        print(f"  Description: {sample_data['concept_description']}")
        print(f"  Questions ({len(sample_data['questions'])}):")
        for i, q in enumerate(sample_data['questions'][:3], 1):
            print(f"    {i}. {q}")
        if len(sample_data['questions']) > 3:
            print(f"    ... (还有 {len(sample_data['questions']) - 3} 个问题)")

def main():
    parser = argparse.ArgumentParser(description='为数据集的concepts生成测试问题集')
    parser.add_argument('--dataset', type=str, required=True,
                       choices=['assist2017', 'nips_task34', 'algebra2005', 'bridge2006'],
                       help='数据集名称')
    parser.add_argument('--workers', type=int, default=30,
                       help='并行线程数 (默认: 30)')
    
    args = parser.parse_args()
    
    generate_questions_for_dataset(args.dataset, max_workers=args.workers)
    
    print("="*100)
    print("✅ 完成！")
    print("="*100)

if __name__ == '__main__':
    main()

