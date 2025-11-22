"""
ARGO - Unified Database System
Centralized SQLite database for projects, memory, and analysis
Corporate-grade data persistence layer
"""
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from contextlib import contextmanager

from core.logger import get_logger

logger = get_logger("Database")


class UnifiedDatabase:
    """
    Centralized SQLite database for projects, memory, and analysis
    Corporate-grade data persistence layer
    
    New in Clean: Analytics queries for usage monitoring
    """
    """
    Base de datos centralizada con:
    - Gestión de proyectos
    - Memoria de conversaciones
    - Registro de análisis
    - Logs de operaciones
    - Índices optimizados
    """
    
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        logger.info(f"Database initialized: {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Context manager para conexiones SQLite"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error en transacción DB", exc_info=True)
            raise
        finally:
            conn.close()
    
    def _init_schema(self):
        """Inicializa esquema completo de la base de datos"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            
            # TABLA: Proyectos (F1 Architecture)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    base_path TEXT NOT NULL,
                    description TEXT,
                    project_type TEXT DEFAULT 'standard',
                    status TEXT DEFAULT 'active',
                    drive_enabled BOOLEAN DEFAULT 0,
                    drive_folder_id TEXT,
                    drive_type TEXT DEFAULT 'none',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata_json TEXT
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_project_name ON projects(name)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_project_type ON projects(project_type)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_project_status ON projects(status, last_accessed)")
            
            # TABLA: Archivos por proyecto (F1 Architecture)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_type TEXT,
                    file_hash TEXT,
                    file_size INTEGER,
                    status TEXT DEFAULT 'indexed',
                    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    chunk_count INTEGER DEFAULT 0,
                    metadata_json TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_file_unique ON files(project_id, file_path)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_file_project ON files(project_id, indexed_at)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_file_hash ON files(file_hash)")
            
            # TABLA: Conversaciones
            cur.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    title TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    tags_json TEXT,
                    summary TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_conv_unique ON conversations(project_id, session_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_conv_project ON conversations(project_id, updated_at)")
            
            # TABLA: Mensajes individuales (F1 Architecture)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tokens_in INTEGER DEFAULT 0,
                    tokens_out INTEGER DEFAULT 0,
                    metadata_json TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id, created_at)")
            
            # TABLA: Documentos (F1 Architecture)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER NOT NULL,
                    project_id TEXT NOT NULL,
                    title TEXT,
                    doc_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_doc_file ON documents(file_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_doc_project ON documents(project_id)")
            
            # TABLA: Chunks de documentos (F1 Architecture)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    project_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    vector_id TEXT,
                    metadata_json TEXT,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_chunk_doc ON chunks(document_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_chunk_project ON chunks(project_id, chunk_index)")
            
            # TABLA: Resultados de análisis
            cur.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    analysis_type TEXT NOT NULL,
                    query TEXT,
                    results TEXT NOT NULL,
                    confidence REAL,
                    model_used TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata_json TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_analysis_project ON analysis_results(project_id, created_at)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_analysis_type ON analysis_results(analysis_type)")
            
            # TABLA: API Usage (F1 Architecture - CRÍTICO)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    project_id TEXT,
                    conversation_id INTEGER,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    prompt_tokens INTEGER DEFAULT 0,
                    completion_tokens INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    cost_estimated REAL DEFAULT 0.0,
                    metadata_json TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON api_usage(timestamp)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_usage_project ON api_usage(project_id, timestamp)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_usage_provider ON api_usage(provider, model, timestamp)")
            
            # TABLA: Métricas del sistema
            cur.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    project_id TEXT,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    context_json TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(name, timestamp)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_metrics_project ON metrics(project_id, timestamp)")
            
            # TABLA: Logs del sistema
            cur.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    logger TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs(level, timestamp)")
            
            # TABLA: Notas del proyecto
            cur.execute("""
                CREATE TABLE IF NOT EXISTS project_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_notes_project ON project_notes(project_id, updated_at)")
            
            # TABLA: Feedback
            cur.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    query TEXT,
                    answer TEXT,
                    correction TEXT,
                    rating TEXT CHECK(rating IN ('up','down')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_feedback_project ON feedback(project_id, created_at)")
            
            logger.debug("Esquema de base de datos inicializado")
    
    # ==========================================
    # PROYECTOS
    # ==========================================
    
    def create_project(
        self,
        name: str,
        path: str = None,
        base_path: str = None,
        description: str = "",
        project_type: str = "standard",
        project_id: str = None,
        metadata: Dict = None
    ) -> str:
        """
        Crea un nuevo proyecto (F1 Architecture con compatibilidad v8)
        
        Args:
            name: Nombre del proyecto
            path: Ruta (legacy, se convierte a base_path)
            base_path: Ruta base (F1)
            description: Descripción
            project_type: Tipo (standard, ed_sto, library)
            project_id: ID personalizado (si no se provee, se genera de name)
            metadata: Metadatos adicionales
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            
            # Compatibilidad: path -> base_path
            if path and not base_path:
                base_path = path
            elif not base_path:
                base_path = f"projects/{name}"
            
            # Generar project_id si no se provee
            if not project_id:
                import re
                project_id = re.sub(r'[^a-zA-Z0-9_-]', '_', name).upper()
            
            cur.execute("""
                INSERT INTO projects (id, name, base_path, description, project_type, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (project_id, name, base_path, description, project_type, json.dumps(metadata or {})))
            
            logger.info(f"Proyecto creado: {name}", project_id=project_id, project_type=project_type)
            return project_id
    
    def get_project(self, name: str = None, project_id: str = None) -> Optional[Dict]:
        """
        Obtiene información de un proyecto por nombre o ID (F1 Architecture)
        
        Args:
            name: Nombre del proyecto
            project_id: ID del proyecto (F1)
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            
            if project_id:
                cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            elif name:
                cur.execute("SELECT * FROM projects WHERE name = ?", (name,))
            else:
                return None
            
            row = cur.fetchone()
            
            if row:
                # Actualizar last_accessed
                update_id = row['id']
                cur.execute(
                    "UPDATE projects SET last_accessed = CURRENT_TIMESTAMP WHERE id = ?",
                    (update_id,)
                )
                return dict(row)
            return None
    
    def list_projects(self, active_only: bool = True, project_type: str = None) -> List[Dict]:
        """
        Lista todos los proyectos (F1 Architecture)
        
        Args:
            active_only: Solo proyectos activos
            project_type: Filtrar por tipo (standard, ed_sto, library)
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            
            query = "SELECT * FROM projects WHERE 1=1"
            params = []
            
            if active_only:
                query += " AND status = 'active'"
            
            if project_type:
                query += " AND project_type = ?"
                params.append(project_type)
            
            query += " ORDER BY last_accessed DESC"
            
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]
    
    # ==========================================
    # ARCHIVOS
    # ==========================================
    
    def register_file(
        self,
        project_id: str,
        filename: str,
        file_path: str,
        file_type: str,
        file_hash: str,
        file_size: int,
        chunk_count: int,
        metadata: Dict = None
    ):
        """Registra un archivo indexado (F1 Architecture)"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO files 
                (project_id, filename, file_path, file_type, file_hash, file_size, chunk_count, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (project_id, filename, file_path, file_type, file_hash, file_size, 
                  chunk_count, json.dumps(metadata or {})))
            
            logger.debug(f"Archivo registrado: {filename}", project_id=project_id)
    
    def get_project_files(self, project_id: str) -> List[Dict]:
        """Lista archivos de un proyecto (F1 Architecture)"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM files 
                WHERE project_id = ? 
                ORDER BY indexed_at DESC
            """, (project_id,))
            
            return [dict(row) for row in cur.fetchall()]
    
    def file_is_indexed(self, project_id: str, file_hash: str) -> bool:
        """Verifica si un archivo ya está indexado (F1 Architecture)"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*) as count FROM files 
                WHERE project_id = ? AND file_hash = ?
            """, (project_id, file_hash))
            
            return cur.fetchone()['count'] > 0
    
    # ==========================================
    # CONVERSACIONES
    # ==========================================
    
    def save_conversation(
        self,
        project_id: str,
        session_id: str,
        messages: List[Dict],
        summary: str = ""
    ):
        """Guarda una conversación (F1 Architecture compatible)"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            
            # Para compatibilidad, guardamos en formato JSON como antes
            cur.execute("""
                INSERT OR REPLACE INTO conversations 
                (project_id, session_id, message_count, summary, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (project_id, session_id, len(messages), summary))
            
            conv_id = cur.lastrowid
            
            # F1: También guardamos mensajes individuales
            for msg in messages[-5:]:  # Solo últimos 5 para no sobrecargar
                cur.execute("""
                    INSERT INTO messages (conversation_id, role, content, tokens_in, tokens_out)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    conv_id,
                    msg.get('role', 'user'),
                    msg.get('content', ''),
                    msg.get('tokens_in', 0),
                    msg.get('tokens_out', 0)
                ))
            
            logger.debug(f"Conversación guardada", session_id=session_id, messages=len(messages))
    
    def load_conversation(self, project_id: str, session_id: str) -> Optional[List[Dict]]:
        """Carga una conversación (F1 Architecture compatible)"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            
            # Buscar conversación
            cur.execute("""
                SELECT id, message_count FROM conversations 
                WHERE project_id = ? AND session_id = ?
            """, (project_id, session_id))
            
            row = cur.fetchone()
            if not row:
                return None
            
            conv_id = row['id']
            
            # F1: Cargar mensajes individuales
            cur.execute("""
                SELECT role, content, tokens_in, tokens_out, created_at
                FROM messages
                WHERE conversation_id = ?
                ORDER BY created_at ASC
            """, (conv_id,))
            
            messages = []
            for msg_row in cur.fetchall():
                messages.append({
                    'role': msg_row['role'],
                    'content': msg_row['content'],
                    'tokens_in': msg_row['tokens_in'],
                    'tokens_out': msg_row['tokens_out']
                })
            
            return messages if messages else None
    
    def list_conversations(self, project_id: str, limit: int = 20) -> List[Dict]:
        """Lista conversaciones de un proyecto (F1 Architecture)"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, session_id, summary, message_count, updated_at, title
                FROM conversations
                WHERE project_id = ?
                ORDER BY updated_at DESC
                LIMIT ?
            """, (project_id, limit))
            
            return [dict(row) for row in cur.fetchall()]
    
    # ==========================================
    # ANÁLISIS
    # ==========================================
    
    def save_analysis(self, project_id: str, analysis_type: str, query: str,
                     results: Dict, confidence: float, model_used: str, metadata: Dict = None):
        """Guarda resultado de análisis"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO analysis_results 
                (project_id, analysis_type, query, results, confidence, model_used, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (project_id, analysis_type, query, json.dumps(results), 
                  confidence, model_used, json.dumps(metadata or {})))
            
            logger.debug(f"Análisis guardado", type=analysis_type, confidence=confidence)
    
    def get_recent_analyses(self, project_id: str, analysis_type: str = None, limit: int = 10) -> List[Dict]:
        """Obtiene análisis recientes"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            
            if analysis_type:
                cur.execute("""
                    SELECT * FROM analysis_results 
                    WHERE project_id = ? AND analysis_type = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (project_id, analysis_type, limit))
            else:
                cur.execute("""
                    SELECT * FROM analysis_results 
                    WHERE project_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (project_id, limit))
            
            return [dict(row) for row in cur.fetchall()]
    
    # ==========================================
    # NOTAS
    # ==========================================
    
    def save_note(self, project_id: str, title: str, content: str, tags: str = ""):
        """Guarda una nota"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO project_notes (project_id, title, content, tags)
                VALUES (?, ?, ?, ?)
            """, (project_id, title, content, tags))
    
    def get_notes(self, project_id: str, limit: int = 50) -> List[Dict]:
        """Obtiene notas del proyecto"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM project_notes
                WHERE project_id = ?
                ORDER BY updated_at DESC
                LIMIT ?
            """, (project_id, limit))
            
            return [dict(row) for row in cur.fetchall()]
    
    def delete_note(self, note_id: int):
        """Elimina una nota"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM project_notes WHERE id = ?", (note_id,))
    
    # ==========================================
    # UTILIDADES
    # ==========================================
    
    def get_project_stats(self, project_id: str) -> Dict:
        """Estadísticas del proyecto"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            
            stats = {}
            
            # Archivos
            cur.execute("SELECT COUNT(*) as count, SUM(chunk_count) as chunks FROM files WHERE project_id = ?", (project_id,))
            row = cur.fetchone()
            stats['files'] = row['count']
            stats['total_chunks'] = row['chunks'] or 0
            
            # Conversaciones
            cur.execute("SELECT COUNT(*) as count FROM conversations WHERE project_id = ?", (project_id,))
            stats['conversations'] = cur.fetchone()['count']
            
            # Análisis
            cur.execute("SELECT COUNT(*) as count FROM analysis_results WHERE project_id = ?", (project_id,))
            stats['analyses'] = cur.fetchone()['count']
            
            return stats
    
    # ==========================================
    # API USAGE TRACKING (F1 Architecture)
    # ==========================================
    
    def insert_api_usage(
        self,
        timestamp: datetime,
        project_id: Optional[str],
        conversation_id: Optional[int],
        provider: str,
        model: str,
        operation: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        cost_estimated: float,
        metadata_json: Dict = None
    ):
        """Registra uso de API"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO api_usage 
                (timestamp, project_id, conversation_id, provider, model, operation,
                 prompt_tokens, completion_tokens, total_tokens, cost_estimated, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, project_id, conversation_id, provider, model, operation,
                prompt_tokens, completion_tokens, total_tokens, cost_estimated,
                json.dumps(metadata_json or {})
            ))
            
            logger.debug(
                f"API usage recorded",
                provider=provider,
                model=model,
                tokens=total_tokens,
                cost=round(cost_estimated, 4)
            )
    
    def get_monthly_usage(self, year: int = None, month: int = None) -> Dict:
        """Obtiene uso del mes actual o especificado"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            
            if year is None or month is None:
                now = datetime.now()
                year = now.year
                month = now.month
            
            # Primer y último día del mes
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            cur.execute("""
                SELECT 
                    COUNT(*) as requests,
                    SUM(total_tokens) as total_tokens,
                    SUM(prompt_tokens) as prompt_tokens,
                    SUM(completion_tokens) as completion_tokens,
                    SUM(cost_estimated) as total_cost
                FROM api_usage
                WHERE timestamp >= ? AND timestamp < ?
            """, (start_date, end_date))
            
            row = cur.fetchone()
            return {
                'requests': row['requests'] or 0,
                'total_tokens': row['total_tokens'] or 0,
                'prompt_tokens': row['prompt_tokens'] or 0,
                'completion_tokens': row['completion_tokens'] or 0,
                'total_cost': row['total_cost'] or 0.0
            }
    
    def get_usage_stats(
        self,
        project_id: Optional[str] = None,
        days: int = 30
    ) -> Dict:
        """Obtiene estadísticas de uso"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            
            # Fecha límite
            from datetime import timedelta
            cutoff = datetime.now() - timedelta(days=days)
            
            base_query = """
                SELECT 
                    provider,
                    model,
                    COUNT(*) as requests,
                    SUM(total_tokens) as tokens,
                    SUM(cost_estimated) as cost
                FROM api_usage
                WHERE timestamp >= ?
            """
            
            params = [cutoff]
            
            if project_id:
                base_query += " AND project_id = ?"
                params.append(project_id)
            
            base_query += " GROUP BY provider, model ORDER BY cost DESC"
            
            cur.execute(base_query, params)
            
            by_model = [dict(row) for row in cur.fetchall()]
            
            # Totales
            total_requests = sum(m['requests'] for m in by_model)
            total_tokens = sum(m['tokens'] or 0 for m in by_model)
            total_cost = sum(m['cost'] or 0 for m in by_model)
            
            return {
                'period_days': days,
                'total_requests': total_requests,
                'total_tokens': total_tokens,
                'total_cost': total_cost,
                'by_model': by_model
            }
    
    def get_daily_usage(self, days: int = 30, project_id: Optional[str] = None) -> List[Dict]:
        """Obtiene uso diario para gráficos"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            
            from datetime import timedelta
            cutoff = datetime.now() - timedelta(days=days)
            
            base_query = """
                SELECT 
                    DATE(timestamp) as day,
                    SUM(total_tokens) as tokens,
                    SUM(cost_estimated) as cost,
                    COUNT(*) as requests
                FROM api_usage
                WHERE timestamp >= ?
            """
            
            params = [cutoff]
            
            if project_id:
                base_query += " AND project_id = ?"
                params.append(project_id)
            
            base_query += " GROUP BY DATE(timestamp) ORDER BY day ASC"
            
            cur.execute(base_query, params)
            
            return [dict(row) for row in cur.fetchall()]

    # ==================== ANALYTICS QUERIES ====================
    # Methods for usage monitoring and cost tracking
    
    def get_daily_usage(self, days: int = 30) -> List[Dict]:
        """
        Get daily API usage for last N days
        
        Args:
            days: Number of days to retrieve
        
        Returns:
            List of dicts with day, tokens, cost, requests
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    DATE(timestamp) as day,
                    SUM(total_tokens) as tokens,
                    SUM(cost_estimated) as cost,
                    COUNT(*) as requests
                FROM api_usage
                WHERE timestamp >= datetime('now', ? || ' days')
                GROUP BY DATE(timestamp)
                ORDER BY day DESC
            """, (f'-{days}',))
            
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    
    def get_usage_by_project(
        self,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict]:
        """
        Get API usage grouped by project
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
        
        Returns:
            List of dicts with project_id, name, tokens, cost, requests
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            
            query = """
                SELECT 
                    p.id as project_id,
                    p.name as project_name,
                    p.project_type,
                    SUM(a.total_tokens) as tokens,
                    SUM(a.cost_estimated) as cost,
                    COUNT(a.id) as requests
                FROM api_usage a
                LEFT JOIN projects p ON a.project_id = p.id
            """
            
            conditions = []
            params = []
            
            if start_date:
                conditions.append("a.timestamp >= ?")
                params.append(start_date)
            
            if end_date:
                conditions.append("a.timestamp <= ?")
                params.append(end_date)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += """
                GROUP BY p.id, p.name, p.project_type
                ORDER BY cost DESC
            """
            
            cur.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    
    def get_usage_by_model(
        self,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict]:
        """
        Get API usage grouped by provider and model
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
        
        Returns:
            List of dicts with provider, model, tokens, cost, requests
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            
            query = """
                SELECT 
                    provider,
                    model,
                    SUM(total_tokens) as tokens,
                    SUM(cost_estimated) as cost,
                    COUNT(*) as requests,
                    AVG(total_tokens) as avg_tokens_per_request
                FROM api_usage
            """
            
            conditions = []
            params = []
            
            if start_date:
                conditions.append("timestamp >= ?")
                params.append(start_date)
            
            if end_date:
                conditions.append("timestamp <= ?")
                params.append(end_date)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += """
                GROUP BY provider, model
                ORDER BY cost DESC
            """
            
            cur.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    
    def get_usage_by_project_type(
        self,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict]:
        """
        Get API usage grouped by project type (standard, ed_sto, library)
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
        
        Returns:
            List of dicts with project_type, tokens, cost, requests
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            
            query = """
                SELECT 
                    p.project_type,
                    SUM(a.total_tokens) as tokens,
                    SUM(a.cost_estimated) as cost,
                    COUNT(a.id) as requests
                FROM api_usage a
                LEFT JOIN projects p ON a.project_id = p.id
            """
            
            conditions = []
            params = []
            
            if start_date:
                conditions.append("a.timestamp >= ?")
                params.append(start_date)
            
            if end_date:
                conditions.append("a.timestamp <= ?")
                params.append(end_date)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += """
                GROUP BY p.project_type
                ORDER BY cost DESC
            """
            
            cur.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    
    def get_monthly_summary(self) -> Dict:
        """
        Get current month usage summary
        
        Returns:
            Dict with total_tokens, total_cost, total_requests, daily_avg
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    SUM(total_tokens) as total_tokens,
                    SUM(cost_estimated) as total_cost,
                    COUNT(*) as total_requests,
                    COUNT(DISTINCT DATE(timestamp)) as days_active
                FROM api_usage
                WHERE timestamp >= date('now', 'start of month')
            """)
            
            row = cur.fetchone()
            if row:
                result = dict(row)
                # Calculate daily average
                if result['days_active'] and result['days_active'] > 0:
                    result['daily_avg_cost'] = result['total_cost'] / result['days_active']
                    result['daily_avg_tokens'] = result['total_tokens'] / result['days_active']
                else:
                    result['daily_avg_cost'] = 0
                    result['daily_avg_tokens'] = 0
                
                return result
            
            return {
                'total_tokens': 0,
                'total_cost': 0,
                'total_requests': 0,
                'days_active': 0,
                'daily_avg_cost': 0,
                'daily_avg_tokens': 0
            }
    
    def check_budget_alert(self, monthly_budget: float) -> Dict:
        """
        Check if budget threshold exceeded
        
        Args:
            monthly_budget: Monthly budget in USD
        
        Returns:
            Dict with alert status and details
        """
        summary = self.get_monthly_summary()
        total_cost = summary['total_cost']
        
        percentage_used = (total_cost / monthly_budget * 100) if monthly_budget > 0 else 0
        
        alert = {
            'has_alert': percentage_used >= 80,
            'percentage_used': percentage_used,
            'total_cost': total_cost,
            'monthly_budget': monthly_budget,
            'remaining': monthly_budget - total_cost,
            'days_in_month': 30,  # Simplified
            'projected_end_of_month': total_cost * (30 / max(summary['days_active'], 1))
        }
        
        if percentage_used >= 100:
            alert['level'] = 'critical'
            alert['message'] = f'Budget exceeded! ${total_cost:.2f} / ${monthly_budget:.2f}'
        elif percentage_used >= 80:
            alert['level'] = 'warning'
            alert['message'] = f'Approaching budget limit: {percentage_used:.1f}% used'
        else:
            alert['level'] = 'ok'
            alert['message'] = f'Budget OK: {percentage_used:.1f}% used'
        
        return alert
    
    def get_api_usage_summary(
        self,
        project_id: str = None,
        days: int = 7
    ) -> Dict:
        """
        Get API usage summary for a project
        
        Args:
            project_id: Project ID (None for all projects)
            days: Number of days to include
        
        Returns:
            Dict with usage statistics
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            
            query = """
                SELECT 
                    SUM(total_tokens) as total_tokens,
                    SUM(prompt_tokens) as prompt_tokens,
                    SUM(completion_tokens) as completion_tokens,
                    SUM(cost_estimated) as total_cost,
                    COUNT(*) as total_requests,
                    AVG(total_tokens) as avg_tokens_per_request
                FROM api_usage
                WHERE timestamp >= datetime('now', ? || ' days')
            """
            
            params = [f'-{days}']
            
            if project_id:
                query += " AND project_id = ?"
                params.append(project_id)
            
            cur.execute(query, params)
            row = cur.fetchone()
            
            if row:
                return dict(row)
            
            return {
                'total_tokens': 0,
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_cost': 0,
                'total_requests': 0,
                'avg_tokens_per_request': 0
            }

