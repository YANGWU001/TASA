#!/usr/bin/env python3
"""
环境测试脚本 - 验证TASA环境是否正确配置
"""

import sys
import os

def print_header(title):
    """打印标题"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def check_package(name, import_cmd, version_cmd=None):
    """检查包是否可以导入"""
    try:
        exec(import_cmd)
        if version_cmd:
            version = eval(version_cmd)
            print(f"  ✅ {name}: {version}")
        else:
            print(f"  ✅ {name}: Available")
        return True
    except Exception as e:
        print(f"  ❌ {name}: {str(e)[:60]}")
        return False

def test_bge_model():
    """测试BGE模型"""
    print_header("🧪 测试BGE Embeddings")
    
    try:
        from FlagEmbedding import BGEM3FlagModel
        print("  📥 加载BGE-M3模型 (首次运行会下载，需要几分钟)...")
        
        model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
        
        # 测试embedding
        texts = ["Hello world", "Test embedding"]
        result = model.encode(texts, batch_size=2)
        
        print(f"  ✅ BGE-M3模型工作正常")
        print(f"     输入: {len(texts)} 个文本")
        print(f"     输出shape: {result['dense_vecs'].shape}")
        print(f"     向量维度: {result['dense_vecs'].shape[1]}")
        return True
    except Exception as e:
        print(f"  ❌ BGE模型测试失败: {e}")
        return False

def test_llm_client():
    """测试LLM客户端"""
    print_header("🤖 测试LLM客户端")
    
    try:
        from llm_client_unified import UnifiedLLMClient
        
        print("  ✅ UnifiedLLMClient导入成功")
        print("  ℹ️  注意: 实际API调用需要配置正确的endpoint")
        return True
    except Exception as e:
        print(f"  ❌ LLM客户端测试失败: {e}")
        return False

def test_pykt():
    """测试pykt-toolkit"""
    print_header("📚 测试PyKT (知识追踪)")
    
    try:
        from pykt.models import LPKT, DKT, AKT, SimpleKT
        
        print("  ✅ LPKT: Available")
        print("  ✅ DKT: Available")
        print("  ✅ AKT: Available")
        print("  ✅ SimpleKT: Available")
        return True
    except Exception as e:
        print(f"  ❌ PyKT测试失败: {e}")
        return False

def test_directories():
    """测试目录结构"""
    print_header("📂 检查目录结构")
    
    required_dirs = [
        'bank/persona',
        'bank/memory',
        'bank/session',
        'bank/dialogue',
        'bank/evaluation_results',
        'logs',
        'data'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        full_path = os.path.join('/mnt/localssd', dir_path)
        if os.path.exists(full_path):
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path} (不存在)")
            all_exist = False
    
    return all_exist

def main():
    """主测试函数"""
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "🧪 TASA 环境测试" + " "*20 + "║")
    print("╚" + "="*78 + "╝")
    
    results = {}
    
    # ============================================================================
    # 基础信息
    # ============================================================================
    print_header("ℹ️  系统信息")
    print(f"  Python版本: {sys.version.split()[0]}")
    print(f"  Python路径: {sys.executable}")
    
    # ============================================================================
    # 核心包检查
    # ============================================================================
    print_header("📦 核心包检查")
    
    results['torch'] = check_package(
        "PyTorch",
        "import torch",
        "torch.__version__"
    )
    
    if results['torch']:
        import torch
        print(f"     CUDA可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"     GPU: {torch.cuda.get_device_name(0)}")
            print(f"     CUDA版本: {torch.version.cuda}")
    
    results['transformers'] = check_package(
        "Transformers",
        "import transformers",
        "transformers.__version__"
    )
    
    results['numpy'] = check_package(
        "NumPy",
        "import numpy as np",
        "np.__version__"
    )
    
    results['pandas'] = check_package(
        "Pandas",
        "import pandas as pd",
        "pd.__version__"
    )
    
    results['openai'] = check_package(
        "OpenAI",
        "import openai",
        "openai.__version__"
    )
    
    results['httpx'] = check_package(
        "httpx",
        "import httpx",
        "httpx.__version__"
    )
    
    results['flag_embedding'] = check_package(
        "FlagEmbedding",
        "from FlagEmbedding import BGEM3FlagModel",
        None
    )
    
    results['sentence_transformers'] = check_package(
        "Sentence-Transformers",
        "import sentence_transformers",
        "sentence_transformers.__version__"
    )
    
    results['sklearn'] = check_package(
        "Scikit-learn",
        "import sklearn",
        "sklearn.__version__"
    )
    
    results['tqdm'] = check_package(
        "tqdm",
        "import tqdm",
        "tqdm.__version__"
    )
    
    # ============================================================================
    # PyKT测试
    # ============================================================================
    results['pykt'] = test_pykt()
    
    # ============================================================================
    # BGE模型测试 (可选)
    # ============================================================================
    print_header("⚠️  BGE模型测试 (可选)")
    print("  是否测试BGE模型? (首次会下载约6GB模型)")
    try:
        user_input = input("  输入 'y' 继续，其他键跳过: ").strip().lower()
        if user_input == 'y':
            results['bge'] = test_bge_model()
        else:
            print("  ⏭️  跳过BGE模型测试")
            results['bge'] = None
    except:
        print("  ⏭️  跳过BGE模型测试 (非交互模式)")
        results['bge'] = None
    
    # ============================================================================
    # LLM客户端测试
    # ============================================================================
    results['llm_client'] = test_llm_client()
    
    # ============================================================================
    # 目录结构测试
    # ============================================================================
    results['directories'] = test_directories()
    
    # ============================================================================
    # 汇总结果
    # ============================================================================
    print_header("📊 测试汇总")
    
    # 统计结果
    critical_checks = ['torch', 'transformers', 'numpy', 'openai', 'httpx', 
                       'flag_embedding', 'pykt', 'llm_client']
    
    passed = sum(1 for key in critical_checks if results.get(key, False))
    total = len(critical_checks)
    
    print(f"\n  关键检查: {passed}/{total} 通过")
    
    if passed == total:
        print("\n  ✅ 所有关键检查通过！环境配置正确。")
        exit_code = 0
    else:
        print("\n  ⚠️  部分检查失败，请检查上述错误信息。")
        print("  💡 提示: 运行 'pip install -r requirements.txt' 安装缺失的包")
        exit_code = 1
    
    # 额外提示
    print_header("📝 下一步")
    print("  1. 配置API endpoints (修改tasa_config_*.py文件)")
    print("  2. 准备学生银行数据")
    print("  3. 运行baseline评估:")
    print("     python baseline_evaluation_conservative.py --help")
    print("\n  详细文档请查看: SETUP.md")
    
    print("\n" + "="*80 + "\n")
    
    return exit_code

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

