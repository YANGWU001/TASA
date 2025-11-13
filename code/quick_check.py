import json
import os

print("快速检查 Persona 状态\n")

data_dir = '/mnt/localssd/bank/persona/nips_task34/data'

# 检查前20个学生
correct = 0
numeric = 0

for sid in range(20):
    filepath = f'{data_dir}/{sid}.json'
    if os.path.exists(filepath):
        with open(filepath) as f:
            personas = json.load(f)
        
        if personas:
            concept_text = personas[0]['concept_text']
            is_numeric = concept_text.strip().isdigit()
            
            if is_numeric:
                numeric += 1
                if sid < 10:
                    print(f"学生 {sid}: ❌ '{concept_text}'")
            else:
                correct += 1
                if sid < 10:
                    print(f"学生 {sid}: ✅ '{concept_text[:40]}...'")

print(f"\n统计 (前20个学生):")
print(f"  ✅ 正确: {correct}/20")
print(f"  ❌ 数字: {numeric}/20")

if numeric > 0:
    print(f"\n⚠️  需要处理 {numeric} 个学生")
    print("   运行: bash /mnt/localssd/run_fix_persona.sh")


