"""
Intelligence Plugins Package

Plugins avanzados de inteligencia para el sistema RAG:
- QueryPlanningPlugin: Clasifica y planifica queries
- AgenticRetrievalPlugin: Recuperación adaptativa
- CorrectiveRAGPlugin: Corrección y optimización de contexto
- SelfReflectiveRAGPlugin: Validación de respuestas
"""

from plugins.intelligence.query_planning_plugin import QueryPlanningPlugin, QueryPlan
from plugins.intelligence.agentic_retrieval_plugin import AgenticRetrievalPlugin, RetrievalResult
from plugins.intelligence.corrective_rag_plugin import CorrectiveRAGPlugin, CorrectedContext
from plugins.intelligence.self_reflective_rag_plugin import SelfReflectiveRAGPlugin, ReflectionResult

__all__ = [
    'QueryPlanningPlugin',
    'QueryPlan',
    'AgenticRetrievalPlugin',
    'RetrievalResult',
    'CorrectiveRAGPlugin',
    'CorrectedContext',
    'SelfReflectiveRAGPlugin',
    'ReflectionResult',
]
