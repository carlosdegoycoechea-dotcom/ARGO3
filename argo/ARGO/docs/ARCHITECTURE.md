# ARGO Platform Architecture

Technical architecture documentation for the ARGO enterprise platform.

## System Overview

ARGO is built on a modern full-stack architecture that separates concerns into distinct layers while maintaining seamless integration.

```
┌─────────────────────────────────────────────────────────┐
│                    Client Layer                          │
│  React SPA + TypeScript + Modern UI Components          │
└─────────────────────────────────────────────────────────┘
                         │
                         │ HTTP/WebSocket
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   API Layer                              │
│  FastAPI + REST Endpoints + WebSocket Gateway           │
└─────────────────────────────────────────────────────────┘
                         │
           ┌─────────────┼─────────────┐
           │             │             │
           ▼             ▼             ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │   Core   │  │   Data   │  │ External │
    │  Engine  │  │  Layer   │  │    AI    │
    └──────────┘  └──────────┘  └──────────┘
```

## Component Architecture

### Frontend Layer

**Technology Stack:**
- React 19+ with TypeScript
- Vite for build and development
- TanStack Query for server state
- Modern component library
- Tailwind CSS for styling

**Key Components:**

1. **Dashboard**
   - Main application container
   - Tab-based navigation
   - State management

2. **Chat Interface**
   - WebSocket client
   - Message management
   - Source attribution

3. **Document Manager**
   - File upload handler
   - Document list viewer
   - Search functionality

4. **Analytics Dashboard**
   - Real-time metrics
   - Chart visualizations
   - Cost tracking

**Data Flow:**
```
User Action → React Component → API Client → Backend
                    ↓
              State Update (TanStack Query)
                    ↓
              UI Re-render
```

### Backend Layer

**Technology Stack:**
- FastAPI framework
- Python 3.11+
- Uvicorn ASGI server
- Pydantic for validation

**Key Modules:**

1. **API Router**
   - REST endpoint handlers
   - Request validation
   - Response formatting

2. **WebSocket Manager**
   - Connection handling
   - Message broadcasting
   - State synchronization

3. **File Handler**
   - Upload processing
   - Validation
   - Storage management

**Request Flow:**
```
HTTP Request → FastAPI → Dependency Injection → Handler
                              ↓
                        Core Engine Call
                              ↓
                        Response Formation
```

### Core Engine

The core engine is the intelligent layer that powers ARGO's AI capabilities.

**Components:**

1. **RAG Engine**
   - Hypothetical Document Embeddings (HyDE)
   - Semantic search
   - Context ranking
   - Response generation

2. **Model Router**
   - LLM provider abstraction
   - Model selection logic
   - Fallback handling
   - Cost optimization

3. **Unified Database**
   - SQLite for metadata
   - Transaction management
   - Query optimization

4. **Document Processors**
   - PDF extraction
   - DOCX parsing
   - Excel analysis
   - Text chunking

**RAG Pipeline:**
```
Query → HyDE Generation → Vector Search → Reranking
                                   ↓
                          Context Assembly
                                   ↓
                          LLM Generation → Response
```

### Data Layer

**Storage:**
- **SQLite**: Metadata, tracking, analytics
- **File System**: Document storage
- **Vector Store**: Semantic embeddings

**Schema Design:**
```
projects
├── id (primary key)
├── name
├── type
└── metadata

documents
├── id (primary key)
├── project_id (foreign key)
├── filename
├── file_path
├── file_type
└── indexed_at

chunks
├── id (primary key)
├── document_id (foreign key)
├── content
├── embedding
└── metadata

api_usage
├── id (primary key)
├── project_id (foreign key)
├── model
├── tokens
├── cost
└── timestamp
```

## Communication Protocols

### REST API

**Characteristics:**
- JSON payload
- HTTP status codes
- Idempotent operations
- Stateless

**Example Flow:**
```
POST /api/chat
Content-Type: application/json

{
  "message": "What is the project status?",
  "use_hyde": true
}

→ Backend Processing →

200 OK
Content-Type: application/json

{
  "message": "Project is on track...",
  "sources": [...],
  "confidence": 0.92
}
```

### WebSocket

**Characteristics:**
- Full-duplex communication
- Real-time messaging
- Persistent connection
- Event-driven

**Message Flow:**
```
Client                          Server
  │                               │
  ├─── WS Connect ───────────────→│
  │                               │
  ├─── Send Message ─────────────→│
  │                               │
  │                         [Processing]
  │                               │
  │←─── Response ─────────────────┤
  │                               │
```

## Security Architecture

### Authentication Layer (Future)
- JWT tokens
- Session management
- Role-based access

### Input Validation
- Pydantic models
- File type checking
- Size limits
- Content sanitization

### CORS Policy
- Whitelisted origins
- Credential handling
- Preflight requests

## Scalability Design

### Horizontal Scaling
```
Load Balancer
     │
     ├─→ Backend Instance 1
     ├─→ Backend Instance 2
     └─→ Backend Instance N
          │
     Shared Database
```

### Caching Strategy
- API response caching
- Semantic cache for queries
- Static asset CDN

### Resource Management
- Connection pooling
- Worker process optimization
- Memory limits

## Error Handling

**Error Flow:**
```
Error Occurs
     │
     ├─→ Logging (file + console)
     │
     ├─→ Sanitize Message
     │
     └─→ Return to Client
          │
     Client Displays Error
          │
     User Notified
```

**Error Types:**
1. Validation Errors (400)
2. Authentication Errors (401)
3. Authorization Errors (403)
4. Not Found (404)
5. Server Errors (500)

## Monitoring & Observability

### Logging Layers
1. **Application Logs**: Business logic events
2. **Access Logs**: Request/response tracking
3. **Error Logs**: Exception tracking
4. **Performance Logs**: Timing metrics

### Metrics Collection
- Request latency
- Error rates
- Resource usage
- API call counts

### Health Checks
```
GET /health
→ Check:
  - Database connection
  - Core engine status
  - External API availability
  - Disk space
```

## Development Workflow

### Local Development
```bash
# Terminal 1: Backend
cd backend
python main.py

# Terminal 2: Frontend
cd frontend
npm run dev:client
```

### Code Organization
```
ARGO/
├── core/              # Business logic
│   ├── rag_engine.py
│   ├── model_router.py
│   └── database.py
├── backend/           # API layer
│   └── main.py
└── frontend/          # UI layer
    └── src/
```

### Dependency Management
- Backend: `requirements.txt`
- Frontend: `package.json`
- Core: Shared by backend

## Performance Characteristics

**Response Times:**
- Simple API call: <100ms
- Chat with RAG: 2-5 seconds
- Document upload: 1-3 seconds
- WebSocket message: <100ms

**Throughput:**
- Concurrent requests: 50+
- Document processing: ~100 chunks/s
- Messages/second: 20+

**Resource Usage:**
- RAM: 2-4 GB
- CPU: 1-2 cores
- Storage: 10GB+ (with documents)

## Technology Decisions

### Why FastAPI?
- Modern async support
- Auto-generated API docs
- High performance
- Type safety with Pydantic

### Why React?
- Component reusability
- Large ecosystem
- TypeScript support
- Modern tooling

### Why SQLite?
- No separate server needed
- Simple deployment
- Sufficient for use case
- Easy backup

### Why WebSocket?
- Real-time requirements
- Bi-directional communication
- Lower latency than polling

## Future Enhancements

### Planned Features
- Multi-user authentication
- Real-time collaboration
- Advanced analytics
- Mobile application
- Kubernetes deployment

### Scalability Path
- PostgreSQL migration
- Redis caching layer
- Microservices split
- Message queue (RabbitMQ/Kafka)

---

This architecture supports enterprise-grade deployment while maintaining flexibility for future growth.
