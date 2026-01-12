# vocalQ - AI Voice Assistant Backend

A production-ready FastAPI backend for an AI-powered voice assistant with RAG (Retrieval-Augmented Generation) capabilities, Twilio integration, and real-time conversation management.

## Features

- 🎙️ **Voice Call Integration** - Twilio-powered inbound/outbound calls
- 🧠 **RAG Knowledge Base** - Upload documents (PDF, TXT, DOCX) for AI context
- 💬 **Real-time Transcription** - Faster Whisper for speech-to-text
- 🔊 **Text-to-Speech** - OpenAI TTS for natural voice responses
- 📊 **Call Analytics** - Store and analyze conversation transcripts
- 🔍 **Vector Search** - Qdrant for semantic document retrieval
- 🗄️ **Database** - Supabase (PostgreSQL) for call logs and summaries

## Tech Stack

- **Framework**: FastAPI
- **AI/ML**: OpenAI GPT-4, Whisper, TTS
- **Vector DB**: Qdrant Cloud
- **Database**: Supabase (PostgreSQL)
- **Telephony**: Twilio
- **Speech**: Faster Whisper (local), OpenAI Whisper API

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/          # API route handlers
│   │   │   ├── admin.py        # Admin endpoints (list, delete)
│   │   │   ├── calls.py        # Call management
│   │   │   ├── knowledge_base.py # Document upload/management
│   │   │   └── websocket.py    # Real-time audio streaming
│   │   └── api.py              # API router configuration
│   ├── core/
│   │   └── config.py           # Settings and environment variables
│   ├── db/
│   │   ├── base.py             # Database models
│   │   └── session.py          # Database session management
│   ├── services/
│   │   ├── audio_service.py    # Audio processing (Whisper, TTS)
│   │   ├── document_ingestion_service.py # Document parsing & chunking
│   │   ├── llm_service.py      # OpenAI GPT integration
│   │   └── qdrant_service.py   # Vector database operations
│   └── main.py                 # FastAPI application entry point
├── docs/                       # Documentation
├── knowledge_base/
│   ├── documents/              # Static knowledge documents
│   └── uploaded/               # User-uploaded documents
├── scripts/                    # Utility scripts
├── .env                        # Environment variables (not in git)
├── requirements.txt            # Python dependencies
├── run_server.py              # Server startup script
└── schema.sql                 # Database schema

```

## Setup

### 1. Prerequisites

- Python 3.10+
- PostgreSQL (via Supabase)
- Qdrant Cloud account
- OpenAI API key
- Twilio account

### 2. Environment Variables

Create a `.env` file in the backend directory:

```env
# Project
PROJECT_NAME=vocalQ
API_V1_STR=/api/v1
BACKEND_CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number
TWILIO_VERIFY_SERVICE_SID=your_verify_sid

# Qdrant
QDRANT_URL=your_qdrant_cluster_url
QDRANT_API_KEY=your_qdrant_api_key

# Models
WHISPER_MODEL=tiny
VAD_AGGRESSIVENESS=3
```

### 3. Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Database Setup

Run the SQL schema in your Supabase project:

```bash
# Execute schema.sql in Supabase SQL Editor
```

### 5. Run the Server

```bash
python run_server.py
```

The server will start on `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Key Endpoints

### Knowledge Base
- `POST /api/v1/admin/knowledge/upload` - Upload document
- `GET /api/v1/admin/knowledge/list` - List documents
- `DELETE /api/v1/admin/knowledge/{doc_id}` - Delete document

### Calls
- `POST /api/v1/calls/incoming` - Handle incoming Twilio call
- `GET /api/v1/calls/history` - Get call history
- `GET /api/v1/calls/{call_id}` - Get call details

### WebSocket
- `WS /api/v1/ws/audio` - Real-time audio streaming

## Knowledge Base

### Supported Formats
- PDF (`.pdf`)
- Text (`.txt`)
- Word Documents (`.docx`)

### Upload Process
1. Document is parsed and text extracted
2. Text is chunked (1000 chars, 200 overlap)
3. Chunks are embedded using OpenAI embeddings
4. Vectors stored in Qdrant for semantic search
5. Original file saved to `knowledge_base/uploaded/`

### Usage in Calls
During calls, the AI automatically searches the knowledge base for relevant context based on the conversation, enabling accurate and informed responses.

## Scripts

### Utility Scripts (in `scripts/`)
- `inspect_db.py` - Inspect database records
- `populate_rag.py` - Populate knowledge base with sample data
- `simulate_call.py` - Test call flow without Twilio
- `verify_phase2.py` - Verify Phase 2 implementation
- `verify_supabase.py` - Test Supabase connection

## Development

### Code Style
- Follow PEP 8
- Use type hints
- Document functions with docstrings

### Testing
```bash
# Run specific test
python scripts/verify_supabase.py
```

## Deployment

### Production Checklist
- [ ] Set `DEBUG=False` in production
- [ ] Use production-grade ASGI server (Gunicorn + Uvicorn)
- [ ] Enable HTTPS
- [ ] Set up proper CORS origins
- [ ] Use environment-specific `.env` files
- [ ] Set up logging and monitoring
- [ ] Configure rate limiting
- [ ] Set up backup for Supabase and Qdrant

### Recommended Deployment
- **Platform**: Railway, Render, or AWS
- **Server**: Gunicorn with Uvicorn workers
- **Environment**: Docker container

## Troubleshooting

### Common Issues

**1. OpenAI API Errors**
- Check API key is valid
- Verify account has credits
- Check rate limits

**2. Qdrant Connection Failed**
- Verify Qdrant URL and API key
- Check network connectivity
- Ensure collection exists

**3. Twilio Webhook Errors**
- Ensure server is publicly accessible
- Use ngrok for local testing
- Verify webhook URLs in Twilio console

**4. Database Connection Issues**
- Check Supabase URL and key
- Verify RLS policies are configured
- Ensure schema is up to date

## License

MIT

## Support

For issues and questions, please check the documentation in the `docs/` folder.
