"""
Agentic Retrieval Plugin - Estrategia inteligente de recuperación

Este plugin ejecuta la búsqueda de manera inteligente:
1. Aplica el plan de query
2. Ejecuta búsqueda adaptativa (puede hacer múltiples búsquedas)
3. Combina resultados de diferentes estrategias
4. Auto-ajusta si los resultados son insuficientes
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from core.plugins.base import PluginMetadata, PluginCapability


@dataclass
class RetrievalResult:
    """Resultado de recuperación inteligente"""
    results: List[Any]          # SearchResults del RAG
    metadata: Dict[str, Any]    # Metadata de la búsqueda
    strategy_used: str          # Qué estrategia se usó
    confidence: float           # Confianza en los resultados (0-1)
    needs_refinement: bool      # Si necesita búsqueda adicional
    refinement_suggestions: List[str]  # Sugerencias de mejora


class AgenticRetrievalPlugin:
    """
    Plugin de recuperación agéntica

    Ejecuta búsquedas inteligentes adaptándose a la calidad de resultados.
    """

    def __init__(self):
        self.confidence_threshold = 0.7  # Threshold para considerar resultados buenos

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="agentic_retrieval",
            version="1.0.0",
            description="Recuperación inteligente con auto-ajuste y estrategias adaptativas",
            author="ARGO Team",
            capabilities=[PluginCapability.INTELLIGENCE]
        )

    def execute(self, rag_engine, query: str, query_plan, **kwargs) -> RetrievalResult:
        """
        Ejecuta recuperación inteligente

        Args:
            rag_engine: Motor RAG del sistema
            query: Query original del usuario
            query_plan: Plan de QueryPlanningPlugin
            **kwargs: Opciones adicionales

        Returns:
            RetrievalResult con resultados optimizados
        """

        # 1. Primera búsqueda usando el plan
        results, metadata = self._execute_search(
            rag_engine,
            query,
            top_k=query_plan.recommended_top_k,
            use_hyde=query_plan.use_hyde,
            use_reranker=query_plan.use_reranker
        )

        # 2. Evaluar calidad de resultados
        confidence = self._evaluate_results_quality(results, query, query_plan)

        # 3. Decidir si necesita refinamiento
        needs_refinement = confidence < self.confidence_threshold and len(results) > 0

        refinement_suggestions = []
        if needs_refinement:
            refinement_suggestions = self._generate_refinement_suggestions(
                results, query, query_plan, confidence
            )

        # 4. Si necesita refinamiento y tenemos sugerencias, ejecutar búsqueda adicional
        if needs_refinement and refinement_suggestions and kwargs.get('allow_refinement', True):
            results, metadata, confidence = self._refine_search(
                rag_engine, query, results, metadata,
                refinement_suggestions, query_plan
            )
            needs_refinement = False  # Ya refinamos

        return RetrievalResult(
            results=results,
            metadata=metadata,
            strategy_used=query_plan.search_strategy,
            confidence=confidence,
            needs_refinement=needs_refinement,
            refinement_suggestions=refinement_suggestions
        )

    def _execute_search(self, rag_engine, query: str, top_k: int,
                       use_hyde: bool, use_reranker: bool) -> Tuple[List, Dict]:
        """Ejecuta una búsqueda en el RAG engine"""

        try:
            results, metadata = rag_engine.search(
                query=query,
                top_k=top_k,
                use_hyde=use_hyde,
                use_reranker=use_reranker,
                include_library=True
            )
            return results, metadata

        except Exception as e:
            # Fallback: búsqueda simple sin HyDE ni reranker
            results, metadata = rag_engine.search(
                query=query,
                top_k=top_k,
                use_hyde=False,
                use_reranker=False,
                include_library=True
            )
            metadata['fallback'] = True
            metadata['fallback_reason'] = str(e)
            return results, metadata

    def _evaluate_results_quality(self, results: List, query: str, query_plan) -> float:
        """
        Evalúa la calidad de los resultados

        Returns:
            Confidence score 0.0-1.0
        """

        if not results:
            return 0.0

        # Factor 1: Scores de similitud
        avg_score = sum(r.score for r in results) / len(results)

        # Factor 2: Si el top result tiene score muy alto, es buena señal
        top_score = results[0].score if results else 0.0
        top_bonus = 0.1 if top_score > 0.8 else 0.0

        # Factor 3: Diversidad de fuentes (múltiples documentos = mejor)
        unique_sources = len(set(r.metadata.get('source', '') for r in results))
        diversity_bonus = min(0.1, unique_sources * 0.02)

        # Factor 4: Si usamos reranker y hay rerank_scores, usar esos
        if results[0].rerank_score is not None:
            avg_rerank = sum(r.rerank_score for r in results if r.rerank_score) / len(results)
            # Rerank scores son más confiables
            confidence = (avg_rerank * 0.7) + (avg_score * 0.3)
        else:
            confidence = avg_score

        # Aplicar bonuses
        confidence = min(1.0, confidence + top_bonus + diversity_bonus)

        return confidence

    def _generate_refinement_suggestions(self, results: List, query: str,
                                        query_plan, confidence: float) -> List[str]:
        """Genera sugerencias para refinar la búsqueda"""

        suggestions = []

        # Si confianza es muy baja y no usamos HyDE, sugerir usarlo
        if confidence < 0.5 and not query_plan.use_hyde:
            suggestions.append("enable_hyde")

        # Si hay pocos resultados, aumentar top_k
        if len(results) < 3:
            suggestions.append("increase_top_k")

        # Si los scores son bajos, podríamos expandir la query
        if results and results[0].score < 0.6:
            suggestions.append("expand_query")

        return suggestions

    def _refine_search(self, rag_engine, query: str, original_results: List,
                      original_metadata: Dict, suggestions: List,
                      query_plan) -> Tuple[List, Dict, float]:
        """
        Refina la búsqueda basándose en sugerencias

        Returns:
            (results, metadata, new_confidence)
        """

        # Aplicar sugerencias
        use_hyde = query_plan.use_hyde or "enable_hyde" in suggestions
        top_k = query_plan.recommended_top_k

        if "increase_top_k" in suggestions:
            top_k = min(15, top_k + 5)

        # Nueva búsqueda con parámetros ajustados
        new_results, new_metadata = self._execute_search(
            rag_engine,
            query,
            top_k=top_k,
            use_hyde=use_hyde,
            use_reranker=True  # Siempre usar reranker en refinamiento
        )

        # Combinar resultados (merge inteligente)
        combined_results = self._merge_results(original_results, new_results)

        # Recalcular confianza
        new_confidence = self._evaluate_results_quality(combined_results, query, query_plan)

        # Metadata combinada
        combined_metadata = {
            **new_metadata,
            'refined': True,
            'original_confidence': self._evaluate_results_quality(original_results, query, query_plan),
            'new_confidence': new_confidence,
            'suggestions_applied': suggestions
        }

        return combined_results, combined_metadata, new_confidence

    def _merge_results(self, original: List, new: List) -> List:
        """
        Combina resultados de dos búsquedas, eliminando duplicados

        Prioriza los de mayor score
        """

        # Crear dict con source+chunk como key para deduplicar
        merged = {}

        for r in original + new:
            key = (r.metadata.get('source', ''), r.metadata.get('chunk_id', ''))

            # Si no existe o el nuevo tiene mejor score, usar el nuevo
            if key not in merged or r.score > merged[key].score:
                merged[key] = r

        # Ordenar por score descendente
        results = sorted(merged.values(), key=lambda x: x.score, reverse=True)

        # Tomar top 10
        return results[:10]
