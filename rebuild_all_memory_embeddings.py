#!/usr/bin/env python3
"""
为所有数据集重建memory embeddings
"""
import subprocess
import time

DATASETS = ['assist2017', 'algebra2005', 'bridge2006', 'nips_task34']

def rebuild_embeddings_for_dataset(dataset):
    """为单个数据集重建embeddings"""
    print(f"\n{'='*100}")
    print(f"🔄 重建 {dataset} 的 Memory Embeddings")
    print(f"{'='*100}\n")
    
    start_time = time.time()
    
    cmd = [
        '/opt/venv/bin/python3',
        '/mnt/localssd/recompute_embeddings.py',
        '--dataset', dataset,
        '--type', 'memory'
    ]
    
    result = subprocess.run(cmd, capture_output=False)
    
    elapsed = time.time() - start_time
    
    if result.returncode == 0:
        print(f"\n✅ {dataset} 完成 (耗时: {elapsed/60:.1f}分钟)\n")
        return True
    else:
        print(f"\n❌ {dataset} 失败\n")
        return False

def main():
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║              🔄 重建所有数据集的Memory Embeddings (BGE-M3)                  ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    print("📊 任务列表:")
    for i, dataset in enumerate(DATASETS, 1):
        print(f"  {i}. {dataset}")
    print()
    
    total_start = time.time()
    success_count = 0
    
    for dataset in DATASETS:
        if rebuild_embeddings_for_dataset(dataset):
            success_count += 1
    
    total_elapsed = time.time() - total_start
    
    print("\n" + "="*100)
    print("📊 最终统计")
    print("="*100)
    print(f"✅ 成功: {success_count}/{len(DATASETS)}")
    print(f"⏱️  总耗时: {total_elapsed/60:.1f}分钟")
    print("="*100)

if __name__ == '__main__':
    main()
