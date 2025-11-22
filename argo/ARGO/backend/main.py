"""
ARGO - FastAPI Backend
Enterprise PMO Platform REST API + WebSocket
"""
import sys
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import asyncio
import json
from datetime import datetime
import traceback

# ARGO Core imports
from core.bootstrap import initialize_argo
from core.config import get_config
from core.logger import get_logger
from tools.extractors import extract_and_chunk, get_file_info

# Initialize
logger = get_logger("FastAPI")
app = FastAPI(
    title="ARGO API",
    version="1.0.0",
    description="Enterprise PMO Platform - REST API + WebSocket"
)

# CORS - Allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
argo_system = None
active_connections: List[WebSocket] = []


# ============================================================================
# MODELS
# ============================================================================

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    project_id: Optional[str] = None
    use_hyde: bool = True
    use_reranker: bool = True
    include_library: bool = True


class ChatResponse(BaseModel):
    message: str
    sources: List[Dict[str, Any]]
    confidence: Optional[float] = None
    timestamp: str
    metadata: Dict[str, Any] = {}


class ProjectInfo(BaseModel):
    id: str
    name: str
    project_type: str
    status: str
    created_at: str


class AnalyticsData(BaseModel):
    monthly_cost: float
    total_tokens: int
    total_requests: int
    daily_average_cost: float
    budget_remaining: float
    daily_usage: List[Dict[str, Any]]
    project_distribution: List[Dict[str, Any]]


class DocumentInfo(BaseModel):
    filename: str
    file_type: str
    chunk_count: int
    indexed_at: str
    file_size: int


class HealthCheck(BaseModel):
    status: str
    version: str
    timestamp: str
    components: Dict[str, bool]


# ============================================================================
# INITIALIZATION
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialize ARGO system on startup"""
    global argo_system

    try:
        logger.info("Starting ARGO Backend...")

        # Initialize ARGO
        config = get_config()
        logger.info(f"Initializing {config.version_display}")

        argo_system = initialize_argo()

        logger.info("✅ ARGO Backend initialized successfully")
        logger.info(f"✅ RAG Engine: Ready")
        logger.info(f"✅ Model Router: Ready")
        logger.info(f"✅ Database: Ready")

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    logger.info("Shutting down ARGO Backend...")

    # Close all WebSocket connections
    for connection in active_connections:
        try:
            await connection.close()
        except:
            pass

    logger.info("✅ Shutdown complete")


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_argo():
    """Get ARGO system instance"""
    if argo_system is None:
        raise HTTPException(status_code=500, detail="ARGO system not initialized")
    return argo_system


def get_config_instance():
    """Get config instance"""
    return get_config()


# ============================================================================
# HEALTH & STATUS
# ============================================================================

@app.get("/health", response_model=HealthCheck)
async def health_check(argo=Depends(get_argo), config=Depends(get_config_instance)):
    """Health check endpoint"""

    try:
        components = {
            "rag_engine": argo['project_components']['rag_engine'] is not None,
            "model_router": argo['model_router'] is not None,
            "database": argo['unified_db'] is not None,
            "project": argo['project'] is not None
        }

        return HealthCheck(
            status="healthy",
            version=config.version_display,
            timestamp=datetime.now().isoformat(),
            components=components
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
async def get_status(argo=Depends(get_argo)):
    """Get system status"""

    try:
        project = argo['project']
        unified_db = argo['unified_db']

        # Get stats
        files = unified_db.get_files(project_id=project['id'])
        total_chunks = sum(f.get('chunk_count', 0) for f in files)

        return {
            "status": "online",
            "project": {
                "id": project['id'],
                "name": project['name'],
                "type": project['project_type'],
                "status": project['status']
            },
            "stats": {
                "documents": len(files),
                "total_chunks": total_chunks,
                "active_connections": len(active_connections)
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROJECT ENDPOINTS
# ============================================================================

@app.get("/api/project", response_model=ProjectInfo)
async def get_project(argo=Depends(get_argo)):
    """Get current project info"""

    try:
        project = argo['project']

        return ProjectInfo(
            id=project['id'],
            name=project['name'],
            project_type=project['project_type'],
            status=project['status'],
            created_at=project.get('created_at', datetime.now().isoformat())
        )
    except Exception as e:
        logger.error(f"Get project failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CHAT ENDPOINTS
# ============================================================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, argo=Depends(get_argo)):
    """
    Chat endpoint - Process user message with RAG
    """

    try:
        project = argo['project']
        rag_engine = argo['project_components']['rag_engine']
        model_router = argo['model_router']

        logger.info(f"Processing chat query: {request.message[:50]}...")

        # Search RAG
        results, metadata = rag_engine.search(
            query=request.message,
            top_k=5,
            use_hyde=request.use_hyde,
            use_reranker=request.use_reranker,
            include_library=request.include_library
        )

        # Format context
        context = rag_engine.format_context(results)

        # Build messages for LLM
        system_prompt = f"""You are ARGO, an enterprise project management assistant.

Use the following context to answer the user's question accurately and professionally.

{context}

Guidelines:
- Answer based on the context provided
- Be concise and professional
- Cite sources when appropriate
- If information is not in context, say so clearly
- Use proper business terminology"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.message}
        ]

        # Get response from router
        response = model_router.run(
            task_type="chat",
            project_id=project['id'],
            messages=messages
        )

        # Extract sources
        sources = [
            {
                "source": r.metadata.get('source', 'Unknown'),
                "score": float(r.score),
                "rerank_score": float(r.rerank_score) if r.rerank_score else None,
                "is_library": r.is_library
            }
            for r in results
        ]

        # Calculate average confidence
        avg_confidence = sum(r.score for r in results) / len(results) if results else 0.0

        logger.info(f"✅ Chat response generated ({len(sources)} sources)")

        return ChatResponse(
            message=response.content,
            sources=sources,
            confidence=avg_confidence,
            timestamp=datetime.now().isoformat(),
            metadata={
                "used_hyde": request.use_hyde,
                "used_reranker": request.use_reranker,
                "included_library": request.include_library,
                "num_results": len(results)
            }
        )

    except Exception as e:
        logger.error(f"Chat failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")


# ============================================================================
# WEBSOCKET CHAT
# ============================================================================

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat
    """
    await websocket.accept()
    active_connections.append(websocket)

    logger.info(f"WebSocket connected. Active connections: {len(active_connections)}")

    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)

            logger.info(f"WebSocket message received: {message_data.get('message', '')[:50]}...")

            # Process via chat endpoint logic
            try:
                request = ChatRequest(**message_data)

                # Get ARGO system
                argo = argo_system
                project = argo['project']
                rag_engine = argo['project_components']['rag_engine']
                model_router = argo['model_router']

                # Search RAG
                results, metadata = rag_engine.search(
                    query=request.message,
                    top_k=5,
                    use_hyde=request.use_hyde,
                    use_reranker=request.use_reranker,
                    include_library=request.include_library
                )

                # Format context
                context = rag_engine.format_context(results)

                # Build messages
                system_prompt = f"""You are ARGO, an enterprise project management assistant.

Use the following context to answer the user's question accurately and professionally.

{context}

Guidelines:
- Answer based on the context provided
- Be concise and professional
- Cite sources when appropriate
- If information is not in context, say so clearly
- Use proper business terminology"""

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.message}
                ]

                # Get response
                response = model_router.run(
                    task_type="chat",
                    project_id=project['id'],
                    messages=messages
                )

                # Extract sources
                sources = [
                    {
                        "source": r.metadata.get('source', 'Unknown'),
                        "score": float(r.score),
                        "rerank_score": float(r.rerank_score) if r.rerank_score else None,
                        "is_library": r.is_library
                    }
                    for r in results
                ]

                # Calculate confidence
                avg_confidence = sum(r.score for r in results) / len(results) if results else 0.0

                # Send response
                response_data = {
                    "type": "message",
                    "message": response.content,
                    "sources": sources,
                    "confidence": avg_confidence,
                    "timestamp": datetime.now().isoformat()
                }

                await websocket.send_json(response_data)
                logger.info("✅ WebSocket response sent")

            except Exception as e:
                error_msg = {
                    "type": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send_json(error_msg)
                logger.error(f"WebSocket processing error: {e}", exc_info=True)

    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Active connections: {len(active_connections)}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        if websocket in active_connections:
            active_connections.remove(websocket)


# ============================================================================
# DOCUMENT ENDPOINTS
# ============================================================================

@app.get("/api/documents", response_model=List[DocumentInfo])
async def get_documents(argo=Depends(get_argo)):
    """Get all documents for current project"""

    try:
        project = argo['project']
        unified_db = argo['unified_db']

        files = unified_db.get_files(project_id=project['id'])

        return [
            DocumentInfo(
                filename=f['filename'],
                file_type=f['file_type'],
                chunk_count=f.get('chunk_count', 0),
                indexed_at=f['indexed_at'],
                file_size=f.get('file_size', 0)
            )
            for f in files
        ]
    except Exception as e:
        logger.error(f"Get documents failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    argo=Depends(get_argo),
    config=Depends(get_config_instance)
):
    """
    Upload and process document
    """

    try:
        project = argo['project']
        unified_db = argo['unified_db']

        logger.info(f"Processing upload: {file.filename}")

        # Validate file type
        allowed_extensions = ['pdf', 'docx', 'xlsx', 'txt', 'md', 'csv']
        file_ext = file.filename.split('.')[-1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )

        # Save temporarily
        temp_dir = Path(config.get("paths.temp_dir", "/tmp/argo"))
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / file.filename

        with open(temp_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        # Get file info
        file_info = get_file_info(str(temp_path))

        # Extract and chunk
        chunks = extract_and_chunk(
            file_path=str(temp_path),
            file_type=file_ext,
            metadata={
                'project_id': project['id'],
                'source': file.filename,
                'uploaded_at': datetime.now().isoformat()
            }
        )

        # TODO: Index chunks in vectorstore
        # For now we just register in database

        # Register in database
        unified_db.add_file(
            project_id=project['id'],
            filename=file.filename,
            file_path=str(temp_path),
            file_type=file_ext,
            file_hash=file_info['file_hash'],
            file_size=file_info['size_bytes'],
            chunk_count=len(chunks)
        )

        logger.info(f"✅ Document processed: {file.filename} ({len(chunks)} chunks)")

        return {
            "success": True,
            "filename": file.filename,
            "chunks": len(chunks),
            "size_kb": file_info['size_kb'],
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/api/analytics", response_model=AnalyticsData)
async def get_analytics(argo=Depends(get_argo)):
    """Get analytics data"""

    try:
        project = argo['project']
        unified_db = argo['unified_db']

        # Get API usage stats
        usage_stats = unified_db.get_api_usage_summary(
            project_id=project['id'],
            days=30
        )

        # Get daily usage for last 7 days
        daily_stats = unified_db.get_daily_usage(
            project_id=project['id'],
            days=7
        )

        # Get project distribution
        project_dist = unified_db.get_project_cost_distribution(days=30)

        # Calculate metrics
        monthly_cost = usage_stats.get('total_cost', 0)
        total_tokens = usage_stats.get('total_tokens', 0)
        total_requests = usage_stats.get('total_requests', 0)

        budget = 200.0  # Default budget
        daily_avg = monthly_cost / 30 if monthly_cost else 0
        remaining = budget - monthly_cost

        return AnalyticsData(
            monthly_cost=monthly_cost,
            total_tokens=total_tokens,
            total_requests=total_requests,
            daily_average_cost=daily_avg,
            budget_remaining=remaining,
            daily_usage=daily_stats or [],
            project_distribution=project_dist or []
        )

    except Exception as e:
        logger.error(f"Analytics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
