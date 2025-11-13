"""
Role-Play评估系统配置文件
请填写你的API凭证
"""

# LLM API配置
# 从 use_gpt/bear/example.py 中获取你的凭证
# endpoint将根据你是在公司网络还是pluto实例上而不同
# 使用Slack命令 /get-llm-cred 获取key

ENDPOINT = "http://pluto-prod-hawang-llm-proxy-9qtfav-0:4000"
API_KEY = "sk-g-wO3D7N2V-VvcfhfqG9ww"

# 模型配置
STUDENT_MODEL = "gpt-oss-120b"  # Role-play学生的模型
GRADER_MODEL = "gpt-4o-mini"     # 批改作业的模型

# 可用模型列表:
# - gpt-oss-120b (推荐用于role-play，更自然)
# - gpt-oss-20b
# - gpt-4o-mini (推荐用于grading，更准确)
# - gpt-4o
# - gpt-5
# - claude-sonnet-4
# - deepseek-r1

# 生成参数
STUDENT_TEMPERATURE = 1.0  # 学生回答的温度（1.0更随机，更容易犯错）
GRADER_TEMPERATURE = 0.3   # 批改的温度（0.3更一致，更客观）

# 速率限制
SLEEP_BETWEEN_QUESTIONS = 0.5  # 问题之间的等待时间（秒）

# 路径配置
BASE_DIR = '/mnt/localssd'
BANK_DIR = f'{BASE_DIR}/bank'

