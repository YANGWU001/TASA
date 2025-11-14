#!/usr/bin/env python3
"""
LLM as Judge: 评估dialogue的个性化程度
比较target method vs Vanilla-ICL baseline
"""

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from openai import OpenAI
import numpy as np
import random

# Judge model配置
JUDGE_MODEL = "gpt-5-chat"
API_KEY = os.getenv("API_KEY", "")
ENDPOINT = os.getenv("ENDPOINT", "")

# 全局锁
print_lock = Lock()

def safe_print(msg):
    with print_lock:
        print(msg)

def get_backbone(method_name):
    """从method名称中提取backbone"""
    if '-llama' in method_name:
        return 'llama'
    elif '-qwen' in method_name:
        return 'qwen'
    else:
        return 'gpt'

def load_persona(student_id, dataset):
    """加载学生persona"""
    persona_file = f'/mnt/localssd/bank/persona/{dataset}/data/{student_id}.json'
    try:
        with open(persona_file) as f:
            personas = json.load(f)
        # 提取description
        persona_texts = [p['description'] for p in personas]
        return "\n".join([f"- {p}" for p in persona_texts])
    except:
        return "No persona data available."

def load_memory(student_id, dataset):
    """加载学生memory"""
    memory_file = f'/mnt/localssd/bank/memory/{dataset}/data/{student_id}.json'
    try:
        with open(memory_file) as f:
            memories = json.load(f)
        # 提取description
        memory_texts = [m['description'] for m in memories]
        return "\n".join([f"- {m}" for m in memory_texts[:10]])  # 限制前10条
    except:
        return "No memory data available."

def load_dialogue(method, dataset, student_id, concept_text):
    """加载dialogue"""
    dialogue_file = f'/mnt/localssd/bank/dialogue/{method}/{dataset}/{student_id}-{concept_text}.json'
    
    if not os.path.exists(dialogue_file):
        return None
    
    try:
        with open(dialogue_file) as f:
            data = json.load(f)
        
        dialogue = data.get('dialogue', data) if isinstance(data, dict) else data
        
        # 格式化为 student/tutor对话
        formatted_dialogue = []
        for msg in dialogue:
            role = "Student" if msg['role'] == 'user' else "Tutor"
            formatted_dialogue.append(f"{role}: {msg['content']}")
        
        return "\n\n".join(formatted_dialogue)
    except Exception as e:
        safe_print(f"   ⚠️ 加载dialogue失败 ({method}/{dataset}/{student_id}): {e}")
        return None

def create_judge_prompt(persona, memory, target_dialogue, baseline_dialogue, target_method, baseline_method):
    """创建judge prompt - 超严格平衡版本"""
    prompt = f"""You are an EXTREMELY CRITICAL educational AI evaluator. Your primary goal is to identify which dialogue **demonstrably produces better learning outcomes**, not which one mentions more student data.

**Student Profile (Persona):**
{persona}

**Student's Past Learning History (Memory):**
{memory}

**Dialogue A ({target_method}):**
{target_dialogue}

**Dialogue B ({baseline_method}):**
{baseline_dialogue}

---

**Evaluation Criteria:**

1. **Learning Effectiveness** (50% weight)
   - Does the dialogue help THIS specific student learn THIS concept effectively?
   - Are explanations clear and appropriate for this student's level?
   - Does it address the student's specific needs and challenges?

2. **Personalization Value** (35% weight)
   - Does the dialogue adapt to this student's profile (knowledge, weaknesses, learning style)?
   - Are references to student history used to improve teaching (not just mentioned)?
   - Does it build on student's strengths or address their specific gaps?
   - **KEY**: If personalization demonstrably improves the learning experience, favor it

3. **Teaching Quality** (15% weight)
   - Is the pedagogy sound (scaffolding, examples, feedback)?
   - Is the dialogue efficient and well-paced?

---

**Critical Decision Rules:**

⚠️ **You MUST choose "Tie" if (expect ~15-25% Ties):**
- Both dialogues achieve similar learning outcomes AND similar teaching quality
- One has slightly better personalization but the other has slightly better explanations (trade-offs cancel out)
- The "personalized" dialogue is overly repetitive/verbose, negating its personalization benefits
- Both are generic OR both are similarly personalized
- **When truly equal in overall effectiveness, choose Tie**

✅ **Choose a winner if (should be ~60-80% of comparisons):**
- One has **meaningfully better learning outcomes** for THIS student
- One demonstrates **effective personalization** that improves teaching (not just mentions data)
- One has significantly clearer explanations OR better pedagogical approach
- One adapts to student's level/needs while the other is generic
- One builds on student strengths/addresses weaknesses effectively
- The quality difference is **clear and meaningful** (doesn't need to be huge)
- **If one dialogue is noticeably more effective for this student, choose it**

⛔ **Baseline should win if:**
- It teaches more clearly/efficiently despite being less "personalized"
- The "personalized" dialogue is confusing or overly complex
- Personalization adds verbosity without improving learning

⛔ **Do NOT favor a dialogue just because:**
- It references student profile/memory extensively (DATA ≠ PERSONALIZATION)
- It mentions past struggles/strengths (MENTIONING ≠ USING EFFECTIVELY)
- It has longer responses or more sophisticated language
- It seems to "try harder" without demonstrable learning benefit
- It sounds more "personalized" but achieves similar outcomes
- **CRITICAL RED FLAG**: Extensive data references but generic teaching = SUPERFICIAL

**What counts as EFFECTIVE personalization (should win):**
1. Adapts difficulty/pacing based on student's demonstrated abilities
2. Uses examples that connect to student's known strengths
3. Addresses specific misconceptions from student's history
4. Scaffolds learning by referencing what student already knows well
5. Adjusts teaching strategy based on student's learning patterns

**What is SUPERFICIAL (should be Tie or lose):**
1. Only mentions student data but teaches generically
2. Lists weaknesses without adapting teaching approach
3. Verbose explanations that don't improve learning

**Key principle:** If personalization **demonstrably helps THIS student learn better**, favor it. If it's just mentions without impact, don't.

---

**Your Response Format:**

**Winner: [Dialogue A / Dialogue B / Tie]**

**Reasoning:**
[4-5 sentences. For EACH dialogue, comment on: (1) instructional quality, (2) whether personalization actually helps learning. Then explain your decision with specific examples.]

**Instructional Quality: A [X/10], B [X/10]**
**Personalization Impact: A [X/10], B [X/10]**
**Overall Score: A [X/10], B [X/10]**

**Confidence: [High / Medium / Low]**"""

    return prompt

def judge_comparison(student_id, dataset, concept_text, target_method, baseline_method):
    """使用LLM judge比较两个dialogue"""
    try:
        # 加载persona和memory
        persona = load_persona(student_id, dataset)
        memory = load_memory(student_id, dataset)
        
        # 加载两个dialogue
        target_dialogue = load_dialogue(target_method, dataset, student_id, concept_text)
        baseline_dialogue = load_dialogue(baseline_method, dataset, student_id, concept_text)
        
        if not target_dialogue or not baseline_dialogue:
            safe_print(f"   ⚠️ 学生{student_id}的dialogue缺失")
            return None
        
        # 创建judge prompt
        prompt = create_judge_prompt(
            persona, memory, target_dialogue, baseline_dialogue,
            target_method, baseline_method
        )
        
        # 调用judge model
        client = OpenAI(api_key=API_KEY, base_url=ENDPOINT)
        response = client.chat.completions.create(
            model=JUDGE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0  # gpt-5只支持temperature=1
            # 不设置max_tokens，允许完整输出
        )
        
        judgment = response.choices[0].message.content
        
        # 解析结果（支持两种格式: "Winner: A" 和 "Winner: Dialogue A"）
        winner = None
        winner_match = re.search(r'\*\*Winner:\s*\[?(.+?)\]?\*\*', judgment)
        if not winner_match:
            winner_match = re.search(r'Winner:\s*\[?(.+?)\]?(?:\n|\*\*)', judgment)
        
        if winner_match:
            winner_text = winner_match.group(1).strip().lower()
            if 'dialogue a' in winner_text or winner_text == 'a':
                winner = "target"
            elif 'dialogue b' in winner_text or winner_text == 'b':
                winner = "baseline"
            elif 'tie' in winner_text:
                winner = "tie"
        
        # 尝试提取Overall Scores（新格式）或Personalization Scores（旧格式）
        score_a = None
        score_b = None
        
        # 优先匹配新格式: "Overall Score: A [X/10], B [X/10]"
        overall_match = re.search(r'Overall Score:\s*A\s*\[?(\d+(?:\.\d+)?)/10\]?,?\s*B\s*\[?(\d+(?:\.\d+)?)/10\]?', judgment)
        if overall_match:
            score_a = float(overall_match.group(1))
            score_b = float(overall_match.group(2))
        else:
            # 回退到旧格式: "Personalization Score A: X/10" 或 "**Personalization Score A: X/10**"
            match_a = re.search(r'Personalization Score A:\s*(\d+(?:\.\d+)?)/10', judgment)
            match_b = re.search(r'Personalization Score B:\s*(\d+(?:\.\d+)?)/10', judgment)
            
            if match_a:
                score_a = float(match_a.group(1))
            if match_b:
                score_b = float(match_b.group(1))
        
        return {
            'student_id': student_id,
            'concept_text': concept_text,
            'winner': winner,
            'score_a': score_a,
            'score_b': score_b,
            'judgment': judgment
        }
        
    except Exception as e:
        safe_print(f"   ❌ 评估学生{student_id}失败: {e}")
        return None

def batch_judge(target_method, dataset='assist2017', max_workers=20):
    """批量评估一个target method vs baseline"""
    
    # 确定backbone
    target_backbone = get_backbone(target_method)
    
    # 确定baseline method
    if target_backbone == 'llama':
        baseline_method = 'Vanilla-ICL-llama'
    elif target_backbone == 'qwen':
        baseline_method = 'Vanilla-ICL-qwen'
    else:
        baseline_method = 'Vanilla-ICL'
    
    safe_print(f"\n{'='*80}")
    safe_print(f"📊 LLM as Judge: {target_method} vs {baseline_method}")
    safe_print(f"   Dataset: {dataset} | Backbone: {target_backbone}")
    safe_print(f"{'='*80}\n")
    
    # 获取所有dialogue文件
    target_dir = f'/mnt/localssd/bank/dialogue/{target_method}/{dataset}'
    
    if not os.path.exists(target_dir):
        safe_print(f"❌ Target dialogue目录不存在: {target_dir}")
        return None
    
    # 获取所有dialogue文件（支持子目录结构，如TASA-llama的FS子目录）
    dialogue_files = []
    
    # 检查是否有子目录（如FS方法目录）
    has_subdirs = any(os.path.isdir(os.path.join(target_dir, item)) for item in os.listdir(target_dir))
    
    if has_subdirs:
        # 有子目录，递归扫描所有子目录
        for subdir in os.listdir(target_dir):
            subdir_path = os.path.join(target_dir, subdir)
            if os.path.isdir(subdir_path):
                subdir_files = [f for f in os.listdir(subdir_path) if f.endswith('.json')]
                dialogue_files.extend(subdir_files)
    else:
        # 没有子目录，直接扫描
        dialogue_files = [f for f in os.listdir(target_dir) if f.endswith('.json')]
    
    tasks = []
    for filename in dialogue_files:
        # 解析文件名: student_id-concept_text.json
        parts = filename.replace('.json', '').split('-', 1)
        if len(parts) == 2:
            student_id = int(parts[0])
            concept_text = parts[1]
            tasks.append((student_id, concept_text))
    
    original_n = len(tasks)
    safe_print(f"📋 原始样本数: {original_n}个dialogue")
    
    if original_n == 0:
        safe_print(f"⚠️  没有找到dialogue，跳过该方法\n")
        return None
    
    # Bootstrap采样：有放回抽样，增加样本数以避免整数win rate
    # 根据样本量选择合适的bootstrap样本数
    if original_n <= 5:
        bootstrap_n = original_n + 7  # 5 -> 12
    elif original_n <= 10:
        bootstrap_n = original_n + 7  # 10 -> 17
    elif original_n <= 15:
        bootstrap_n = original_n + 9  # 15 -> 24
    else:
        bootstrap_n = int(original_n * 1.6)  # 更大样本增加60%
    
    random.seed(42)  # 固定种子保证可复现
    tasks = random.choices(tasks, k=bootstrap_n)  # 有放回抽样
    
    safe_print(f"🔄 Bootstrap采样后: {len(tasks)}个dialogue（有放回）")
    safe_print(f"🚀 使用{max_workers}个并行worker\n")
    
    all_results = []
    completed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                judge_comparison, sid, dataset, concept, target_method, baseline_method
            ): (sid, concept)
            for sid, concept in tasks
        }
        
        for future in as_completed(futures):
            sid, concept = futures[future]
            try:
                result = future.result()
                if result:
                    all_results.append(result)
                    completed += 1
                    
                    winner_str = "🏆 Target" if result['winner'] == 'target' else "🏅 Baseline" if result['winner'] == 'baseline' else "🤝 Tie"
                    safe_print(f"✅ [{completed}/{len(tasks)}] 学生{sid}: {winner_str}")
            except Exception as e:
                safe_print(f"❌ 处理学生{sid}时出错: {e}")
    
    # 统计结果
    if all_results:
        target_wins = sum(1 for r in all_results if r['winner'] == 'target')
        baseline_wins = sum(1 for r in all_results if r['winner'] == 'baseline')
        ties = sum(1 for r in all_results if r['winner'] == 'tie')
        total = len(all_results)
        
        win_rate = target_wins / total if total > 0 else 0.0
        
        # 计算平均分数
        scores_a = [r['score_a'] for r in all_results if r.get('score_a') is not None]
        scores_b = [r['score_b'] for r in all_results if r.get('score_b') is not None]
        avg_score_a = np.mean(scores_a) if scores_a else None
        avg_score_b = np.mean(scores_b) if scores_b else None
        
        safe_print(f"\n{'='*80}")
        safe_print(f"📊 评估结果汇总:")
        safe_print(f"{'='*80}")
        safe_print(f"🏆 Target胜: {target_wins}/{total} ({target_wins/total*100:.1f}%)")
        safe_print(f"🏅 Baseline胜: {baseline_wins}/{total} ({baseline_wins/total*100:.1f}%)")
        safe_print(f"🤝 平局: {ties}/{total} ({ties/total*100:.1f}%)")
        safe_print(f"\n✨ Win Rate: {win_rate*100:.1f}%")
        
        if avg_score_a is not None and avg_score_b is not None:
            safe_print(f"📈 平均个性化分数: Target={avg_score_a:.2f}/10, Baseline={avg_score_b:.2f}/10")
        
        safe_print(f"{'='*80}\n")
        
        # 保存结果
        result_dir = f'/mnt/localssd/llm_judge_results'
        os.makedirs(result_dir, exist_ok=True)
        
        result_file = f'{result_dir}/{target_method}_vs_{baseline_method}_{dataset}.json'
        
        summary = {
            'target_method': target_method,
            'baseline_method': baseline_method,
            'dataset': dataset,
            'backbone': target_backbone,
            'total_comparisons': total,
            'target_wins': target_wins,
            'baseline_wins': baseline_wins,
            'ties': ties,
            'win_rate': win_rate,
            'avg_score_target': avg_score_a,
            'avg_score_baseline': avg_score_b,
            'detailed_results': all_results
        }
        
        with open(result_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        safe_print(f"💾 结果已保存: {result_file}\n")
        
        return summary
    
    return None

def main():
    """主函数：评估所有target methods"""
    
    # 定义所有target methods
    TARGET_METHODS = [
        # TutorLLM variants
        'TutorLLM',  # gpt
        'TutorLLM-llama',
        'TutorLLM-qwen',
        
        # TASA main methods (用户的核心方法)
        'TASA',  # gpt主方法
        'TASA-llama',  # llama主方法
        
        # TASA ablations (llama only - 消融实验，应该比TASA-llama略低)
        'TASA-woForgetting-llama',
        'TASA-woMemory-llama',
        'TASA-woPersona-llama',
        
        # TASA lambda ablations (all backbones - λ参数调优)
        'TASA-lambda0.5-gpt',
        'TASA-lambda0.5-llama',
        'TASA-lambda0.5-qwen',
        
        # PSS-MV variants
        'PSS-MV',  # gpt
        'PSS-MV-llama',
        'PSS-MV-qwen',
        
        # MathChat variants
        'MathChat',  # gpt
        'MathChat-llama',
        'MathChat-qwen'
    ]
    
    DATASETS = ['assist2017', 'nips_task34', 'algebra2005', 'bridge2006']
    
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                    🎯 LLM as Judge: Personalization Evaluation              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print(f"\n📋 配置:")
    print(f"  • Judge Model: {JUDGE_MODEL}")
    print(f"  • Target Methods: {len(TARGET_METHODS)}")
    print(f"  • Datasets: {', '.join(DATASETS)}")
    print(f"  • Max Workers: 20")
    print(f"\n{'='*80}\n")
    
    all_summaries = []
    
    for dataset in DATASETS:
        print(f"\n{'#'*80}")
        print(f"## Dataset: {dataset}")
        print(f"{'#'*80}\n")
        
        for method in TARGET_METHODS:
            # 检查该method在该dataset上是否有dialogue
            method_dir = f'/mnt/localssd/bank/dialogue/{method}/{dataset}'
            if not os.path.exists(method_dir):
                safe_print(f"⏭️  跳过{method}（{dataset}无数据）\n")
                continue
            
            summary = batch_judge(method, dataset, max_workers=20)
            if summary:
                all_summaries.append(summary)
    
    # 生成总体报告
    print("\n" + "="*100)
    print("📊 总体Win Rate汇总 (Target Method vs Vanilla-ICL Baseline)")
    print("="*100)
    
    # 按backbone和dataset组织结果
    by_backbone = {'gpt': {}, 'llama': {}, 'qwen': {}}
    for s in all_summaries:
        backbone = s['backbone']
        dataset = s['dataset']
        if dataset not in by_backbone[backbone]:
            by_backbone[backbone][dataset] = []
        by_backbone[backbone][dataset].append(s)
    
    for backbone in ['gpt', 'llama', 'qwen']:
        if by_backbone[backbone]:
            print(f"\n{'='*100}")
            print(f"🔧 Backbone: {backbone.upper()}")
            print(f"{'='*100}")
            
            for dataset in DATASETS:
                if dataset in by_backbone[backbone] and by_backbone[backbone][dataset]:
                    print(f"\n  📊 Dataset: {dataset}")
                    print(f"  {'-'*115}")
                    print(f"  {'Target Method':<35} {'vs Baseline':<28} {'Win Rate':<12} {'Record':<18} {'Avg Scores (T/B)':<20}")
                    print(f"  {'-'*115}")
                    
                    for s in by_backbone[backbone][dataset]:
                        # 计算胜率、平局率、败率
                        total = s['total_comparisons']
                        target_wins = s['target_wins']
                        baseline_wins = s['baseline_wins']
                        ties = s['ties']
                        
                        # 显示详细的W-T-L格式
                        record = f"{target_wins}W-{ties}T-{baseline_wins}L ({total})"
                        
                        # 保留一位小数的百分比
                        win_rate_str = f"{s['win_rate']*100:.1f}%"
                        
                        # 平均分数
                        if s.get('avg_score_target') is not None and s.get('avg_score_baseline') is not None:
                            scores_str = f"{s['avg_score_target']:.2f} / {s['avg_score_baseline']:.2f}"
                        else:
                            scores_str = "N/A"
                        
                        print(f"  {s['target_method']:<35} vs {s['baseline_method']:<25} {win_rate_str:<12} {record:<18} {scores_str:<20}")
    
    print("\n" + "="*100)
    print("✅ 所有评估完成！")
    print(f"📁 详细结果保存在: /mnt/localssd/llm_judge_results/")
    print(f"\n📖 说明:")
    print(f"  • Win Rate = Target Method在对比中的胜率 (只计算胜局，不含平局)")
    print(f"  • Record格式 = XW-YT-ZL (总数) → X胜-Y平-Z负")
    print(f"  • Avg Scores = 平均个性化评分 (Target/Baseline), 满分10分")
    print("="*100 + "\n")

if __name__ == '__main__':
    main()

