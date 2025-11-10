import os
import json
from tqdm import tqdm

data_dir = '/mnt/localssd/bank/persona/nips_task34/data'
files = sorted([f for f in os.listdir(data_dir) if f.endswith('.json')])

print(f"清理 {len(files)} 个 persona 文件...")
cleaned = 0

for filename in tqdm(files):
    filepath = os.path.join(data_dir, filename)
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        has_embedding = False
        for item in data:
            if 'embedding' in item:
                del item['embedding']
                has_embedding = True
        
        if has_embedding:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            cleaned += 1
    except:
        pass

print(f"完成！清理了 {cleaned} 个文件")

