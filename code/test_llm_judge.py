#!/usr/bin/env python3
"""
测试LLM as Judge - 仅测试1个学生
"""

import sys
sys.path.append('/mnt/localssd')
from llm_as_judge_personalization import judge_comparison, load_persona, load_memory, load_dialogue

# 测试参数
STUDENT_ID = 170
DATASET = 'assist2017'
CONCEPT_TEXT = 'fraction-multiplication'
TARGET_METHOD = 'Vanilla-ICL-qwen'
BASELINE_METHOD = 'Vanilla-ICL'

print("="*80)
print("🧪 测试LLM as Judge")
print("="*80)
print(f"\n📋 测试配置:")
print(f"  • 学生ID: {STUDENT_ID}")
print(f"  • Dataset: {DATASET}")
print(f"  • Concept: {CONCEPT_TEXT}")
print(f"  • Target: {TARGET_METHOD}")
print(f"  • Baseline: {BASELINE_METHOD}")
print("\n" + "="*80 + "\n")

# 加载数据
print("📥 加载数据...")
persona = load_persona(STUDENT_ID, DATASET)
memory = load_memory(STUDENT_ID, DATASET)
target_dialogue = load_dialogue(TARGET_METHOD, DATASET, STUDENT_ID, CONCEPT_TEXT)
baseline_dialogue = load_dialogue(BASELINE_METHOD, DATASET, STUDENT_ID, CONCEPT_TEXT)

print(f"✅ Persona长度: {len(persona)} chars")
print(f"✅ Memory长度: {len(memory)} chars")
print(f"✅ Target dialogue长度: {len(target_dialogue) if target_dialogue else 0} chars")
print(f"✅ Baseline dialogue长度: {len(baseline_dialogue) if baseline_dialogue else 0} chars")

if not target_dialogue or not baseline_dialogue:
    print("\n❌ Dialogue数据缺失，无法测试")
    sys.exit(1)

print("\n🚀 开始LLM Judge评估...")
result = judge_comparison(STUDENT_ID, DATASET, CONCEPT_TEXT, TARGET_METHOD, BASELINE_METHOD)

if result:
    print("\n" + "="*80)
    print("📊 评估结果:")
    print("="*80)
    print(f"\n🏆 Winner: {result['winner']}")
    print(f"\n📝 完整判断:\n")
    print(result['judgment'])
    print("\n" + "="*80)
    print("✅ 测试成功！")
else:
    print("\n❌ 评估失败")

