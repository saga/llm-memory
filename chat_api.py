import openai
from typing import Dict, Any, Optional, List
import os
from memory_system import LLMChatWithMemory, DeterministicMemoryStore


class CompletionChatAPI:
    """Completion Chat API集成类"""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: str = "gpt-3.5-turbo",
                 memory_store_path: str = "memory_store.json",
                 temperature: float = 0.1,  # 低温度确保确定性
                 max_tokens: int = 1000):
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("请提供OpenAI API密钥或通过环境变量OPENAI_API_KEY设置")
        
        openai.api_key = self.api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # 初始化记忆系统
        self.memory_store = DeterministicMemoryStore(memory_store_path)
        self.chat_with_memory = LLMChatWithMemory(self.memory_store)
    
    def set_context(self, context: str):
        """设置当前对话上下文"""
        self.chat_with_memory.set_context(context)
    
    def chat_completion(self, 
                       user_input: str, 
                       context: Optional[str] = None,
                       save_to_memory: bool = True,
                       system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        发送聊天完成请求
        
        Args:
            user_input: 用户输入
            context: 上下文（可选，会覆盖当前设置）
            save_to_memory: 是否保存到记忆
            system_prompt: 系统提示词（可选）
        
        Returns:
            包含响应和元数据的字典
        """
        # 设置上下文
        if context:
            original_context = self.chat_with_memory.current_context
            self.chat_with_memory.set_context(context)
        
        try:
            # 获取相关记忆
            relevant_context = self.chat_with_memory.get_relevant_context(user_input)
            
            # 构建消息
            messages = []
            
            # 添加系统提示词
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # 如果有相关记忆，添加到系统消息中
            if relevant_context:
                memory_message = f"之前的相关对话记忆:\n{relevant_context}\n\n请结合以上上下文回答用户的问题。"
                if messages and messages[0]["role"] == "system":
                    messages[0]["content"] += f"\n\n{memory_message}"
                else:
                    messages.insert(0, {"role": "system", "content": memory_message})
            
            # 添加用户输入
            messages.append({"role": "user", "content": user_input})
            
            # 调用API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,  # 低温度确保确定性
                max_tokens=self.max_tokens
            )
            
            assistant_response = response.choices[0].message.content
            
            # 保存到记忆
            if save_to_memory:
                self.chat_with_memory.add_memory_from_interaction(
                    user_input=user_input,
                    assistant_response=assistant_response,
                    metadata={
                        "model": self.model,
                        "temperature": self.temperature,
                        "timestamp": response.created
                    }
                )
            
            return {
                "response": assistant_response,
                "model": self.model,
                "usage": response.usage,
                "has_memory": bool(relevant_context),
                "memory_count": len(self.memory_store.memories),
                "timestamp": response.created
            }
            
        finally:
            # 恢复原始上下文
            if context:
                self.chat_with_memory.set_context(original_context)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        return {
            "total_memories": len(self.memory_store.memories),
            "contexts": len(self.memory_store.context_index),
            "storage_path": self.memory_store.storage_path
        }
    
    def search_memories(self, query: str, context: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索记忆"""
        memories = self.memory_store.search_memories(query, context, limit)
        return [memory.to_dict() for memory in memories]
    
    def clear_memories(self, context: Optional[str] = None):
        """清除记忆"""
        if context:
            # 清除特定上下文的记忆
            if context in self.memory_store.context_index:
                memory_ids = self.memory_store.context_index[context].copy()
                for memory_id in memory_ids:
                    if memory_id in self.memory_store.memories:
                        del self.memory_store.memories[memory_id]
                del self.memory_store.context_index[context]
                self.memory_store.save_memories()
        else:
            # 清除所有记忆
            self.memory_store.memories.clear()
            self.memory_store.context_index.clear()
            self.memory_store.save_memories()


# 使用示例和测试函数
def demo_financial_chat():
    """金融科技场景演示"""
    
    # 初始化API（请确保设置了OPENAI_API_KEY环境变量）
    try:
        api = CompletionChatAPI(
            model="gpt-3.5-turbo",
            temperature=0.1,  # 低温度确保确定性
            memory_store_path="financial_memory.json"
        )
    except ValueError as e:
        print(f"初始化失败: {e}")
        print("请设置OPENAI_API_KEY环境变量")
        return
    
    # 设置金融上下文
    api.set_context("financial_advisory")
    
    # 模拟金融咨询对话
    conversations = [
        "用户的风险承受能力如何评估？",
        "基于稳健型投资者，推荐什么理财产品？",
        "这些产品的预期收益率是多少？",
        "如何分散投资风险？"
    ]
    
    print("=== 金融科技LLM Memory演示 ===\n")
    
    for i, user_input in enumerate(conversations):
        print(f"对话 {i+1}:")
        print(f"用户: {user_input}")
        
        # 添加金融专业系统提示词
        system_prompt = """你是一个专业的金融顾问。请提供准确、合规、风险可控的建议。
        回答必须：
        1. 基于事实和数据
        2. 考虑风险因素
        3. 符合监管要求
        4. 适合用户的风险承受能力"""
        
        result = api.chat_completion(
            user_input=user_input,
            system_prompt=system_prompt,
            save_to_memory=True
        )
        
        print(f"助手: {result['response']}")
        print(f"使用记忆: {result['has_memory']}, 总记忆数: {result['memory_count']}")
        print("-" * 50)
    
    # 显示记忆统计
    stats = api.get_memory_stats()
    print(f"\n记忆统计: {stats}")
    
    # 搜索相关记忆
    print("\n搜索'风险'相关记忆:")
    risk_memories = api.search_memories("风险", limit=3)
    for memory in risk_memories:
        print(f"- {memory['content'][:100]}...")


if __name__ == "__main__":
    demo_financial_chat()