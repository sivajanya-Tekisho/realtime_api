# vocalQ - AI Voice Assistant

An intelligent voice assistant platform with RAG-powered knowledge base, real-time call handling, and comprehensive analytics dashboard.

## Overview

vocalQ is a full-stack AI voice assistant that combines:
- **AI-Powered Conversations** - GPT-4 with context-aware responses
- **Knowledge Base** - Upload documents for the AI to reference
- **Call Management** - Twilio integration for phone calls
- **Real-time Dashboard** - Monitor calls, transcripts, and analytics

## Project Structure

```
vocalQ/
├── backend/          # FastAPI server
├── frontend/         # React + TypeScript UI
├── venv/            # Python virtual environment
└── README.md        # This file
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Supabase account
- Qdrant Cloud account
- OpenAI API key
- Twilio account

### Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Copy .env.example to .env and fill in your credentials

# Run the server
python run_server.py
```

Server runs on: http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

UI runs on: http://localhost:5173

## Features

### 📞 Call Management
- Inbound/outbound call handling via Twilio
- Real-time transcription with Whisper
- Natural voice responses with OpenAI TTS
- Call history and analytics

### 🧠 Knowledge Base (RAG)
- Upload PDF, TXT, DOCX documents
- Automatic text extraction and chunking
- Semantic search with Qdrant vector database
- AI uses knowledge base for accurate responses

### 📊 Dashboard
- Live call monitoring
- Transcript viewing
- Call summaries
- Knowledge base management

### 🔒 Security
- Environment-based configuration
- Supabase Row Level Security
- API key authentication
- CORS protection

## Documentation

- **Backend**: See `backend/README.md`
- **API Docs**: http://localhost:8000/docs (when server is running)
- **Implementation Guides**: `backend/docs/`

## Tech Stack

### Backend
- FastAPI
- OpenAI (GPT-4, Whisper, TTS)
- Qdrant (Vector DB)
- Supabase (PostgreSQL)
- Twilio (Telephony)

### Frontend
- React 18
- TypeScript
- Vite
- TailwindCSS

## Environment Variables

Both backend and frontend require environment configuration. See:
- `backend/.env.example`
- `frontend/.env.example`

## Development

### Backend
```bash
cd backend
python run_server.py
```

### Frontend
```bash
cd frontend
npm run dev
```

### Testing
```bash
# Backend tests
cd backend
python scripts/verify_supabase.py

# Frontend build
cd frontend
npm run build
```

## Deployment

### Backend
- Recommended: Railway, Render, or AWS
- Use Gunicorn + Uvicorn for production
- Set environment variables in platform

### Frontend
- Recommended: Vercel, Netlify, or Cloudflare Pages
- Build command: `npm run build`
- Output directory: `dist`

## Common Issues

**Backend won't start**
- Check all environment variables are set
- Verify Supabase and Qdrant connections
- Ensure Python 3.10+ is installed

**Frontend can't connect to backend**
- Check backend is running on port 8000
- Verify CORS settings in backend
- Check API URLs in frontend code

**Uploads not working**
- Verify OpenAI API key has credits
- Check Qdrant connection
- Ensure file format is supported (PDF/TXT/DOCX)

## License

MIT

## Support

For detailed documentation, see the `backend/docs/` folder.
