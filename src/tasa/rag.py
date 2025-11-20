"""
TASA RAG模块
从persona和memory中检索相关信息，并进行重排
"""

import json
import numpy as np
from typing import List, Dict, Tuple
from FlagEmbedding import BGEM3FlagModel, FlagReranker
import os

from tasa_config import *

class TASARAG:
    def __init__(self):
        """初始化RAG模块"""
        print("🔧 初始化TASA RAG模块...")
        
        # 加载embedding模型 (使用GPU)
        print(f"   加载Embedding模型: {EMBEDDING_MODEL}")
        self.embed_model = BGEM3FlagModel(EMBEDDING_MODEL, use_fp16=True, device='cuda')
        
        # 加载reranker模型 (使用GPU)
        print(f"   加载Reranker模型: {RERANKER_MODEL}")
        self.reranker = FlagReranker(RERANKER_MODEL, use_fp16=True, device='cuda')
        
        print("✅ TASA RAG模块初始化完成 (GPU加速)")
    
    def load_student_data(self, student_id: int, dataset: str, concept_text: str) -> Tuple[List[Dict], List[Dict]]:
        """
        加载学生的persona和memory数据
        
        Returns:
            persona_items: List of {description, keywords, description_emb, keywords_emb, stats, ...}
            memory_items: List of {description, keywords, description_emb, keywords_emb, timestamp, ...}
        """
        # 加载persona
        persona_file = f"{PERSONA_DIR}/{dataset}/data/{student_id}.json"
        with open(persona_file) as f:
            persona_data = json.load(f)
        
        # 加载persona embeddings
        persona_desc_emb_file = f"{PERSONA_DIR}/{dataset}/embeddings/{student_id}_description.npz"
        persona_kw_emb_file = f"{PERSONA_DIR}/{dataset}/embeddings/{student_id}_keywords.npz"
        
        persona_desc_embs = np.load(persona_desc_emb_file, allow_pickle=True)['embeddings']
        persona_kw_embs = np.load(persona_kw_emb_file, allow_pickle=True)['embeddings']
        
        # 组装persona items
        persona_items = []
        for i, concept_data in enumerate(persona_data):
            if concept_data['concept_text'] == concept_text:
                # 只加载相关concept的persona（但实际上我们可能想要所有相关的）
                pass
            persona_items.append({
                'concept_text': concept_data['concept_text'],
                'description': concept_data['description'],
                'keywords': concept_data['keywords'],
                'description_emb': persona_desc_embs[i],
                'keywords_emb': persona_kw_embs[i],
                'stats': concept_data['stats']
            })
        
        # 加载memory
        memory_file = f"{MEMORY_DIR}/{dataset}/data/{student_id}.json"
        with open(memory_file) as f:
            memory_data = json.load(f)
        
        # 加载memory embeddings
        memory_desc_emb_file = f"{MEMORY_DIR}/{dataset}/embeddings/{student_id}_description.npz"
        memory_desc_embs = np.load(memory_desc_emb_file)['embeddings']
        
        # 注意：memory可能没有keywords embeddings，我们只用description
        memory_items = []
        for i, mem in enumerate(memory_data):
            if mem['concept_text'] == concept_text:
                # 只保留目标concept的memory
                memory_items.append({
                    'concept_text': mem['concept_text'],
                    'description': mem['description'],
                    'keywords': mem.get('keywords', mem['description']),  # 如果没有keywords用description
                    'description_emb': memory_desc_embs[i],
                    'keywords_emb': memory_desc_embs[i],  # memory可能没有单独的keywords embedding
                    'timestamp': mem.get('timestamp', 0),
                    'response': mem.get('response', 0)
                })
        
        return persona_items, memory_items
    
    def compute_similarity(self, query_emb: np.ndarray, desc_emb: np.ndarray, 
                          kw_emb: np.ndarray, lambda_weight: float = LAMBDA_WEIGHT) -> float:
        """
        计算相似度: total_score = lambda * sim(query, desc) + (1-lambda) * sim(query, kw)
        """
        # 余弦相似度
        sim_desc = np.dot(query_emb, desc_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(desc_emb))
        sim_kw = np.dot(query_emb, kw_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(kw_emb))
        
        total_score = lambda_weight * sim_desc + (1 - lambda_weight) * sim_kw
        return float(total_score)
    
    def retrieve_and_rerank(self, query: str, student_id: int, dataset: str, 
                           concept_text: str) -> Tuple[List[Dict], List[Dict]]:
        """
        RAG检索并重排
        
        Returns:
            top_persona: Top 3 persona items
            top_memory: Top 3 memory items
        """
        # 1. 编码query
        query_emb = self.embed_model.encode(query)['dense_vecs']
        
        # 2. 加载学生数据
        persona_items, memory_items = self.load_student_data(student_id, dataset, concept_text)
        
        # 3. 计算persona相似度并排序
        persona_scores = []
        for item in persona_items:
            score = self.compute_similarity(query_emb, item['description_emb'], item['keywords_emb'])
            persona_scores.append((score, item))
        
        # 取top-K
        persona_scores.sort(key=lambda x: x[0], reverse=True)
        top_k_persona = persona_scores[:TOP_K_RETRIEVE]
        
        # 4. 计算memory相似度并排序
        memory_scores = []
        for item in memory_items:
            score = self.compute_similarity(query_emb, item['description_emb'], item['keywords_emb'])
            memory_scores.append((score, item))
        
        memory_scores.sort(key=lambda x: x[0], reverse=True)
        top_k_memory = memory_scores[:TOP_K_RETRIEVE]
        
        # 5. 使用reranker精排persona（只用description）
        if len(top_k_persona) > 0:
            persona_pairs = [[query, item['description']] for _, item in top_k_persona]
            persona_rerank_scores = self.reranker.compute_score(persona_pairs, normalize=True)
            
            # 重新排序
            persona_reranked = list(zip(persona_rerank_scores, [item for _, item in top_k_persona]))
            persona_reranked.sort(key=lambda x: x[0], reverse=True)
            top_persona = [item for _, item in persona_reranked[:TOP_K_RERANK]]
        else:
            top_persona = []
        
        # 6. 使用reranker精排memory
        if len(top_k_memory) > 0:
            memory_pairs = [[query, item['description']] for _, item in top_k_memory]
            memory_rerank_scores = self.reranker.compute_score(memory_pairs, normalize=True)
            
            # 重新排序
            memory_reranked = list(zip(memory_rerank_scores, [item for _, item in top_k_memory]))
            memory_reranked.sort(key=lambda x: x[0], reverse=True)
            top_memory = [item for _, item in memory_reranked[:TOP_K_RERANK]]
        else:
            top_memory = []
        
        return top_persona, top_memory

# 测试函数
if __name__ == "__main__":
    rag = TASARAG()
    
    # 测试检索
    query = "I want to learn about rotations in geometry"
    top_persona, top_memory = rag.retrieve_and_rerank(
        query=query,
        student_id=1,
        dataset="assist2017",
        concept_text="transformations-rotations"
    )
    
    print(f"\n查询: {query}")
    print(f"\nTop 3 Persona:")
    for i, item in enumerate(top_persona, 1):
        print(f"{i}. {item['description']}")
    
    print(f"\nTop 3 Memory:")
    for i, item in enumerate(top_memory, 1):
        print(f"{i}. {item['description']}")

