import json
import hashlib
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import os


@dataclass
class MemoryEntry:
    """单个记忆条目"""
    id: str
    content: str
    context: str
    timestamp: float
    metadata: Dict[str, Any]
    hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        return cls(**data)


class DeterministicMemoryStore:
    """确定性记忆存储系统"""
    
    def __init__(self, storage_path: str = "memory_store.json"):
        self.storage_path = storage_path
        self.memories: Dict[str, MemoryEntry] = {}
        self.context_index: Dict[str, List[str]] = {}  # 上下文索引
        self.load_memories()
    
    def _generate_hash(self, content: str, context: str) -> str:
        """生成确定性哈希"""
        combined = f"{content}|{context}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def _generate_id(self, content: str, context: str, timestamp: float) -> str:
        """生成确定性ID"""
        combined = f"{content}|{context}|{timestamp}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def add_memory(self, content: str, context: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加记忆，返回记忆ID"""
        timestamp = time.time()
        memory_id = self._generate_id(content, context, timestamp)
        memory_hash = self._generate_hash(content, context)
        
        # 检查是否已存在相同内容的记忆
        if memory_hash in [m.hash for m in self.memories.values()]:
            return list(self.memories.keys())[list([m.hash for m in self.memories.values()]).index(memory_hash)]
        
        entry = MemoryEntry(
            id=memory_id,
            content=content,
            context=context,
            timestamp=timestamp,
            metadata=metadata or {},
            hash=memory_hash
        )
        
        self.memories[memory_id] = entry
        
        # 更新上下文索引
        if context not in self.context_index:
            self.context_index[context] = []
        self.context_index[context].append(memory_id)
        
        self.save_memories()
        return memory_id
    
    def get_memories_by_context(self, context: str, limit: int = 10) -> List[MemoryEntry]:
        """根据上下文获取记忆"""
        if context not in self.context_index:
            return []
        
        memory_ids = self.context_index[context][-limit:]  # 获取最近的记忆
        return [self.memories[mid] for mid in memory_ids if mid in self.memories]
    
    def search_memories(self, query: str, context: Optional[str] = None, limit: int = 5) -> List[MemoryEntry]:
        """搜索记忆"""
        relevant_memories = []
        
        # 如果在特定上下文中搜索
        if context:
            candidates = self.get_memories_by_context(context)
        else:
            candidates = list(self.memories.values())
        
        # 简单的关键词匹配
        query_lower = query.lower()
        for memory in candidates:
            if (query_lower in memory.content.lower() or 
                query_lower in memory.context.lower()):
                relevant_memories.append(memory)
        
        # 按时间戳排序（最新的在前）
        relevant_memories.sort(key=lambda x: x.timestamp, reverse=True)
        return relevant_memories[:limit]
    
    def save_memories(self):
        """保存记忆到文件"""
        data = {
            "memories": {mid: entry.to_dict() for mid, entry in self.memories.items()},
            "context_index": self.context_index
        }
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.storage_path) if os.path.dirname(self.storage_path) else '.', exist_ok=True)
        
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_memories(self):
        """从文件加载记忆"""
        if not os.path.exists(self.storage_path):
            return
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.memories = {
                mid: MemoryEntry.from_dict(entry_data) 
                for mid, entry_data in data.get("memories", {}).items()
            }
            self.context_index = data.get("context_index", {})
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            self.memories = {}
            self.context_index = {}


class LLMChatWithMemory:
    """带记忆功能的LLM Chat系统"""
    
    def __init__(self, memory_store: Optional[DeterministicMemoryStore] = None):
        self.memory_store = memory_store or DeterministicMemoryStore()
        self.current_context = "default"
    
    def set_context(self, context: str):
        """设置当前上下文"""
        self.current_context = context
    
    def add_memory_from_interaction(self, user_input: str, assistant_response: str, 
                                  metadata: Optional[Dict[str, Any]] = None):
        """从交互中添加记忆"""
        # 存储用户输入
        self.memory_store.add_memory(
            content=user_input,
            context=self.current_context,
            metadata={"type": "user_input", **(metadata or {})}
        )
        
        # 存储助手回复
        self.memory_store.add_memory(
            content=assistant_response,
            context=self.current_context,
            metadata={"type": "assistant_response", **(metadata or {})}
        )
    
    def get_relevant_context(self, query: str, limit: int = 3) -> str:
        """获取相关的上下文信息"""
        relevant_memories = self.memory_store.search_memories(
            query=query, 
            context=self.current_context, 
            limit=limit
        )
        
        if not relevant_memories:
            return ""
        
        context_parts = []
        for memory in relevant_memories:
            memory_type = memory.metadata.get("type", "unknown")
            if memory_type == "user_input":
                context_parts.append(f"用户之前问: {memory.content}")
            elif memory_type == "assistant_response":
                context_parts.append(f"之前回答: {memory.content}")
            else:
                context_parts.append(f"相关信息: {memory.content}")
        
        return "\n".join(context_parts)
    
    def format_prompt_with_memory(self, user_input: str) -> str:
        """格式化带记忆的提示词"""
        relevant_context = self.get_relevant_context(user_input)
        
        if relevant_context:
            return f"""基于之前的对话记忆:
{relevant_context}

当前用户输入: {user_input}

请结合以上上下文信息回答:"""
        else:
            return user_input