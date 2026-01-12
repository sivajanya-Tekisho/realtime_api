# Knowledge Base Management System

## Overview

The vocalQ Knowledge Base is a complete RAG (Retrieval-Augmented Generation) system that allows you to upload documents manually and have them automatically processed for semantic search and context retrieval in voice conversations.

## Features

✅ **Document Upload** - Upload PDFs, TXT, and DOCX files
✅ **Automatic Parsing** - Extracts text from multiple document formats
✅ **Smart Chunking** - Splits documents into overlapping chunks for better context
✅ **Embedding Generation** - Uses OpenAI embeddings for semantic understanding
✅ **Vector Storage** - Stores in Qdrant for fast similarity search
✅ **Document Management** - List and delete documents as needed

## Folder Structure

```
backend/knowledge_base/
├── documents/          # Documentation and guidelines
└── uploaded/          # Uploaded documents (organized by doc_id)
    ├── doc_id_1/
    │   ├── file.pdf
    │   └── metadata.json
    └── doc_id_2/
        ├── file.docx
        └── metadata.json
```

## Supported File Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| PDF | .pdf | Extracts text from all pages |
| Plain Text | .txt | UTF-8 and Latin-1 encoding supported |
| Word Document | .docx | Extracts text from paragraphs |

## API Endpoints

### 1. Upload Document
```
POST /api/knowledge-base/upload
```

**Description**: Upload a document to the knowledge base

**Parameters**:
- `file` (required): Document file (PDF, TXT, or DOCX)
- `category` (optional): Category for the document
- `description` (optional): Description of the document content

**Example**:
```bash
curl -X POST "http://localhost:8000/api/knowledge-base/upload" \
  -F "file=@document.pdf" \
  -F "category=support" \
  -F "description=Customer support documentation"
```

**Response**:
```json
{
  "success": true,
  "file_name": "document.pdf",
  "doc_id": "a1b2c3d4e5f6",
  "chunks_created": 15,
  "points_stored": 15,
  "saved_path": "/path/to/knowledge_base/uploaded/a1b2c3d4e5f6/document.pdf",
  "message": "Successfully ingested document.pdf with 15 chunks"
}
```

### 2. List Documents
```
GET /api/knowledge-base/documents
```

**Description**: Get list of all ingested documents

**Response**:
```json
{
  "success": true,
  "count": 2,
  "documents": [
    {
      "doc_id": "a1b2c3d4e5f6",
      "files": ["document.pdf"],
      "file_count": 1
    },
    {
      "doc_id": "x7y8z9a0b1c2",
      "files": ["guide.txt"],
      "file_count": 1
    }
  ]
}
```

### 3. Delete Document
```
DELETE /api/knowledge-base/documents/{doc_id}
```

**Description**: Delete a document and all its chunks

**Parameters**:
- `doc_id`: Document ID to delete

**Response**:
```json
{
  "success": true,
  "doc_id": "a1b2c3d4e5f6",
  "message": "Successfully deleted document a1b2c3d4e5f6"
}
```

### 4. Knowledge Base Info
```
GET /api/knowledge-base/info
```

**Description**: Get knowledge base statistics and configuration

**Response**:
```json
{
  "status": "operational",
  "total_documents": 2,
  "total_files": 2,
  "supported_formats": ["pdf", "txt", "docx"],
  "chunk_size": 1000,
  "chunk_overlap": 200,
  "embedding_model": "OpenAI text-embedding-3-small",
  "vector_database": "Qdrant"
}
```

## How It Works

### 1. Document Upload
When you upload a document:
```
User Upload → Temporary Storage → Parsing → Chunking → Embedding → Vector Storage
```

### 2. Document Parsing
- **PDF**: Uses PyPDF2 to extract text from all pages
- **TXT**: Reads file with UTF-8 or Latin-1 encoding
- **DOCX**: Uses python-docx to extract paragraph text

### 3. Chunking Strategy
Documents are split into overlapping chunks:
- **Chunk Size**: 1000 characters
- **Overlap**: 200 characters
- **Strategy**: Sentence-aware (tries to break at sentence boundaries)

Example:
```
Original: "The quick brown fox... [continues for 1500 chars]"

Chunk 1: "The quick brown fox... [0-1000 chars]"
Chunk 2: "[800-1800 chars]"  (overlaps by 200 chars with Chunk 1)
Chunk 3: "[1600-2100 chars]" (overlaps by 200 chars with Chunk 2)
```

### 4. Embedding Generation
Each chunk is embedded using **OpenAI's text-embedding-3-small** model:
- Dimension: 1536
- Distance metric: Cosine similarity
- Cost efficient for large documents

### 5. Vector Storage in Qdrant
Points are stored with:
- **Vector**: 1536-dimensional embedding
- **Payload**: Full text + metadata
- **Metadata**: Source, doc_id, category, chunk info

## Configuration

Edit `DocumentIngestionService` in `app/services/document_ingestion_service.py`:

```python
class DocumentIngestionService:
    def __init__(self):
        self.chunk_size = 1000      # Adjust chunk size
        self.chunk_overlap = 200    # Adjust overlap
```

## Usage Examples

### Python
```python
from app.services.document_ingestion_service import DocumentIngestionService

service = DocumentIngestionService()

# Ingest a document
result = service.ingest_document(
    file_path="/path/to/doc.pdf",
    file_name="doc.pdf",
    metadata={"category": "support", "department": "sales"}
)

# List documents
docs = service.list_documents()

# Delete document
service.delete_document("a1b2c3d4e5f6")
```

### cURL
```bash
# Upload document
curl -X POST "http://localhost:8000/api/knowledge-base/upload" \
  -F "file=@support_guide.pdf" \
  -F "category=support"

# List documents
curl -X GET "http://localhost:8000/api/knowledge-base/documents"

# Delete document
curl -X DELETE "http://localhost:8000/api/knowledge-base/documents/a1b2c3d4e5f6"

# Get info
curl -X GET "http://localhost:8000/api/knowledge-base/info"
```

## Integration with LLM

The knowledge base integrates with the LLM service for context retrieval:

```python
# In your conversation flow:
1. User asks question
2. Search knowledge base: llm_service.search_knowledge_base(query)
3. Get top results with similarity scores
4. Include in LLM context for better responses
5. Respond with context-aware answer
```

## Performance Notes

- **Embedding Cost**: ~$0.02 per 1M tokens with text-embedding-3-small
- **Storage**: Each 1KB of text ≈ 1 Qdrant point
- **Search Speed**: <100ms typical for similarity search
- **Memory**: Minimal, as vectors are stored in Qdrant

## Troubleshooting

### Issue: "Unsupported file format"
**Solution**: Only PDF, TXT, and DOCX are supported. Convert your file format first.

### Issue: "Could not extract text from document"
**Solution**: 
- Ensure PDF is not scanned/image-based (need OCR)
- Check file is not corrupted
- Verify file encoding for TXT files

### Issue: Embeddings failing
**Solution**:
- Check OpenAI API key in `.env`
- Verify API key has embeddings permission
- Check rate limits

### Issue: Qdrant connection error
**Solution**:
- Verify Qdrant is running: `docker ps`
- Check `QDRANT_URL` and `QDRANT_API_KEY` in `.env`
- Restart Qdrant service

## Best Practices

1. **Document Size**: Optimal 5-50 MB. Very large files (>100MB) should be split
2. **Content Quality**: Better structured documents = better chunks
3. **Categories**: Use consistent category names for better filtering
4. **Metadata**: Add meaningful descriptions for easy retrieval
5. **Regular Updates**: Keep documents current, delete outdated ones

## Future Enhancements

- [ ] OCR support for scanned PDFs
- [ ] Support for additional formats (PPTX, HTML, CSV)
- [ ] Document preview and search
- [ ] Batch upload with progress tracking
- [ ] Custom chunking strategies
- [ ] Metadata-based filtering in search
- [ ] Document versioning
