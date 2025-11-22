# ARGO - Enterprise PMO Platform

**Professional-grade Project Management Office platform with AI-powered capabilities.**

---

## 🚀 INSTALACIÓN RÁPIDA (Windows)

**¿Primera vez instalando ARGO?** Sigue esta guía simple:

1. Descarga el ZIP: [Última versión](https://github.com/carlosdegoycoechea-dotcom/ARGO-v10/archive/refs/heads/claude/initial-setup-01LBBMg5Hz5CeVrQRjznjHD9.zip)
2. Extrae en `C:\Users\TU_USUARIO\ARGO\`
3. Ejecuta `INSTALAR.bat`
4. Edita `.env` y agrega tu OpenAI API key
5. Ejecuta `INICIAR.bat`

📖 **[Ver Guía Completa de Instalación](GUIA_INSTALACION_RAPIDA.md)**

---

## Overview

ARGO is a full-stack enterprise platform that combines modern web technologies with advanced AI capabilities to deliver intelligent project management solutions.

## Features

### Core Capabilities
- **Real-time Chat** - WebSocket-powered AI assistant with RAG
- **Document Management** - Upload, index, and search project documents
- **Analytics Dashboard** - Real-time cost tracking and usage metrics
- **RAG Engine** - Hypothetical Document Embeddings + Semantic Reranking
- **Professional UI** - Modern React with enterprise-grade components
- **REST + WebSocket API** - Full-featured backend

### Technical Stack

**Backend:**
- FastAPI (REST + WebSocket)
- Python 3.11+
- RAG Engine with semantic search
- SQLite Database
- LangChain + OpenAI integration

**Frontend:**
- React 19+
- TypeScript
- Vite build system
- TanStack Query for data management
- Modern UI component library
- Tailwind CSS

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- OpenAI API key

### Installation

```bash
# Navigate to project directory
cd ARGO

# Configure API key
cp backend/.env.example backend/.env
nano backend/.env  # Add your OPENAI_API_KEY

# Start the system
./scripts/start.sh
```

The application will be available at:
- **Frontend**: http://localhost:5000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Project Structure

```
ARGO/
├── core/              # Core engine (RAG, Model Router, Database)
├── backend/           # FastAPI backend server
├── frontend/          # React frontend application
├── docs/              # Documentation
└── scripts/           # Utility scripts
```

## Configuration

### Backend Configuration

Edit `backend/.env`:

```env
# Required
OPENAI_API_KEY=your_api_key_here

# Optional (defaults provided)
HOST=0.0.0.0
PORT=8000
DATABASE_PATH=./data/argo.db
```

### Frontend Configuration

Edit `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Usage

### Document Upload

1. Navigate to Documents section
2. Upload files via drag & drop or file picker
3. Supported formats: PDF, DOCX, XLSX, TXT, MD, CSV
4. Files are automatically indexed for search

### AI Chat

1. Navigate to Chat section
2. Ask questions about your documents
3. View sources and confidence scores
4. Get real-time responses

### Analytics

1. Navigate to Analytics section
2. Monitor API usage and costs
3. Track token consumption
4. View usage trends

## API Endpoints

### Health & Status
- `GET /health` - System health check
- `GET /api/status` - Detailed system status

### Project
- `GET /api/project` - Current project information

### Chat
- `POST /api/chat` - Send chat message (REST)
- `WS /ws/chat` - Real-time chat (WebSocket)

### Documents
- `GET /api/documents` - List all documents
- `POST /api/documents/upload` - Upload new document

### Analytics
- `GET /api/analytics` - Get analytics data

Full API documentation: http://localhost:8000/docs

## Development

### Backend Development

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev:client
```

## Security

- Environment variable isolation
- File type and size validation
- CORS configuration
- Input sanitization
- Secure error handling

## Performance

- Chat response: 2-5 seconds (with RAG)
- Document processing: ~100 chunks/second
- WebSocket latency: <100ms
- Concurrent users: Tested up to 50

## Architecture

The system uses a modern full-stack architecture:

- **Frontend**: React SPA with real-time WebSocket communication
- **Backend**: FastAPI server with REST and WebSocket endpoints
- **Core Engine**: Advanced RAG with HyDE and semantic reranking
- **Database**: SQLite for metadata and tracking
- **Vector Store**: Semantic search capabilities

## Support

For issues or questions:
- Check the documentation in `/docs`
- Review API documentation at `/docs` endpoint
- Run system verification: `./scripts/verify.py`

## License

Proprietary - All rights reserved

---

**Enterprise-Grade PMO Platform**
