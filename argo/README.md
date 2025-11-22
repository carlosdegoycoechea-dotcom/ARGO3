# ARGO - Enterprise PMO Platform

Professional-grade Project Management Office platform with AI-powered capabilities.

## Quick Start

```bash
# Configure API key
nano ARGO/backend/.env
# Add: OPENAI_API_KEY=your_key_here

# Start system
cd ARGO
./scripts/start.sh
```

Access at: **http://localhost:5000**

## Documentation

- **Main README**: `ARGO/README.md`
- **Deployment Guide**: `ARGO/docs/DEPLOYMENT.md`
- **Architecture**: `ARGO/docs/ARCHITECTURE.md`
- **API Documentation**: http://localhost:8000/docs

## Project Structure

```
ARGO/
├── core/              # Core engine (RAG, Router, Database)
├── backend/           # FastAPI server
├── frontend/          # React application
├── docs/              # Documentation
└── scripts/           # Startup scripts
```

## Support

For detailed information, see `ARGO/README.md`

---

**Enterprise PMO Platform**
