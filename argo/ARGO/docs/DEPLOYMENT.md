# ARGO Deployment Guide

Complete guide for deploying ARGO platform.

## Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key
- 4GB RAM minimum
- 10GB disk space

## Quick Deployment

### 1. Configure Environment

```bash
# Backend configuration
cp backend/.env.example backend/.env
nano backend/.env
```

Add your OpenAI API key:
```env
OPENAI_API_KEY=sk-...your-key-here
```

### 2. Start System

```bash
./scripts/start.sh
```

### 3. Access Application

- Frontend: http://localhost:5000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Manual Setup

### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p data logs temp

# Start server
python main.py
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev:client
```

## Production Deployment

### Backend (Production)

```bash
# Use production WSGI server
pip install gunicorn

# Start with gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### Frontend (Production)

```bash
# Build for production
npm run build

# Serve with nginx or similar
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /path/to/ARGO/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Environment Variables

### Backend Variables

```env
# Required
OPENAI_API_KEY=your_key_here

# Server
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production

# Database
DATABASE_PATH=./data/argo.db

# Security
CORS_ORIGINS=https://your-domain.com

# Features
RAG_TOP_K=5
RAG_USE_HYDE=true
RAG_USE_RERANKER=true
```

### Frontend Variables

```env
VITE_API_URL=https://your-domain.com/api
VITE_WS_URL=wss://your-domain.com/ws
VITE_ENV=production
```

## Docker Deployment (Optional)

### Backend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY core/ ./core/

CMD ["python", "main.py"]
```

### Frontend Dockerfile

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
```

### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
```

## System Verification

Run verification before deployment:

```bash
./scripts/verify.py
```

Expected: All checks should pass.

## Health Monitoring

### Check System Health

```bash
curl http://localhost:8000/health
```

### Check System Status

```bash
curl http://localhost:8000/api/status
```

## Troubleshooting

### Backend Issues

**Port already in use:**
```bash
lsof -i :8000
kill -9 <PID>
```

**Import errors:**
```bash
# Ensure PYTHONPATH includes core
export PYTHONPATH="${PYTHONPATH}:$(pwd)/core"
```

### Frontend Issues

**Build failures:**
```bash
rm -rf node_modules
npm install
npm run build
```

**Port conflicts:**
```bash
PORT=3000 npm run dev:client
```

### WebSocket Issues

- Verify backend is running
- Check firewall rules
- Ensure WebSocket upgrade headers
- Test with `wscat` tool

## Security Checklist

- [ ] Change default ports
- [ ] Configure HTTPS/SSL
- [ ] Set up firewall rules
- [ ] Configure rate limiting
- [ ] Enable request logging
- [ ] Set strong CORS policy
- [ ] Regular security updates
- [ ] Backup database regularly

## Performance Tuning

### Backend

- Use production WSGI server (gunicorn/uvicorn)
- Configure worker processes
- Enable gzip compression
- Set up caching layer (Redis)
- Database connection pooling

### Frontend

- Enable build optimization
- Configure CDN for assets
- Enable browser caching
- Minimize bundle size
- Lazy load components

## Backup Strategy

```bash
# Database backup
cp data/argo.db backups/argo_$(date +%Y%m%d).db

# Full backup
tar -czf argo_backup_$(date +%Y%m%d).tar.gz data/ logs/
```

## Monitoring

Recommended monitoring tools:
- Prometheus + Grafana
- ELK Stack for logs
- Sentry for error tracking
- Uptime monitoring service

## Scaling

### Horizontal Scaling

- Load balancer (nginx/HAProxy)
- Multiple backend instances
- Shared database
- Redis for session management

### Vertical Scaling

- Increase worker processes
- Allocate more RAM
- Faster CPU
- SSD storage

---

For additional support, consult the main README.md
