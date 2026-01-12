# Integration Guide: Knowledge Base with LLM

This guide explains how the Knowledge Base integrates with the LLM Service for RAG (Retrieval-Augmented Generation) conversations.

## Architecture

```
┌─────────────────┐
│  User Query     │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Search  │
    │   KB    │ ← DocumentIngestionService searches Qdrant
    └────┬────┘
         │ Retrieved context
         │
    ┌────▼──────────┐
    │  LLM Service  │ ← Generates response with context
    └────┬──────────┘
         │
    ┌────▼────────┐
    │  Response   │
    └─────────────┘
```

## How It Works

### 1. Document Ingestion (One-time)
When you upload a document:
- Parse → Chunk → Embed → Store in Qdrant

### 2. Query Time (Per conversation)
When a user asks a question:
1. Embed the user's question
2. Search Qdrant for similar chunks
3. Include top results as context in LLM prompt
4. LLM generates response using context

### 3. Response Generation
The LLM uses both:
- **Knowledge Base context**: From uploaded documents
- **System knowledge**: From training data
- **Conversation history**: From previous messages

## Integration Points

### In orchestrator.py
```python
from app.services.document_ingestion_service import DocumentIngestionService
from app.services.qdrant_service import QdrantService

class Orchestrator:
    def __init__(self):
        self.kb_service = DocumentIngestionService()
        self.qdrant_service = QdrantService()
    
    async def get_kb_context(self, query: str, num_results: int = 3) -> str:
        """Retrieve relevant context from knowledge base."""
        # Search Qdrant for similar documents
        results = await self.qdrant_service.search(query, limit=num_results)
        
        # Format results as context
        context = "\n".join([
            f"- {result}" for result in results
        ])
        
        return context
```

### In LLM Service
```python
async def generate_response(
    query: str, 
    context: str = None,
    conversation_history: List = None
) -> str:
    """Generate response with optional context."""
    
    messages = []
    
    # Add context if provided
    if context:
        messages.append({
            "role": "system",
            "content": f"Use this context to answer: {context}"
        })
    
    # Add conversation history
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add user query
    messages.append({
        "role": "user",
        "content": query
    })
    
    # Generate response
    response = await self.llm.create_chat_completion(
        model="gpt-4",
        messages=messages
    )
    
    return response.choices[0].message.content
```

## Implementation Example

### Simple Integration
```python
from app.services.qdrant_service import QdrantService
from app.services.llm_service import LLMService

class ConversationHandler:
    def __init__(self):
        self.qdrant = QdrantService()
        self.llm = LLMService()
    
    async def handle_query(self, user_query: str) -> str:
        # Step 1: Get context from knowledge base
        kb_results = await self.qdrant.search(user_query, limit=3)
        context = "\n".join(kb_results) if kb_results else ""
        
        # Step 2: Generate response with context
        if context:
            system_prompt = f"""You are a helpful assistant.
Use the following information to answer the user's question:

{context}

If the information doesn't help, use your general knowledge."""
        else:
            system_prompt = "You are a helpful assistant."
        
        response = await self.llm.generate_response(
            user_query,
            system_prompt=system_prompt
        )
        
        return response
```

### Advanced Integration with Metadata
```python
async def handle_query_with_metadata(self, user_query: str) -> dict:
    # Search with metadata filtering
    results = await self.qdrant.search(user_query, limit=5)
    
    # Process results
    context_blocks = []
    sources = set()
    
    for result in results:
        payload = result.get("payload", {})
        text = payload.get("text", "")
        metadata = payload.get("metadata", {})
        
        context_blocks.append(f"[{metadata.get('source', 'Unknown')}] {text}")
        sources.add(metadata.get("source", "Unknown"))
    
    context = "\n".join(context_blocks)
    
    # Generate response
    response = await self.llm.generate_response(
        user_query,
        context=context
    )
    
    return {
        "response": response,
        "context_used": len(context_blocks),
        "sources": list(sources)
    }
```

## KB-Aware Prompting

### Example System Prompt
```
You are a helpful customer support AI assistant for vocalQ.

You have access to the following documentation:
{knowledge_base_context}

Guidelines:
1. Always check the documentation first
2. If information is in the docs, use it
3. If not in docs, you can use general knowledge
4. Always cite your sources when using documentation
5. Be honest if information isn't available

User Query: {user_query}
```

### Context Formatting
```python
def format_kb_context(search_results: List[Dict]) -> str:
    """Format KB search results for LLM context."""
    
    formatted = "## Knowledge Base Context\n\n"
    
    for i, result in enumerate(search_results, 1):
        payload = result.get("payload", {})
        text = payload.get("text", "")
        metadata = payload.get("metadata", {})
        
        formatted += f"### Source {i}: {metadata.get('source', 'Unknown')}\n"
        formatted += f"**Category:** {metadata.get('category', 'General')}\n"
        formatted += f"**Content:** {text[:500]}...\n\n"
    
    return formatted
```

## Performance Optimization

### Caching KB Results
```python
from functools import lru_cache
import hashlib

class CachedKBService:
    def __init__(self):
        self.qdrant = QdrantService()
        self.cache = {}
    
    async def search_with_cache(self, query: str, ttl: int = 300) -> List[str]:
        # Generate cache key
        cache_key = hashlib.md5(query.encode()).hexdigest()
        
        # Check cache
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < ttl:
                return cached_result
        
        # Search if not cached or expired
        results = await self.qdrant.search(query, limit=3)
        self.cache[cache_key] = (results, time.time())
        
        return results
```

### Batch Processing
```python
async def process_multiple_queries(self, queries: List[str]):
    """Process multiple queries efficiently."""
    
    import asyncio
    
    # Search all queries in parallel
    search_tasks = [
        self.qdrant.search(q, limit=3) for q in queries
    ]
    results = await asyncio.gather(*search_tasks)
    
    # Process results
    for query, kb_results in zip(queries, results):
        context = "\n".join(kb_results)
        response = await self.llm.generate_response(query, context=context)
        yield {"query": query, "response": response}
```

## Monitoring and Debugging

### Log KB Usage
```python
import logging

logger = logging.getLogger(__name__)

class MonitoredKBService:
    def __init__(self):
        self.qdrant = QdrantService()
        self.llm = LLMService()
    
    async def handle_query_with_monitoring(self, query: str):
        # Search KB
        results = await self.qdrant.search(query, limit=3)
        
        logger.info(f"KB Search: '{query[:50]}...' → {len(results)} results")
        logger.debug(f"Top result: {results[0][:100]}..." if results else "No results")
        
        # Generate response
        context = "\n".join(results) if results else ""
        response = await self.llm.generate_response(query, context=context)
        
        logger.info(f"Response generated: {len(response)} chars")
        
        return response
```

## Best Practices

1. **Always search KB first** before making LLM calls
2. **Include relevance scores** in context
3. **Cite sources** from KB in responses
4. **Cache frequently asked questions**
5. **Monitor KB hit rate** for quality metrics
6. **Update KB regularly** with new documents
7. **Test quality** of retrieved context
8. **Log all KB searches** for analytics

## Testing Integration

```python
async def test_kb_integration():
    """Test KB integration with LLM."""
    
    service = ConversationHandler()
    
    # Test queries
    test_queries = [
        "How do I reset my password?",
        "What are your office hours?",
        "How much does it cost?",
    ]
    
    for query in test_queries:
        print(f"\n✓ Query: {query}")
        
        # Get KB context
        kb_results = await service.qdrant.search(query)
        print(f"  KB Results: {len(kb_results)}")
        
        # Generate response
        response = await service.handle_query(query)
        print(f"  Response: {response[:100]}...")
```

## Troubleshooting

### No KB results found
- Ensure documents are uploaded
- Check Qdrant is running
- Verify embeddings are being generated

### Poor response quality
- Improve document chunks
- Increase relevance threshold
- Add more diverse documents

### Slow queries
- Implement result caching
- Reduce context window size
- Use vector database pagination

---

See `README.md` for full documentation and configuration options.
