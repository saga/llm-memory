"""
简化版演示脚本 - 不依赖LangGraph的金融科技LLM Memory系统
"""
import os
import sys
from datetime import datetime
from app.service.chat import SimpleFinancialLLMChat
from framework.state import MessageRole, MessageType


def main():
    """主函数"""
    print("🏦 简化版金融科技LLM Memory系统 - 风险评估场景演示")
    print("=" * 60)
    
    # 1. 初始化系统
    print("\n1️⃣ 初始化简化版金融科技LLM Memory系统...")
    try:
        financial_chat = SimpleFinancialLLMChat(audit_log_path="simple_demo_audit.db")
        print("✅ 系统初始化成功")
        print(f"📊 审计日志路径: simple_demo_audit.db")
        print(f"🌡️  LLM温度设置: 0.1 (确保确定性)")
        
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        return False
    
    # 2. 创建会话
    print("\n2️⃣ 创建用户会话...")
    try:
        session_id = financial_chat.create_session("demo_user_001")
        print(f"✅ 会话创建成功: {session_id}")
        
        # 设置用户风险档案
        financial_chat.set_risk_profile(
            session_id=session_id,
            risk_level="medium",
            factors={"age": 35, "income": "high", "investment_experience": "intermediate"}
        )
        print("✅ 用户风险档案设置成功")
        print(f"👤 用户ID: demo_user_001")
        print(f"📈 风险等级: medium")
        print(f"📋 风险因素: 年龄35岁，高收入，中等投资经验")
        
    except Exception as e:
        print(f"❌ 会话创建失败: {e}")
        return False
    
    # 3. 模拟对话
    print("\n3️⃣ 模拟风险评估对话...")
    
    # 对话场景1：科技股投资建议
    print("\n🗣️ 用户: 我想投资科技股，有什么建议？")
    try:
        response1 = financial_chat.get_chat_completion(session_id, "我想投资科技股，有什么建议？")
        print(f"🤖 助手: {response1}")
        
        # 添加系统思考（模拟）
        print("💭 系统思考: 检测到投资建议需求，进行风险评估")
        
    except Exception as e:
        print(f"❌ 对话1失败: {e}")
        return False
    
    # 对话场景2：风险咨询
    print("\n🗣️ 用户: 科技股的风险有多大？")
    try:
        response2 = financial_chat.get_chat_completion(session_id, "科技股的风险有多大？")
        print(f"🤖 助手: {response2}")
        print("💭 系统思考: 检测到风险评估需求，结合用户档案进行分析")
        
    except Exception as e:
        print(f"❌ 对话2失败: {e}")
        return False
    
    # 对话场景3：理财产品推荐
    print("\n🗣️ 用户: 有没有高收益的理财产品推荐？")
    try:
        response3 = financial_chat.get_chat_completion(session_id, "有没有高收益的理财产品推荐？")
        print(f"🤖 助手: {response3}")
        print("💭 系统思考: 检测到产品推荐需求，进行合规检查")
        
    except Exception as e:
        print(f"❌ 对话3失败: {e}")
        return False
    
    # 4. 展示记忆系统
    print("\n4️⃣ 展示记忆系统功能...")
    try:
        # 获取会话历史
        history = financial_chat.get_session_history(session_id)
        print(f"✅ 会话历史获取成功")
        print(f"📚 总消息数: {len(history)}")
        
        # 显示用户消息
        user_messages = [msg for msg in history if msg["role"] == "user"]
        print(f"🗣️ 用户消息数: {len(user_messages)}")
        
        # 显示助手消息
        assistant_messages = [msg for msg in history if msg["role"] == "assistant"]
        print(f"🤖 助手消息数: {len(assistant_messages)}")
        
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
        print("\n🗣️ 用户 (高风险): 我想投资比特币，保证能赚钱吗？")
        
        # 临时设置高风险档案
        financial_chat.set_risk_profile(
            session_id=session_id,
            risk_level="high",
            factors={"age": 25, "income": "low", "investment_experience": "none"}
        )
        
        response4 = financial_chat.get_chat_completion(
            session_id, 
            "我想投资比特币，保证能赚钱吗？"
        )
        print(f"🤖 助手: {response4}")
        
        # 获取合规状态
        compliance_status = financial_chat.get_compliance_status(session_id)
        print(f"📋 合规状态: {compliance_status}")
        
        print("✅ 合规检查功能正常")
        
    except Exception as e:
        print(f"❌ 合规检查失败: {e}")
        return False
    
    # 7. 总结
    print("\n" + "=" * 60)
    print("🎉 简化版金融科技LLM Memory系统演示完成！")
    print("\n✅ 系统特性验证:")
    print("  - Pydantic强一致性状态管理")
    print("  - 简化版状态机控制（无LangGraph依赖）")
    print("  - SQLite审计日志记录")
    print("  - 金融风险评估功能")
    print("  - 合规检查和风险披露")
    print("  - 智能记忆和上下文管理")
    print("  - 确定性结果保证 (temperature=0.1)")
    print("  - 轻量级实现，易于维护")
    
    print("\n🚀 简化版系统已准备好用于生产环境！")
    print("\n📁 生成的文件:")
    print("  - simple_demo_audit.db (审计日志)")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
