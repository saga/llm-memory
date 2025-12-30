# 🧠 LLM Memory System v2.0

**Production-grade long-term memory for LLM agents**

Built with PydanticAI + ChromaDB + Clean Architecture

---

## ✨ What Makes This Production-Ready

This is **not a demo**. This is a production architecture you can deploy and scale.

### 🎯 Core Principles

1. **Vector DB ≠ Agent State**
   - Agent operates on `MemoryState` (working memory)
   - ChromaDB is long-term storage (brain)
   - Clean separation prevents hallucination pollution

2. **Memory Writes After Agent Run**
   - Agent outputs to state
   - Persistence happens outside agent
   - No hallucinated memories in vector DB

3. **Layered Architecture**
   ```
   agent/     → PydanticAI logic (stateless)
   memory/    → Business logic (will outlive agent)
   infra/     → Swappable services (embeddings, config, snapshots)
   api/       → Thin HTTP layer
   ```

4. **Everything is Swappable**
   - Change vector DB? Edit `memory/vector_store.py`
   - Change embedding provider? Edit `infra/embedding.py`
   - Change LLM? Pass different model to agent

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key

### 1. Install Dependencies

```bash
# Activate virtual environment
.\activate.ps1

# Install with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

### 2. Set API Key

```powershell
$env:OPENAI_API_KEY = "sk-..."
```

### 3. Run Example

```bash
# Complete production flow demo
python main.py

# Or use automation script
.\setup_and_run.ps1 main.py
```

### 4. Run API Server

```bash
# Start FastAPI server
python -m api.chat_api

# Or with uvicorn
uvicorn api.chat_api:app --reload

# Test with curl
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Remember that I love Python"}'
```

---

## 📂 Architecture

```
llm-memory/
├── agent/              # 🤖 PydanticAI Agent
│   ├── agent.py        #   Agent definition
│   ├── tools.py        #   Memory tools (@agent.tool)
│   └── prompts.py      #   System prompts & policies
│
├── memory/             # 🧠 Memory Management
│   ├── models.py       #   Pydantic schemas (MemoryState, MemoryItem)
│   ├── manager.py      #   Core business logic (retrieve, score, persist)
│   ├── vector_store.py #   ChromaDB abstraction (swappable)
│   └── summarizer.py   #   Conversation compression
│
├── infra/              # 🔧 Infrastructure
│   ├── embedding.py    #   Embedding service (OpenAI, Cohere, etc.)
│   ├── config.py       #   Configuration management
│   └── snapshot.py     #   S3 backup/restore
│
├── api/                # 🌐 HTTP API
│   └── chat_api.py     #   FastAPI endpoints
│
├── main.py             # 📱 Complete example
└── demos/              # 📚 Learning demos
```

---

## 🔄 The Core Flow

Every chat request follows this pattern:

```python
# 1. Retrieve relevant memories from vector DB
memories = memory_manager.retrieve(query=user_input)

# 2. Create agent state (working memory)
state = MemoryState(active_memories=memories)

# 3. Run agent (stateless)
result = agent.run_sync(user_input, deps=state)

# 4. Persist new memories (AFTER agent run)
for memory in state.active_memories[len(memories):]:
    memory_manager.write_memory(memory)

# 5. Return response
return result.data
```

**Why this order matters:**
- ✅ Memories are retrieved **before** agent (context)
- ✅ Agent operates on state **during** run (logic)
- ✅ Persistence happens **after** agent (safety)

This prevents hallucinated memories from polluting your vector DB.

---

## 💡 Key Features

### 1. Memory Types
- **semantic**: General knowledge, concepts
- **preference**: User preferences, habits
- **fact**: Specific user facts, commitments

### 2. Intelligent Scoring
```python
final_score = relevance * 0.5 + importance * 0.3 + recency * 0.2
```

### 3. Structured Updates
```python
@agent.tool
def update_memory(update: MemoryUpdate) -> str:
    # Type-safe memory creation
    # LLM can't inject invalid data
```

### 4. Swappable Components
```python
# Change embedding provider
embedder = create_embedder(provider="cohere")

# Change vector DB (edit vector_store.py)
# Current: ChromaDB
# Future: pgvector, Milvus, Pinecone
```

---

## 🧪 Example Usage

### Python API

```python
from memory import VectorStore, MemoryManager
from agent import create_memory_agent
from infra import create_embedder

# Initialize
embedder = create_embedder()
vector_store = VectorStore()
memory_manager = MemoryManager(vector_store, embedder)
agent = create_memory_agent()

# Chat
memories = memory_manager.retrieve("What did I tell you?")
state = MemoryState(active_memories=memories)
result = agent.run_sync("What did I tell you?", deps=state)

# Persist
for mem in state.active_memories[len(memories):]:
    memory_manager.write_memory(mem.content, mem.type, mem.importance)
```

### HTTP API

```bash
# Start server
uvicorn api.chat_api:app

# Chat endpoint
POST /chat
{
  "user_input": "I prefer Python over JavaScript",
  "user_id": "user_123"
}

# Response
{
  "response": "Got it! I'll remember your preference for Python.",
  "memories_created": 1,
  "memories_retrieved": 0
}

# Stats
GET /stats
```

---

## ⚙️ Configuration

All configuration via environment variables or `infra/config.py`:

```bash
# Embedding
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small

# Vector Store
VECTOR_STORE_DIR=./chroma_db

# Agent
AGENT_MODEL=openai:gpt-4
AGENT_TEMPERATURE=0.7

# Memory
MAX_ACTIVE_MEMORIES=10
RETENTION_DAYS=90

# API
API_PORT=8000

# S3 Snapshots
S3_BUCKET=my-memory-backups
SNAPSHOT_INTERVAL=24
```

---

## 📊 S3 Snapshots

```python
from infra import create_snapshot_manager

snapshot = create_snapshot_manager()

# Backup to S3
snapshot.snapshot_to_s3()

# Restore from S3
snapshot.restore_from_s3("latest")

# List snapshots
snapshots = snapshot.list_snapshots()
```

---

## 🛠️ Development

### Run Tests
```bash
pytest
```

### Code Quality
```bash
black .
flake8
```

### Install Dev Dependencies
```bash
uv pip install -e ".[dev]"
```

---

## 🎓 Learning Path

1. **Start Here**: [main.py](main.py) - Complete production flow
2. **Architecture**: [docs/](docs/) - Design decisions
3. **Demos**: [demos/](demos/) - Simple examples
4. **API**: [api/chat_api.py](api/chat_api.py) - HTTP interface

---

## 🔥 What's Different from LangChain/LangGraph?

| Feature | This System | LangChain |
|---------|-------------|-----------|
| **Architecture** | Layered, decoupled | Tightly coupled |
| **Agent Framework** | PydanticAI (type-safe) | LangChain (string-based) |
| **Vector DB** | Isolated layer | Exposed to agent |
| **Memory Safety** | Persists AFTER agent | Can persist during |
| **Code Size** | ~1,500 lines | ~5,000+ lines |
| **Swappability** | Easy (edit one file) | Hard (refactor everywhere) |
| **Type Safety** | Full Pydantic | Partial |

---

## 📈 Scalability

This architecture is designed to scale:

- **Multi-user**: Add `user_id` filtering
- **Multi-region**: S3 snapshots for replication
- **High traffic**: Vector DB is read-heavy optimized
- **Long conversations**: Summarization layer prevents context bloat
- **Large memory**: ChromaDB handles millions of vectors

---

## 🚨 Production Checklist

- [ ] Set up S3 snapshots (daily cron)
- [ ] Configure monitoring (log memory stats)
- [ ] Set retention policies (delete old memories)
- [ ] Add rate limiting (API layer)
- [ ] Enable HTTPS (reverse proxy)
- [ ] Set up CI/CD (test before deploy)
- [ ] Monitor embedding costs (cache aggressively)
- [ ] Add rerank for better retrieval (future)

---

## 🤝 Contributing

This is a reference architecture. Fork and adapt to your needs.

Key extension points:
- `memory/vector_store.py` - Swap vector DB
- `infra/embedding.py` - Add embedding providers
- `agent/tools.py` - Add custom tools
- `memory/manager.py` - Tune scoring logic

---

## 📝 License

MIT

---

## 💬 Support

- Docs: [docs/](docs/)
- Issues: GitHub Issues

---

> **Design Philosophy**: "This architecture's value isn't that it works today, but that you can add features 6 months from now without rewriting everything."

Built with ❤️ for production LLM systems.
