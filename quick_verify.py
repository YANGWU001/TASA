import json
import os

print("验证 NIPS_TASK34 学生 0-5 的匹配度\n")

for sid in range(6):
    persona_file = f'/mnt/localssd/bank/persona/nips_task34/data/{sid}.json'
    memory_file = f'/mnt/localssd/bank/memory/nips_task34/data/{sid}.json'
    
    try:
        with open(persona_file) as f:
            personas = json.load(f)
        with open(memory_file) as f:
            memories = json.load(f)
        
        persona_concepts = set(p['concept_id'] for p in personas)
        memory_concepts = set(m['concept_id'] for m in memories)
        
        match = len(persona_concepts & memory_concepts)
        total = len(persona_concepts)
        
        print(f"学生 {sid}:")
        print(f"  Persona: {len(personas)} 条记录, {len(persona_concepts)} 个 concepts")
        print(f"  Memory:  {len(memories)} 条记录, {len(memory_concepts)} 个 concepts")
        print(f"  匹配: {match}/{total} ({match/total*100:.1f}%)")
        
        # 检查 concept_text 是否正确（不是数字）
        sample_p = personas[0] if personas else {}
        sample_m = memories[0] if memories else {}
        p_text = sample_p.get('concept_text', '')
        m_text = sample_m.get('concept_text', '')
        
        print(f"  Persona concept_text: '{p_text[:50]}...'")
        print(f"  Memory concept_text:  '{m_text[:50]}...'")
        
        if p_text.isdigit() or m_text.isdigit():
            print(f"  ⚠️  发现数字格式的 concept_text!")
        
        if match == total:
            print(f"  ✅ 完全匹配")
        else:
            only_p = persona_concepts - memory_concepts
            only_m = memory_concepts - persona_concepts
            if only_p:
                print(f"  ⚠️  只在 Persona: {sorted(list(only_p))[:5]}")
            if only_m:
                print(f"  ⚠️  只在 Memory: {sorted(list(only_m))[:5]}")
        
        print()
    except Exception as e:
        print(f"学生 {sid}: 错误 - {e}\n")

