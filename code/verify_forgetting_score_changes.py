#!/usr/bin/env python3
"""
验证Forgetting Score的修改是否正确
"""
import json
import sys

def test_forgetting_score_extraction():
    """测试从session中提取FS的功能"""
    print("="*80)
    print("🔬 Testing Forgetting Score Extraction")
    print("="*80)
    
    # 测试不同的FS methods
    methods = ['simple_time', 'history', 'lpkt', 'dkt', 'akt', 'simplekt']
    
    # 加载一个session
    session_file = '/mnt/localssd/bank/session/assist2017/10.json'
    with open(session_file, 'r') as f:
        session = json.load(f)
    
    print(f"\n测试Session: student_id={session['student_id']}, concept={session['concept_text']}")
    print(f"Time: delta_t={session['delta_t_minutes']:.2f} minutes ({session['delta_t_days']:.4f} days)")
    
    print(f"\n{'='*80}")
    print(f"Available Methods in Session:")
    print(f"{'='*80}")
    for method, data in session.get('methods', {}).items():
        if isinstance(data, dict):
            fs = data.get('fs', 'N/A')
            level = data.get('level', 'N/A')
            fs_str = f"{fs:.4f}" if isinstance(fs, float) else str(fs)
            print(f"  {method:12s}: fs={fs_str}, level={level}")
    
    print(f"\n{'='*80}")
    print(f"Testing FS Extraction for Each Method:")
    print(f"{'='*80}")
    
    from tasa_rewrite import MasteryRewriter
    from tasa_config import get_forgetting_level
    
    for method in methods:
        print(f"\n--- Method: {method} ---")
        
        # 临时修改配置
        import tasa_config
        original_method = tasa_config.FORGETTING_SCORE_METHOD
        tasa_config.FORGETTING_SCORE_METHOD = method
        
        try:
            rewriter = MasteryRewriter()
            forgetting_info = rewriter.load_forgetting_info(
                student_id=session['student_id'],
                dataset='assist2017',
                concept_text=session['concept_text']
            )
            
            fs = forgetting_info['forgetting_score']
            level = forgetting_info['forgetting_level']
            
            print(f"  Forgetting Score: {fs:.4f}")
            print(f"  Forgetting Level: {level}")
            
            # 检查level映射
            if method in ['history', 'lpkt', 'dkt', 'akt', 'simplekt']:
                if method in session.get('methods', {}):
                    method_level = session['methods'][method].get('level', '')
                    # 正确的映射规则
                    if method_level == 'medium':
                        expected_level = 'moderate'
                    elif method_level == 'high':
                        expected_level = 'high'
                    elif method_level == 'low':
                        expected_level = 'low'
                    else:
                        expected_level = method_level
                    
                    if level == expected_level:
                        print(f"  ✅ Level mapping correct: {method_level} → {level}")
                    else:
                        print(f"  ❌ Level mapping error: expected {expected_level}, got {level}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
        finally:
            # 恢复原始配置
            tasa_config.FORGETTING_SCORE_METHOD = original_method
    
    print(f"\n{'='*80}")
    print(f"✅ Verification Complete")
    print(f"{'='*80}")

def show_prompt_example():
    """展示实际的prompt示例"""
    print("\n" + "="*80)
    print("📝 Example Prompt with New Format")
    print("="*80)
    
    # 模拟一个forgetting info
    fs = 0.3294
    level = "moderate"
    mastery = 0.67
    delta_t_days = 0.32
    
    from tasa_config import FORGETTING_LEVELS
    
    prompt = f"""The student's original state: "Student shows good understanding of 'area' with 67% accuracy" for concept "area", with mastery {mastery:.2f}.
This concept was last practiced {delta_t_days:.1f} days ago.

Forgetting Score: {fs:.4f} (range: 0-1, where higher values indicate more forgetting)
Forgetting Level: {level} - {FORGETTING_LEVELS[level]}

Rewrite the description to reflect the current knowledge state after forgetting."""
    
    print("\n" + prompt)
    print("\n" + "="*80)

def compare_fs_values():
    """对比simple_time和各个method的FS值"""
    print("\n" + "="*80)
    print("📊 Comparing FS Values: simple_time vs Methods")
    print("="*80)
    
    # 加载一个session
    with open('/mnt/localssd/bank/session/assist2017/10.json', 'r') as f:
        session = json.load(f)
    
    delta_t_days = session['delta_t_days']
    
    # Simple time calculation
    fs_simple = 1 - 1 / (1 + delta_t_days / 7)
    
    print(f"\nStudent: {session['student_id']}, Concept: {session['concept_text']}")
    print(f"Time: {delta_t_days:.4f} days ({delta_t_days*24:.2f} hours)")
    print(f"\n{'Method':<15} {'FS Value':<12} {'Difference from simple_time':<30}")
    print("-"*80)
    print(f"{'simple_time':<15} {fs_simple:.4f}")
    
    for method, data in session.get('methods', {}).items():
        if isinstance(data, dict) and 'fs' in data:
            fs_method = data['fs']
            diff = fs_method - fs_simple
            diff_pct = (diff / fs_simple * 100) if fs_simple > 0 else 0
            print(f"{method:<15} {fs_method:.4f}       {diff:+.4f} ({diff_pct:+.1f}%)")
    
    print("\n💡 Observation:")
    print("   - Simple_time只看时间，可能低估或高估遗忘")
    print("   - Methods考虑了学习历史，更准确反映知识状态")

if __name__ == '__main__':
    try:
        test_forgetting_score_extraction()
        show_prompt_example()
        compare_fs_values()
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

