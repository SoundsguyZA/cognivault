# CogniVault + Aluna-Memory Integration Architecture

## Overview
This document outlines how CogniVault (RAG knowledge processor) integrates with Aluna-Memory (persistent memory layer) to create an intelligent knowledge management system.

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     User Input                               │
│  (Files, Folders, WhatsApp exports, ChatGPT logs, etc.)    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     v
┌─────────────────────────────────────────────────────────────┐
│                   COGNIVAULT                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Document Processing                               │  │
│  │     - Extract text from PDFs, DOCX, TXT, MD          │  │
│  │     - Process WhatsApp/ChatGPT exports                │  │
│  │     - Transcribe audio (Whisper)                      │  │
│  │     - Extract image metadata                          │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  2. Intelligent Indexing                              │  │
│  │     - TF-IDF vector embeddings                        │  │
│  │     - Entity extraction                               │  │
│  │     - Metadata tagging                                 │  │
│  │     - Content categorization                          │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  3. Local Vector Store                                │  │
│  │     - TF-IDF search index                             │  │
│  │     - Fast local retrieval                            │  │
│  │     - Session storage                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │ Memory Bridge API
                     │ (REST/gRPC)
                     v
┌─────────────────────────────────────────────────────────────┐
│                  ALUNA-MEMORY (Mem0)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  4. Persistent Memory Storage                         │  │
│  │     - PostgreSQL vector database                      │  │
│  │     - Redis cache layer                               │  │
│  │     - Long-term memory retention                      │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  5. Memory Operations                                 │  │
│  │     - Add: Store processed knowledge                  │  │
│  │     - Search: Semantic/vector search                  │  │
│  │     - Update: Refine memories                         │  │
│  │     - Delete: Remove obsolete info                    │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  6. Graph Relationships                               │  │
│  │     - Entity relationships                            │  │
│  │     - Knowledge graph                                 │  │
│  │     - Context linking                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │ MCP Protocol
                     │ (Model Context Protocol)
                     v
┌─────────────────────────────────────────────────────────────┐
│                    OPENMEMORY                                │
│  - Public memory interface                                   │
│  - MCP server endpoint                                       │
│  - Claude Desktop integration                                │
│  - API for external access                                   │
└─────────────────────────────────────────────────────────────┘
                     │
                     v
┌─────────────────────────────────────────────────────────────┐
│              AI AGENTS & APPLICATIONS                        │
│  - Agent Zero (autonomous AI agent)                          │
│  - ClawdBot (WhatsApp/Telegram gateway)                     │
│  - Claude Desktop (via MCP)                                  │
│  - Custom applications                                       │
└─────────────────────────────────────────────────────────────┘
```

## Integration Components

### 1. Memory Bridge (To Be Implemented)
**Location**: `cognivault/memory_bridge.py`

```python
class MemoryBridge:
    """Bridge between CogniVault and Aluna-Memory"""
    
    def __init__(self, aluna_memory_url: str, api_key: str):
        self.aluna_url = aluna_memory_url
        self.api_key = api_key
        self.client = Mem0Client(api_key)
    
    def store_document(self, doc_id: str, content: str, metadata: dict):
        """Store processed document in Aluna-Memory"""
        memory = {
            "messages": [{"role": "user", "content": content}],
            "metadata": {
                **metadata,
                "source": "cognivault",
                "doc_id": doc_id,
                "timestamp": datetime.now().isoformat()
            }
        }
        return self.client.add(memory, user_id=metadata.get("user_id", "default"))
    
    def search_memories(self, query: str, filters: dict = None):
        """Search Aluna-Memory with filters"""
        return self.client.search(query, user_id="default", filters=filters)
    
    def get_related_memories(self, memory_id: str):
        """Get related memories using graph relationships"""
        return self.client.get_related(memory_id)
```

### 2. Data Flow

#### Upload Flow:
1. **User uploads file to CogniVault** (Web UI - Streamlit)
2. **CogniVault processes**:
   - Detects file type (WhatsApp/ChatGPT/Document/Audio/Image)
   - Extracts content and metadata
   - Creates TF-IDF embeddings
   - Stores in local vector store (fast access)
3. **Memory Bridge transfers to Aluna-Memory**:
   - Converts CogniVault format to Mem0 format
   - Adds memory with metadata
   - Creates relationships with existing memories
   - Stores in PostgreSQL + Redis
4. **OpenMemory exposes**:
   - Makes memory available via MCP protocol
   - Provides API access for agents

#### Retrieval Flow:
1. **User queries through CogniVault**
2. **CogniVault searches locally** (fast)
3. **Memory Bridge queries Aluna-Memory** (comprehensive)
4. **Merge results** from both sources
5. **Return ranked results** to user

### 3. Configuration

#### Environment Variables:
```env
# CogniVault
COGNIVAULT_PORT=50004
COGNIVAULT_DATA_DIR=/app/data

# Aluna-Memory Connection
ALUNA_MEMORY_URL=http://aluna-memory:8000
ALUNA_MEMORY_API_KEY=your_api_key_here

# Memory Bridge
ENABLE_MEMORY_SYNC=true
SYNC_INTERVAL=300  # seconds
AUTO_SYNC=true

# OpenMemory
OPENMEMORY_MCP_PORT=8081
```

#### Docker Compose Integration:
```yaml
services:
  cognivault:
    build: ./cognivault
    ports:
      - "50004:8501"
    environment:
      - ALUNA_MEMORY_URL=http://aluna-memory:8000
      - ENABLE_MEMORY_SYNC=true
    depends_on:
      - aluna-memory
    networks:
      - veritas-network
  
  aluna-memory:
    build: ./aluna-memory
    ports:
      - "50003:8000"
    environment:
      - POSTGRES_HOST=postgres
      - REDIS_HOST=redis
    depends_on:
      - postgres
      - redis
    networks:
      - veritas-network
```

## Use Cases

### 1. WhatsApp Chat Knowledge Base
- **Input**: WhatsApp export ZIP
- **CogniVault**: Extracts messages, media, metadata
- **Aluna-Memory**: Stores conversations with relationships
- **Query**: "What did John say about the project last week?"
- **Result**: Retrieves relevant messages from memory

### 2. ChatGPT Log Analysis
- **Input**: ChatGPT conversation export
- **CogniVault**: Parses conversations, extracts key insights
- **Aluna-Memory**: Creates knowledge graph of discussions
- **Query**: "Summarize all AI-related discussions"
- **Result**: Synthesizes memories across conversations

### 3. Document Library
- **Input**: Collection of PDFs, DOCX files
- **CogniVault**: Extracts text, creates embeddings
- **Aluna-Memory**: Stores with semantic relationships
- **Query**: "Find documents about machine learning"
- **Result**: Semantic search across all stored docs

### 4. Audio Knowledge Extraction
- **Input**: Audio files (interviews, meetings, podcasts)
- **CogniVault**: Transcribes with Whisper
- **Aluna-Memory**: Stores transcriptions with timestamps
- **Query**: "What was discussed about the budget?"
- **Result**: Retrieves relevant audio segments

## Benefits of Integration

1. **Dual Storage Strategy**:
   - CogniVault: Fast local access, session-based
   - Aluna-Memory: Persistent, cross-session, relational

2. **Intelligent Routing**:
   - Recent queries → CogniVault (fast)
   - Complex queries → Aluna-Memory (comprehensive)
   - Hybrid queries → Both sources merged

3. **Scalability**:
   - CogniVault handles upload processing
   - Aluna-Memory handles long-term storage
   - OpenMemory provides universal access

4. **Privacy**:
   - Local processing in CogniVault
   - Encrypted storage in Aluna-Memory
   - Controlled access via MCP

## Implementation Phases

### Phase 1: Basic Integration (Week 1)
- [ ] Create Memory Bridge API
- [ ] Implement document→memory conversion
- [ ] Basic sync functionality
- [ ] Docker integration

### Phase 2: Advanced Features (Week 2)
- [ ] Bidirectional sync
- [ ] Graph relationship creation
- [ ] Hybrid search (local + mem0)
- [ ] Memory deduplication

### Phase 3: Optimization (Week 3)
- [ ] Caching strategies
- [ ] Batch processing
- [ ] Memory compression
- [ ] Performance tuning

### Phase 4: Production (Week 4)
- [ ] Monitoring & logging
- [ ] Backup strategies
- [ ] API documentation
- [ ] User guides

## API Endpoints

### CogniVault → Aluna-Memory
```
POST /api/memory/store
GET  /api/memory/search
PUT  /api/memory/update
DELETE /api/memory/delete
GET  /api/memory/related/{id}
```

### Aluna-Memory → OpenMemory
```
MCP Protocol endpoints (via Model Context Protocol)
```

## Next Steps

1. **Review this architecture** with Rob
2. **Implement Memory Bridge** (`memory_bridge.py`)
3. **Update CogniVault** to use Memory Bridge
4. **Test integration** locally
5. **Deploy to VPS** with updated docker-compose
6. **Document API usage** for agents

---

**Created**: 2026-01-30
**Version**: 1.0
**Status**: Architecture Complete - Ready for Implementation
