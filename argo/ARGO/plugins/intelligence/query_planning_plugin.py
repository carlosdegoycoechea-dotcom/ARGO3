"""
Query Planning Plugin - Clasifica y planifica la estrategia de respuesta

Este plugin analiza la query del usuario y determina:
1. Tipo de pregunta (factual, analítica, comparativa, procedural)
2. Complejidad (simple, media, compleja)
3. Necesita descomposición en sub-queries
4. Estrategia de búsqueda recomendada
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from core.plugins.base import PluginMetadata, PluginCapability


class QueryType(str, Enum):
    """Tipos de queries identificados"""
    FACTUAL = "factual"              # "¿Cuál es el budget del proyecto X?"
    ANALYTICAL = "analytical"         # "¿Por qué el proyecto está atrasado?"
    COMPARATIVE = "comparative"       # "Compara proyecto A vs B"
    PROCEDURAL = "procedural"         # "¿Cómo hacer X?"
    AGGREGATION = "aggregation"       # "Resume todos los riesgos"
    TEMPORAL = "temporal"             # "¿Qué pasó en Q1?"
    MULTI_HOP = "multi_hop"           # Requiere múltiples pasos de razonamiento


class QueryComplexity(str, Enum):
    """Niveles de complejidad"""
    SIMPLE = "simple"        # Respuesta directa de 1-2 documentos
    MEDIUM = "medium"        # Requiere integrar 3-5 documentos
    COMPLEX = "complex"      # Requiere análisis profundo, múltiples fuentes


@dataclass
class QueryPlan:
    """Plan de ejecución para una query"""
    query_type: QueryType
    complexity: QueryComplexity
    needs_decomposition: bool
    sub_queries: List[str]
    recommended_top_k: int           # Cuántos documentos recuperar
    use_hyde: bool                   # Si HyDE ayudaría
    use_reranker: bool               # Si reranker es necesario
    search_strategy: str             # "dense", "sparse", "hybrid"
    reasoning: str                   # Por qué este plan


class QueryPlanningPlugin:
    """
    Plugin de planificación de queries

    Analiza la query del usuario y crea un plan de ejecución optimizado.
    """

    def __init__(self):
        super().__init__()

        # Patterns para clasificación
        self.factual_patterns = [
            r'\b(cuál|cuáles|qué|quién|quiénes|dónde|cuándo|cuánto|cuántos)\b',
            r'\b(what|who|where|when|which|how many|how much)\b',
        ]

        self.analytical_patterns = [
            r'\b(por qué|razón|causa|motivo|explicar|justificar)\b',
            r'\b(why|reason|cause|explain|justify)\b',
            r'\b(análisis|analizar|evaluar)\b',
        ]

        self.comparative_patterns = [
            r'\b(comparar|comparación|diferencia|vs|versus|mejor|peor)\b',
            r'\b(compare|comparison|difference|better|worse)\b',
        ]

        self.procedural_patterns = [
            r'\b(cómo|paso|pasos|procedimiento|proceso|guía)\b',
            r'\b(how to|steps|procedure|process|guide)\b',
        ]

        self.aggregation_patterns = [
            r'\b(resumir|resumen|todos|todas|lista|listar)\b',
            r'\b(summarize|summary|all|list)\b',
        ]

        self.temporal_patterns = [
            r'\b(histórico|historia|evolución|tendencia|cambio)\b',
            r'\b(history|historical|evolution|trend|change|over time)\b',
            r'\b(Q[1-4]|trimestre|mes|año)\b',
        ]

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="query_planning",
            version="1.0.0",
            description="Analiza queries y crea plan de ejecución inteligente",
            author="ARGO Team",
            capabilities=[PluginCapability.INTELLIGENCE]
        )

    def execute(self, query: str, **kwargs) -> QueryPlan:
        """
        Analiza la query y retorna un plan de ejecución

        Args:
            query: La pregunta del usuario
            **kwargs: Contexto adicional (historial, proyecto, etc.)

        Returns:
            QueryPlan con la estrategia recomendada
        """
        import re

        query_lower = query.lower()

        # 1. Clasificar tipo de query
        query_type = self._classify_query_type(query_lower)

        # 2. Determinar complejidad
        complexity = self._determine_complexity(query, query_type)

        # 3. Decidir si necesita descomposición
        needs_decomposition, sub_queries = self._check_decomposition(query, query_type, complexity)

        # 4. Recomendar estrategia de búsqueda
        recommended_top_k = self._recommend_top_k(query_type, complexity)
        use_hyde = self._should_use_hyde(query_type, complexity)
        use_reranker = self._should_use_reranker(complexity)
        search_strategy = self._recommend_search_strategy(query_type)

        # 5. Generar razonamiento
        reasoning = self._generate_reasoning(
            query_type, complexity, needs_decomposition,
            use_hyde, use_reranker, search_strategy
        )

        return QueryPlan(
            query_type=query_type,
            complexity=complexity,
            needs_decomposition=needs_decomposition,
            sub_queries=sub_queries,
            recommended_top_k=recommended_top_k,
            use_hyde=use_hyde,
            use_reranker=use_reranker,
            search_strategy=search_strategy,
            reasoning=reasoning
        )

    def _classify_query_type(self, query: str) -> QueryType:
        """Clasifica el tipo de query usando patterns"""
        import re

        # Check patterns en orden de especificidad
        if any(re.search(pattern, query, re.IGNORECASE) for pattern in self.comparative_patterns):
            return QueryType.COMPARATIVE

        if any(re.search(pattern, query, re.IGNORECASE) for pattern in self.temporal_patterns):
            return QueryType.TEMPORAL

        if any(re.search(pattern, query, re.IGNORECASE) for pattern in self.analytical_patterns):
            return QueryType.ANALYTICAL

        if any(re.search(pattern, query, re.IGNORECASE) for pattern in self.procedural_patterns):
            return QueryType.PROCEDURAL

        if any(re.search(pattern, query, re.IGNORECASE) for pattern in self.aggregation_patterns):
            return QueryType.AGGREGATION

        if any(re.search(pattern, query, re.IGNORECASE) for pattern in self.factual_patterns):
            return QueryType.FACTUAL

        # Default: analytical si tiene > 15 palabras
        if len(query.split()) > 15:
            return QueryType.ANALYTICAL

        return QueryType.FACTUAL

    def _determine_complexity(self, query: str, query_type: QueryType) -> QueryComplexity:
        """Determina la complejidad de la query"""

        # Factores de complejidad
        word_count = len(query.split())
        has_multiple_questions = query.count('?') > 1 or ' y ' in query.lower()

        # Queries comparativas/analíticas son inherentemente más complejas
        if query_type in [QueryType.COMPARATIVE, QueryType.MULTI_HOP]:
            return QueryComplexity.COMPLEX

        if query_type in [QueryType.ANALYTICAL, QueryType.AGGREGATION, QueryType.TEMPORAL]:
            return QueryComplexity.MEDIUM if word_count < 20 else QueryComplexity.COMPLEX

        # Procedurales son medianas
        if query_type == QueryType.PROCEDURAL:
            return QueryComplexity.MEDIUM

        # Factuales simples si son cortas
        if word_count < 10 and not has_multiple_questions:
            return QueryComplexity.SIMPLE

        return QueryComplexity.MEDIUM

    def _check_decomposition(self, query: str, query_type: QueryType,
                            complexity: QueryComplexity) -> tuple[bool, List[str]]:
        """Decide si la query necesita descomposición en sub-queries"""

        sub_queries = []

        # Queries complejas comparativas/analíticas se benefician de descomposición
        if complexity == QueryComplexity.COMPLEX and query_type == QueryType.COMPARATIVE:
            # Ejemplo: "Compara proyecto A vs B" → ["Info proyecto A", "Info proyecto B"]
            # Por ahora retornamos False, pero aquí iría lógica de descomposición
            return False, []

        if complexity == QueryComplexity.COMPLEX and query_type == QueryType.AGGREGATION:
            # Ejemplo: "Resume todos los riesgos" podría descomponerse
            return False, []

        return False, []

    def _recommend_top_k(self, query_type: QueryType, complexity: QueryComplexity) -> int:
        """Recomienda cuántos documentos recuperar"""

        # Queries de agregación necesitan más documentos
        if query_type == QueryType.AGGREGATION:
            return 10

        # Queries comparativas necesitan más contexto
        if query_type == QueryType.COMPARATIVE:
            return 8

        # Complejidad alta → más documentos
        if complexity == QueryComplexity.COMPLEX:
            return 7

        if complexity == QueryComplexity.MEDIUM:
            return 5

        # Simple → pocos documentos suficientes
        return 3

    def _should_use_hyde(self, query_type: QueryType, complexity: QueryComplexity) -> bool:
        """Decide si HyDE ayudaría con esta query"""

        # HyDE es excelente para queries analíticas/procedurales
        # donde generar una respuesta hipotética ayuda a encontrar documentos similares
        if query_type in [QueryType.ANALYTICAL, QueryType.PROCEDURAL]:
            return True

        # Queries complejas se benefician de HyDE
        if complexity == QueryComplexity.COMPLEX:
            return True

        # Factuales simples no necesitan HyDE
        if query_type == QueryType.FACTUAL and complexity == QueryComplexity.SIMPLE:
            return False

        return False

    def _should_use_reranker(self, complexity: QueryComplexity) -> bool:
        """Decide si usar reranker"""

        # Queries complejas siempre usan reranker
        if complexity == QueryComplexity.COMPLEX:
            return True

        # Medianas también se benefician
        if complexity == QueryComplexity.MEDIUM:
            return True

        # Simples pueden omitirlo
        return False

    def _recommend_search_strategy(self, query_type: QueryType) -> str:
        """Recomienda estrategia de búsqueda"""

        # Queries factuales → dense (embeddings)
        if query_type == QueryType.FACTUAL:
            return "dense"

        # Queries con keywords específicos → hybrid
        if query_type in [QueryType.PROCEDURAL, QueryType.AGGREGATION]:
            return "hybrid"

        # Default: dense
        return "dense"

    def _generate_reasoning(self, query_type: QueryType, complexity: QueryComplexity,
                           needs_decomposition: bool, use_hyde: bool,
                           use_reranker: bool, search_strategy: str) -> str:
        """Genera explicación del plan"""

        reasoning = f"Query clasificada como {query_type.value} con complejidad {complexity.value}. "

        if use_hyde:
            reasoning += "HyDE habilitado para mejorar recuperación semántica. "

        if use_reranker:
            reasoning += "Reranker habilitado para precisión. "

        reasoning += f"Estrategia: {search_strategy}."

        return reasoning
