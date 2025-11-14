#!/usr/bin/env python3
"""
LLM as Judge for TASA variants vs Vanilla-ICL baselines
评估6个TASA变体方法，与对应backbone的Vanilla-ICL-conservative进行比较
"""

import json
import os
import sys
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
import re

# GPT-5 Judge配置（使用内网代理，更快）
import os
JUDGE_API_KEY = os.getenv("API_KEY", "")
JUDGE_ENDPOINT = os.getenv("ENDPOINT", "")
JUDGE_MODEL = "gpt-5-chat"

DATASETS = ['assist2017', 'algebra2005', 'bridge2006', 'nips_task34']

# 6个TASA方法及其对应的baseline
TASA_METHODS = [
    {
        'name': 'TASA-lambda0.5-gpt',
        'dialogue_path': '/mnt/localssd/bank/dialogue/TASA-lambda0.5-gpt',
        'baseline_dialogue_path': '/mnt/localssd/bank/dialogue/Vanilla-ICL',
        'backbone': 'gpt'
    },
    {
        'name': 'TASA-lambda0.5-llama',
        'dialogue_path': '/mnt/localssd/bank/dialogue/TASA-lambda0.5-llama',
        'baseline_dialogue_path': '/mnt/localssd/bank/dialogue/Vanilla-ICL-llama',
        'backbone': 'llama'
    },
    {
        'name': 'TASA-lambda0.5-qwen',
        'dialogue_path': '/mnt/localssd/bank/dialogue/TASA-lambda0.5-qwen',
        'baseline_dialogue_path': '/mnt/localssd/bank/dialogue/Vanilla-ICL-qwen',
        'backbone': 'qwen'
    },
    {
        'name': 'TASA-woForgetting-llama',
        'dialogue_path': '/mnt/localssd/bank/dialogue/TASA-woForgetting-llama',
        'baseline_dialogue_path': '/mnt/localssd/bank/dialogue/Vanilla-ICL-llama',
        'backbone': 'llama'
    },
    {
        'name': 'TASA-woMemory-llama',
        'dialogue_path': '/mnt/localssd/bank/dialogue/TASA-woMemory-llama',
        'baseline_dialogue_path': '/mnt/localssd/bank/dialogue/Vanilla-ICL-llama',
        'backbone': 'llama'
    },
    {
        'name': 'TASA-woPersona-llama',
        'dialogue_path': '/mnt/localssd/bank/dialogue/TASA-woPersona-llama',
        'baseline_dialogue_path': '/mnt/localssd/bank/dialogue/Vanilla-ICL-llama',
        'backbone': 'llama'
    }
]

def create_judge_prompt(target_method, baseline_method):
    """创建LLM judge的prompt"""
    return f"""You are an expert educational AI evaluator tasked with comparing two tutoring dialogues for the same student learning the same concept.

**Your Task:**
Compare Dialogue A ({target_method}) and Dialogue B ({baseline_method}) to determine which provides a MORE EFFECTIVE and PERSONALIZED learning experience.

**Evaluation Framework (Weighted Criteria):**

1. **Learning Effectiveness (50%)** - Primary consideration
   - Does the dialogue help the student master the concept?
   - Are explanations clear, accurate, and appropriate for the student's level?
   - Does the tutor effectively address misunderstandings?
   - Is feedback constructive and actionable?

2. **Personalization Value (35%)** - Secondary consideration  
   - Does the tutor adapt to the student's specific knowledge gaps or strengths?
   - Are examples/questions tailored to the student's learning history?
   - Does the tutor reference or build upon the student's past performance?

3. **Teaching Quality (15%)** - Supporting consideration
   - Is the tutoring approach pedagogically sound?
   - Does the tutor maintain appropriate pacing and engagement?
   - Are practice questions well-designed?

**What counts as EFFECTIVE personalization:**
- Adjusting difficulty based on student's demonstrated ability
- Referencing specific past struggles or successes meaningfully
- Providing targeted practice on identified weak areas
- Adapting explanation style when student shows confusion

**What is SUPERFICIAL (does NOT count as effective personalization):**
- Simply mentioning past topics without connecting to current learning
- Generic encouragement phrases with student data inserted
- Listing past performance without using it to inform instruction

**Decision Rules:**

→ **Choose "Winner"** (15-25% of cases) when ONE dialogue is CLEARLY more effective:
  - Significantly better learning outcomes (student shows real understanding)
  - Personalization directly improves learning effectiveness
  - One dialogue has major pedagogical flaws while the other doesn't

→ **Choose "Tie"** (75-85% of cases) as DEFAULT when:
  - Both dialogues achieve similar learning outcomes
  - Personalization differences don't significantly impact learning
  - Both are competent but neither stands out strongly
  - Trade-offs exist (one more personalized, other clearer explanations)

**Output Format:**

Winner: [Dialogue A / Dialogue B / Tie]

Overall Score: A [X/10], B [Y/10]

Reasoning: [2-3 sentences explaining your decision based on the weighted criteria. Focus on learning effectiveness first, then personalization value, then teaching quality.]

---

**Student Profile:**
{{STUDENT_PROFILE}}

**Concept:** {{CONCEPT}}

**Dialogue A ({target_method}):**
{{DIALOGUE_A}}

**Dialogue B ({baseline_method}):**
{{DIALOGUE_B}}
"""

def load_dialogue_files(method_info, dataset):
    """加载某个方法在某个dataset下的所有dialogue文件"""
    dialogue_path = method_info['dialogue_path']
    
    # 检查是否有dkt子目录
    if os.path.exists(f"{dialogue_path}/{dataset}/dkt"):
        dialogue_dir = f"{dialogue_path}/{dataset}/dkt"
    elif os.path.exists(f"{dialogue_path}/{dataset}"):
        dialogue_dir = f"{dialogue_path}/{dataset}"
    else:
        return {}
    
    dialogue_files = {}
    if not os.path.exists(dialogue_dir):
        return dialogue_files
    
    for fname in os.listdir(dialogue_dir):
        if fname.endswith('.json'):
            # 提取student_id
            student_id = fname.split('-')[0]
            dialogue_files[student_id] = os.path.join(dialogue_dir, fname)
    
    return dialogue_files

def find_common_students(target_dialogues, baseline_dialogues):
    """找到两个方法都有的学生"""
    target_students = set(target_dialogues.keys())
    baseline_students = set(baseline_dialogues.keys())
    common = target_students & baseline_students
    return sorted(common, key=lambda x: int(x))

def judge_comparison(target_dialogue, baseline_dialogue, student_profile, concept, 
                    target_method, baseline_method, judge_client):
    """使用LLM judge比较两个dialogue（带重试）"""
    import time
    
    # 构建prompt
    prompt_template = create_judge_prompt(target_method, baseline_method)
    
    # 格式化dialogue
    def format_dialogue(dialogue):
        if isinstance(dialogue, list):
            return '\n\n'.join([f"[Round {d.get('round', '?')}] {d.get('role', '?')}: {d.get('content', '')[:500]}" 
                               for d in dialogue[:20]])  # 限制长度
        else:
            return str(dialogue)[:2000]
    
    prompt = prompt_template.replace('{{STUDENT_PROFILE}}', student_profile or 'No profile available')
    prompt = prompt.replace('{{CONCEPT}}', concept)
    prompt = prompt.replace('{{DIALOGUE_A}}', format_dialogue(target_dialogue))
    prompt = prompt.replace('{{DIALOGUE_B}}', format_dialogue(baseline_dialogue))
    
    # 重试3次
    for attempt in range(3):
        try:
            response = judge_client.chat.completions.create(
                model=JUDGE_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert educational evaluator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800,
                timeout=60
            )
            
            result_text = response.choices[0].message.content
            
            # 解析结果
            winner = None
            if 'Winner: Dialogue A' in result_text or 'Winner: A' in result_text:
                winner = 'A'
            elif 'Winner: Dialogue B' in result_text or 'Winner: B' in result_text:
                winner = 'B'
            elif 'Winner: Tie' in result_text or 'Tie' in result_text:
                winner = 'Tie'
            
            # 提取分数
            score_a, score_b = None, None
            score_match = re.search(r'Overall Score:\s*A\s*\[(\d+)/10\],\s*B\s*\[(\d+)/10\]', result_text)
            if score_match:
                score_a = int(score_match.group(1))
                score_b = int(score_match.group(2))
            
            return {
                'winner': winner,
                'score_a': score_a,
                'score_b': score_b,
                'reasoning': result_text
            }
        except Exception as e:
            if attempt < 2:
                time.sleep(2 ** attempt)  # 指数退避：1s, 2s
                continue
            else:
                return None
    
    return None

def batch_judge(method_info, dataset, max_workers=20):
    """批量评估一个方法在一个dataset上的表现"""
    
    target_method = method_info['name']
    baseline_dialogue_path = method_info['baseline_dialogue_path']
    baseline_method = f"Vanilla-ICL-{method_info['backbone']}"
    
    print(f"\n{'='*80}", flush=True)
    print(f"📊 LLM as Judge: {target_method} vs {baseline_method}", flush=True)
    print(f"   Dataset: {dataset} | Backbone: {method_info['backbone']}", flush=True)
    print(f"{'='*80}\n", flush=True)
    
    # 加载dialogue文件
    target_dialogues = load_dialogue_files(method_info, dataset)
    
    # 加载baseline dialogues
    if os.path.exists(f"{baseline_dialogue_path}/{dataset}/dkt"):
        baseline_dir = f"{baseline_dialogue_path}/{dataset}/dkt"
    elif os.path.exists(f"{baseline_dialogue_path}/{dataset}"):
        baseline_dir = f"{baseline_dialogue_path}/{dataset}"
    else:
        print(f"⏭️  跳过{target_method}（{dataset}无baseline数据）\n")
        return None
    
    baseline_dialogues = {}
    for fname in os.listdir(baseline_dir):
        if fname.endswith('.json'):
            student_id = fname.split('-')[0]
            baseline_dialogues[student_id] = os.path.join(baseline_dir, fname)
    
    # 找common students
    common_students = find_common_students(target_dialogues, baseline_dialogues)
    
    if not common_students:
        print(f"⏭️  跳过{target_method}（{dataset}无common students）\n")
        return None
    
    print(f"📋 Common students: {len(common_students)}", flush=True)
    
    # Bootstrap sampling
    original_n = len(common_students)
    if original_n == 0:
        return None
    elif original_n <= 5:
        bootstrap_n = original_n * 4
    elif original_n <= 10:
        bootstrap_n = original_n * 3
    else:
        bootstrap_n = int(original_n * 2.5)
    
    print(f"🔄 Bootstrap采样后: {bootstrap_n}个dialogue（有放回）", flush=True)
    print(f"🚀 使用{max_workers}个并行worker\n", flush=True)
    
    print(f"⏳ 开始处理{bootstrap_n}个comparisons...", flush=True)
    
    # Bootstrap sampling
    sampled_students = random.choices(common_students, k=bootstrap_n)
    
    # 准备tasks
    tasks = []
    for student_id in sampled_students:
        tasks.append({
            'student_id': student_id,
            'target_file': target_dialogues[student_id],
            'baseline_file': baseline_dialogues[student_id]
        })
    
    # 初始化judge client
    judge_client = OpenAI(api_key=JUDGE_API_KEY, base_url=JUDGE_ENDPOINT)
    
    # 并行评估
    results = {'A_wins': 0, 'B_wins': 0, 'ties': 0, 'scores_a': [], 'scores_b': []}
    
    def process_task(task):
        try:
            # 加载dialogues
            with open(task['target_file']) as f:
                target_data = json.load(f)
            with open(task['baseline_file']) as f:
                baseline_data = json.load(f)
            
            # 提取dialogue
            target_dialogue = target_data if isinstance(target_data, list) else target_data.get('dialogue', [])
            baseline_dialogue = baseline_data if isinstance(baseline_data, list) else baseline_data.get('dialogue', [])
            
            # 提取concept
            if isinstance(target_data, dict):
                concept = target_data.get('concept', 'unknown')
            else:
                concept = os.path.basename(task['target_file']).replace(f"{task['student_id']}-", '').replace('.json', '')
            
            # Judge
            result = judge_comparison(
                target_dialogue, baseline_dialogue,
                f"Student {task['student_id']}", concept,
                target_method, baseline_method, judge_client
            )
            
            return result
        except Exception as e:
            print(f"   ⚠️  学生{task['student_id']}的dialogue评估失败: {e}")
            return None
    
    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_task, task): task for task in tasks}
        
        for future in as_completed(futures):
            result = future.result()
            completed += 1
            if completed % 5 == 0 or completed == len(tasks):
                print(f"   进度: {completed}/{len(tasks)}", flush=True)
            
            if result and result['winner']:
                if result['winner'] == 'A':
                    results['A_wins'] += 1
                elif result['winner'] == 'B':
                    results['B_wins'] += 1
                else:
                    results['ties'] += 1
                
                if result['score_a']:
                    results['scores_a'].append(result['score_a'])
                if result['score_b']:
                    results['scores_b'].append(result['score_b'])
    
    # 计算统计
    total = results['A_wins'] + results['B_wins'] + results['ties']
    if total == 0:
        return None
    
    win_rate = (results['A_wins'] / total) * 100
    tie_rate = (results['ties'] / total) * 100
    loss_rate = (results['B_wins'] / total) * 100
    
    avg_score_a = sum(results['scores_a']) / len(results['scores_a']) if results['scores_a'] else 0
    avg_score_b = sum(results['scores_b']) / len(results['scores_b']) if results['scores_b'] else 0
    
    print(f"\n📊 结果:")
    print(f"   Win rate: {win_rate:.1f}% ({results['A_wins']}W-{results['ties']}T-{results['B_wins']}L / {total})")
    print(f"   Avg scores: {target_method}={avg_score_a:.2f}/10, {baseline_method}={avg_score_b:.2f}/10")
    print(f"{'='*80}\n")
    
    # 保存结果
    result_dir = '/mnt/localssd/llm_judge_results'
    os.makedirs(result_dir, exist_ok=True)
    
    result_file = f'{result_dir}/{target_method}_vs_{baseline_method}_{dataset}.json'
    with open(result_file, 'w') as f:
        json.dump({
            'target_method': target_method,
            'baseline_method': baseline_method,
            'dataset': dataset,
            'backbone': method_info['backbone'],
            'common_students': len(common_students),
            'bootstrap_samples': bootstrap_n,
            'results': results,
            'win_rate': win_rate,
            'tie_rate': tie_rate,
            'loss_rate': loss_rate,
            'avg_score_target': avg_score_a,
            'avg_score_baseline': avg_score_b
        }, f, indent=2)
    
    return {
        'method': target_method,
        'dataset': dataset,
        'win_rate': win_rate,
        'tie_rate': tie_rate,
        'total': total
    }

def main():
    print('='*80, flush=True)
    print('🔬 LLM as Judge: TASA Variants评估', flush=True)
    print('='*80, flush=True)
    print(f'Methods: {len(TASA_METHODS)}')
    print(f'  - TASA-lambda0.5-gpt vs Vanilla-ICL-gpt')
    print(f'  - TASA-lambda0.5-llama vs Vanilla-ICL-llama')
    print(f'  - TASA-lambda0.5-qwen vs Vanilla-ICL-qwen')
    print(f'  - TASA-woForgetting-llama vs Vanilla-ICL-llama')
    print(f'  - TASA-woMemory-llama vs Vanilla-ICL-llama')
    print(f'  - TASA-woPersona-llama vs Vanilla-ICL-llama')
    print(f'Datasets: {DATASETS}')
    print(f'Max workers: 10')
    print('='*80)
    print()
    
    all_results = []
    
    for method_info in TASA_METHODS:
        for dataset in DATASETS:
            result = batch_judge(method_info, dataset, max_workers=20)
            if result:
                all_results.append(result)
    
    # 打印汇总
    print('\n' + '='*80)
    print('📊 所有评估汇总')
    print('='*80)
    for result in all_results:
        print(f"{result['method']:30s} | {result['dataset']:15s} | {result['win_rate']:5.1f}% ({result['total']} comparisons)")
    print('='*80)

if __name__ == '__main__':
    main()

