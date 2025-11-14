"""
TASA Method Configuration - Llama Backbone
Tutoring with Adaptive Student Assessment
"""

# API配置
ENDPOINT = ""  # Your Llama endpoint
#GPT_ENDPOINT = ""  # GPT endpoint (for Student/Grader/Rewriter)
API_KEY = ""  # Your API key

# 模型配置
TUTOR_MODEL = "llama-3.1-8B-Instruct"
REWRITE_MODEL = "gpt-oss-120b"    # Mastery重写模型
STUDENT_MODEL = "gpt-oss-120b"    # 学生role-play模型
GRADER_MODEL = "gpt-4o-mini"      # 批改模型

# 生成参数
TUTOR_TEMPERATURE = 0.7           # Tutor生成温度
REWRITE_TEMPERATURE = 0.5         # Rewrite温度
STUDENT_TEMPERATURE = 1.0         # Student温度（高一些，模拟真实学生）
GRADER_TEMPERATURE = 0.3          # Grader温度（低一些，保持一致性）

# RAG配置
LAMBDA_WEIGHT = 0.5               # description和keywords的权重平衡
TOP_K_RETRIEVE = 10               # 初始检索top-K
TOP_K_RERANK = 3                  # 重排后保留top-K
EMBEDDING_MODEL = "BAAI/bge-m3"   # Embedding模型
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"  # Reranker模型

# 对话配置
NUM_TUTORING_ROUNDS = 10          # 教学轮数（生成10次回复）
MAX_TOKENS_TUTOR = 1000           # Tutor回复最大token数
MAX_TOKENS_STUDENT = 500          # Student回答最大token数

# 文件路径配置
DIALOGUE_DIR = "/mnt/localssd/bank/dialogue/TASA"
PERSONA_DIR = "/mnt/localssd/bank/persona"
MEMORY_DIR = "/mnt/localssd/bank/memory"
SESSION_DIR = "/mnt/localssd/bank/session"
EVALUATION_DIR = "/mnt/localssd/bank/evaluation_results"

# Forgetting curve配置
# Forgetting Score Method: "history", "lpkt", "dkt", "akt", "simplekt", "simple_time"
FORGETTING_SCORE_METHOD = "dkt"

FORGETTING_LEVELS = {
    "high": "high (significant knowledge loss)",      # F_c(t) > 0.7
    "moderate": "moderate (some knowledge retained)", # 0.3 < F_c(t) <= 0.7
    "low": "low (most knowledge retained)"           # F_c(t) <= 0.3
}

def get_forgetting_level(forgetting_score: float) -> str:
    """根据遗忘分数返回遗忘水平"""
    if forgetting_score > 0.7:
        return "high"
    elif forgetting_score > 0.3:
        return "moderate"
    else:
        return "low"

