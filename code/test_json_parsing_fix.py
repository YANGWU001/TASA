#!/usr/bin/env python
"""测试JSON解析修复是否有效"""

import json

# 模拟GPT-4o返回的内容（带markdown代码块）
content_with_markdown = '''```json
{
  "memories": [
    {"index": 1, "description": "The student successfully understood the concept of addition and subtraction."},
    {"index": 2, "description": "The student struggled with the concept of area, perimeter, and volume."},
    {"index": 3, "description": "The student demonstrated a correct understanding of basic geometry concepts."}
  ]
}
```'''

print("=" * 80)
print("测试JSON解析修复")
print("=" * 80)

print("\n原始内容（包含markdown）:")
print(content_with_markdown[:100] + "...")

# 应用修复
content = content_with_markdown.strip()
if content.startswith("```json"):
    content = content[7:]  # 移除 ```json
if content.startswith("```"):
    content = content[3:]  # 移除 ```
if content.endswith("```"):
    content = content[:-3]  # 移除结尾的 ```
content = content.strip()

print("\n清理后的内容:")
print(content[:100] + "...")

# 尝试解析
try:
    result = json.loads(content)
    print("\n✅ JSON解析成功！")
    print(f"包含 {len(result.get('memories', []))} 条memory:")
    for mem in result['memories']:
        print(f"  - Index {mem['index']}: {mem['description'][:50]}...")
except json.JSONDecodeError as e:
    print(f"\n❌ JSON解析失败: {e}")

print("\n" + "=" * 80)

