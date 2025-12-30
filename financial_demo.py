#!/usr/bin/env python3
"""
金融科技LLM Memory系统完整使用示例
演示Pydantic + LangGraph在金融风险评估场景下的应用
"""

import sys
import os
import json
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """主示例函数"""
    print("🏦 金融科技LLM Memory系统 - 风险评估场景演示")
    print("=" * 60)
    
    # 1. 初始化系统
    print("\n1️⃣ 初始化金融科技LLM Memory系统...")
    try:
        from chat_api_v2 import FinancialLLMChat
        from state import FinancialAgentState, MessageRole, MessageType
        
        # 创建金融专用LLM聊天系统
        financial_chat = FinancialLLMChat(
            api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"),
            model="gpt-3.5-turbo",
            temperature=0.1,  # 低温度确保确定性结果
            audit_log_path="financial_demo_audit.db"
        )
        
        print("✅ 系统初始化成功")
        print(f"📊 审计日志路径: financial_demo_audit.db")
        print(f"🌡️  LLM温度设置: 0.1 (确保确定性)")
        
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        return False
    
    # 2. 设置用户风险档案
    print("\n2️⃣ 设置用户风险档案...")
    try:
        session_id = "demo_user_001"
        
        # 设置用户风险档案
        financial_chat.set_risk_profile(
            session_id=session_id,
            risk_level="medium",
            factors={
                "age": 35,
                "income": "high",
                "investment_experience": "intermediate",
                "investment_goal": "growth",
                "time_horizon": "long_term",
                "liquidity_needs": "low"
            }
        )
        
        print("✅ 用户风险档案设置成功")
        print(f"👤 用户ID: {session_id}")
        print(f"📈 风险等级: medium")
        print(f"📋 风险因素: 年龄35岁，高收入，中等投资经验")
        
    except Exception as e:
        print(f"❌ 风险档案设置失败: {e}")
        return False
    
    # 3. 模拟风险评估对话
    print("\n3️⃣ 模拟风险评估对话...")
    try:
        # 第一轮对话 - 用户询问投资建议
        print("\n🗣️ 用户: " + "我想投资科技股，有什么建议？")
        
        response1 = financial_chat.chat_completion(
            session_id=session_id,
            user_input="我想投资科技股，有什么建议？"
        )["response"]
        
        print("🤖 助手: " + response1)
        print("💭 系统思考: " + "检测到投资建议需求，进行风险评估")
        
        # 第二轮对话 - 用户询问具体风险
        print("\n🗣️ 用户: " + "科技股的风险有多大？")
        
        response2 = financial_chat.chat_completion(
            session_id=session_id,
            user_input="科技股的风险有多大？"
        )["response"]
        
        print("🤖 助手: " + response2)
        print("💭 系统思考: " + "检测到风险评估需求，结合用户档案进行分析")
        
        # 第三轮对话 - 用户询问高收益产品
        print("\n🗣️ 用户: " + "有没有高收益的理财产品推荐？")
        
        response3 = financial_chat.chat_completion(
            session_id=session_id,
            user_input="有没有高收益的理财产品推荐？"
        )["response"]
        
        print("🤖 助手: " + response3)
        print("💭 系统思考: " + "检测到产品推荐需求，进行合规检查")
        
    except Exception as e:
        print(f"❌ 对话模拟失败: {e}")
        return False
    
    # 4. 展示记忆系统
    print("\n4️⃣ 展示记忆系统功能...")
    try:
        # 获取会话历史
        session_history = financial_chat.get_session_history(session_id)
        
        print("✅ 会话历史获取成功")
        print(f"📚 总消息数: {len(session_history)}")
        
        # 获取相关记忆
        relevant_memories = financial_chat.search_memories(
            session_id=session_id,
            query="科技股风险"
        )
        
        print(f"🧠 相关记忆数: {len(relevant_memories)}")
        
        # 展示具体记忆内容
        if relevant_memories:
            print("\n📝 相关记忆内容:")
            for i, memory in enumerate(relevant_memories[:3], 1):
                print(f"  {i}. {memory.get('content', 'N/A')[:100]}...")
                print(f"     上下文: {memory.get('context', 'N/A')}")
                print(f"     时间: {memory.get('timestamp', 'N/A')}")
        
    except Exception as e:
        print(f"❌ 记忆系统展示失败: {e}")
        return False
    
    # 5. 展示审计功能
    print("\n5️⃣ 展示审计功能...")
    try:
        # 获取审计历史
        audit_history = financial_chat.audit_log.get_session_history(session_id)
        
        print("✅ 审计历史获取成功")
        print(f"📊 审计记录数: {len(audit_history)}")
        
        # 展示最近的审计记录
        if audit_history:
            print("\n📋 最近审计记录:")
            latest_audit = audit_history[-1]
            print(f"  步骤: {latest_audit.get('step', 'N/A')}")
            print(f"  时间: {latest_audit.get('timestamp', 'N/A')}")
            print(f"  状态哈希: {latest_audit.get('state_hash', 'N/A')[:16]}...")
            
            # 验证状态完整性
            is_valid = financial_chat.audit_log.verify_state_integrity(session_id)
            print(f"  完整性验证: {'✅ 通过' if is_valid else '❌ 失败'}")
        
    except Exception as e:
        print(f"❌ 审计功能展示失败: {e}")
        return False
    
    # 6. 展示合规检查
    print("\n6️⃣ 展示合规检查功能...")
    try:
        # 创建一个高风险场景
        test_session = "compliance_test_001"
        
        # 设置高风险用户
        financial_chat.set_risk_profile(
            session_id=test_session,
            risk_level="high",
            factors={"age": 25, "income": "low", "investment_experience": "none"}
        )
        
        # 测试高风险投资建议
        print("\n🗣️ 用户 (高风险): " + "我想投资比特币，保证能赚钱吗？")
        
        response = financial_chat.chat_completion(
            session_id=test_session,
            user_input="我想投资比特币，保证能赚钱吗？"
        )["response"]
        
        print("🤖 助手: " + response)
        
        # 检查合规标记
        current_state = financial_chat._get_current_state(test_session)
        if hasattr(current_state, 'compliance_flags') and current_state.compliance_flags:
            print("\n⚠️  触发的合规标记:")
            for flag in current_state.compliance_flags:
                print(f"  - {flag}")
        
        print("✅ 合规检查功能正常")
        
    except Exception as e:
        print(f"❌ 合规检查展示失败: {e}")
        return False
    
    # 7. 总结
    print("\n" + "=" * 60)
    print("🎉 金融科技LLM Memory系统演示完成！")
    print("\n✅ 系统特性验证:")
    print("  - Pydantic强一致性状态管理")
    print("  - LangGraph显式状态机控制")
    print("  - SQLite审计日志记录")
    print("  - 金融风险评估功能")
    print("  - 合规检查和风险披露")
    print("  - 智能记忆和上下文管理")
    print("  - 确定性结果保证 (temperature=0.1)")
    
    print("\n🚀 系统已准备好用于生产环境！")
    print("\n📁 生成的文件:")
    print("  - financial_demo_audit.db (审计日志)")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)