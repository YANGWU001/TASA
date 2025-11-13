#!/usr/bin/env python3
"""测试改进后的prompt"""

from student_roleplay_evaluation import build_student_system_prompt, load_session

# 加载学生1的session
session = load_session('/mnt/localssd/bank/session/assist2017/1.json')

# 生成新的system prompt
prompt = build_student_system_prompt(session)

print('='*80)
print('改进后的System Prompt')
print('='*80)
print(prompt)
print()
print('='*80)
print('关键改进点:')
print('='*80)
print('✅ 1. 明确指出期望正确数量: 约2-3题/10题')
print('✅ 2. 明确指出期望错误数量: 约7-8题/10题')
print('✅ 3. 强调"DO NOT perform better than 27%"')
print('✅ 4. 列出具体的错误策略')
print('✅ 5. 强调"STRUGGLING student"')
print('✅ 6. 温度提高到1.0（更随机，更容易犯错）')
