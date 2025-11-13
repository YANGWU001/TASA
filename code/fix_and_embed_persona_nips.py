#!/usr/bin/env python3
"""
修复 nips_task34 persona 文件中的 concept 映射，并重新生成 embeddings
只处理那些 concept_text 还是数字ID的文件
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import torch
try:
    from FlagEmbedding import BGEM3FlagModel
except ImportError:
    from FlagEmbedding import FlagModel as BGEM3FlagModel
from tqdm import tqdm
import os

def load_subject_mapping():
    """加载 subject metadata 并创建 SubjectId -> Name 的映射"""
    metadata_file = '/mnt/localssd/pykt-toolkit/data/nips_task34/metadata/subject_metadata.csv'
    df = pd.read_csv(metadata_file)
    
    # 创建 SubjectId -> Name 的映射
    subject_mapping = {}
    for _, row in df.iterrows():
        subject_id = int(row['SubjectId'])
        name = str(row['Name']).strip()
        subject_mapping[subject_id] = name
    
    print(f"📚 加载了 {len(subject_mapping)} 个 subject 映射")
    return subject_mapping

def init_bge_model():
    """初始化BGE模型"""
    print("🔧 初始化 BGE 模型...")
    bge_model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
    print("✅ BGE 模型加载完成")
    return bge_model

def find_files_needing_update(persona_dir):
    """找到所有需要更新的文件（concept_text还是数字的）"""
    files = sorted(list(Path(persona_dir).glob('*.json')))
    needs_update = []
    
    print(f"🔍 扫描 {len(files)} 个文件...")
    
    for f in tqdm(files, desc="扫描文件"):
        try:
            with open(f) as fp:
                data = json.load(fp)
            
            if data and data[0].get('concept_text', '').isdigit():
                needs_update.append(f)
        except Exception as e:
            print(f"  ⚠️ 读取文件 {f.name} 失败: {e}")
    
    return needs_update

def update_persona_file(filepath, subject_mapping, bge_model):
    """更新单个persona文件并生成embeddings"""
    try:
        with open(filepath, 'r') as f:
            personas = json.load(f)
        
        updated = False
        descriptions = []
        keywords_list = []
        
        for persona in personas:
            old_text = persona['concept_text']
            
            # 如果是数字，则转换为实际的 subject 名称
            try:
                concept_id = int(old_text)
                if concept_id in subject_mapping:
                    new_text = subject_mapping[concept_id]
                    persona['concept_text'] = new_text
                    persona['keywords'] = new_text
                    
                    # 更新 description 中的引用
                    old_desc = persona['description']
                    new_desc = old_desc.replace(f"'{old_text}'", f"'{new_text}'")
                    persona['description'] = new_desc
                    
                    updated = True
                else:
                    # 如果找不到映射，保持原样但记录
                    pass
            except (ValueError, TypeError):
                # 如果不是数字，跳过
                pass
            
            descriptions.append(persona['description'])
            keywords_list.append(persona['keywords'])
        
        if updated:
            # 生成 embeddings
            desc_embeddings = bge_model.encode(descriptions)
            kw_embeddings = bge_model.encode(keywords_list)
            
            # 保存更新后的persona文件（不包含embeddings）
            with open(filepath, 'w') as f:
                json.dump(personas, f, indent=2)
            
            # 保存 embeddings
            student_id = filepath.stem
            embeddings_dir = filepath.parent.parent / 'embeddings'
            embeddings_dir.mkdir(exist_ok=True)
            
            # 保存 description embeddings
            desc_emb_file = embeddings_dir / f"{student_id}_desc.npy"
            np.save(desc_emb_file, desc_embeddings)
            
            # 保存 keywords embeddings
            kw_emb_file = embeddings_dir / f"{student_id}_keywords.npy"
            np.save(kw_emb_file, kw_embeddings)
            
            return True, None
        else:
            return False, "没有需要更新的内容"
    
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 80)
    print("修复并重新生成 NIPS_TASK34 Persona Embeddings")
    print("=" * 80)
    
    # 1. 加载 subject mapping
    subject_mapping = load_subject_mapping()
    
    # 2. 初始化BGE模型
    bge_model = init_bge_model()
    
    # 3. 找到需要更新的文件
    persona_dir = Path('/mnt/localssd/bank/persona/nips_task34/data')
    files_to_update = find_files_needing_update(persona_dir)
    
    print(f"\n📝 找到 {len(files_to_update)} 个需要更新的文件")
    
    if not files_to_update:
        print("✅ 所有文件都已经是正确的格式！")
        return
    
    # 4. 更新文件并生成embeddings
    print(f"\n🔄 开始更新文件并生成embeddings...")
    
    updated_count = 0
    error_count = 0
    errors = []
    
    for filepath in tqdm(files_to_update, desc="处理文件"):
        success, error_msg = update_persona_file(filepath, subject_mapping, bge_model)
        
        if success:
            updated_count += 1
        else:
            error_count += 1
            if error_msg and error_msg != "没有需要更新的内容":
                errors.append((filepath.name, error_msg))
    
    # 5. 报告结果
    print(f"\n{'=' * 80}")
    print(f"✅ 处理完成！")
    print(f"{'=' * 80}")
    print(f"  成功更新: {updated_count} 个文件")
    print(f"  失败: {error_count} 个文件")
    
    if errors:
        print(f"\n⚠️ 错误详情（前10个）:")
        for fname, error in errors[:10]:
            print(f"  - {fname}: {error}")
    
    # 6. 验证一些文件
    print(f"\n{'=' * 80}")
    print(f"验证修复效果")
    print(f"{'=' * 80}")
    
    sample_files = files_to_update[:5] if len(files_to_update) >= 5 else files_to_update
    for filepath in sample_files:
        with open(filepath) as f:
            data = json.load(f)
        
        student_id = filepath.stem
        print(f"\n学生 {student_id}:")
        
        # 检查是否还有数字 concept_text
        numeric = [p['concept_text'] for p in data if p['concept_text'].isdigit()]
        if numeric:
            print(f"  ⚠️ 仍有数字 concept: {numeric[:3]}")
        else:
            print(f"  ✅ 所有 concept 都已转换")
        
        # 显示前3个concept
        for i, p in enumerate(data[:3]):
            print(f"    {i+1}. [{p['concept_id']}] {p['concept_text']}")
        
        # 检查embeddings
        emb_dir = filepath.parent.parent / 'embeddings'
        desc_emb = emb_dir / f"{student_id}_desc.npy"
        kw_emb = emb_dir / f"{student_id}_keywords.npy"
        
        if desc_emb.exists() and kw_emb.exists():
            desc_data = np.load(desc_emb)
            kw_data = np.load(kw_emb)
            print(f"  📊 Embeddings: desc={desc_data.shape}, keywords={kw_data.shape}")
        else:
            print(f"  ⚠️ Embeddings文件未找到")

if __name__ == '__main__':
    main()

