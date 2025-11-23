"""
Corrective RAG Plugin - Corrige y optimiza el contexto

Este plugin filtra y mejora el contexto antes de enviarlo al LLM:
1. Elimina chunks irrelevantes (por score bajo)
2. Detecta contradicciones entre chunks
3. Re-ordena chunks por relevancia y coherencia
4. Agrega metadata útil para el LLM
5. Detecta si falta información crítica
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from core.plugins.base import PluginMetadata, PluginCapability


@dataclass
class CorrectedContext:
    """Contexto corregido y optimizado"""
    filtered_results: List[Any]        # Chunks filtrados
    formatted_context: str             # Contexto formateado para LLM
    relevance_scores: List[float]      # Scores de relevancia
    has_contradictions: bool           # Si hay contradicciones detectadas
    missing_info_detected: bool        # Si falta información
    confidence_level: str              # "high", "medium", "low"
    correction_notes: List[str]        # Qué correcciones se aplicaron


class CorrectiveRAGPlugin:
    """
    Plugin de corrección de contexto RAG

    Filtra, ordena y optimiza el contexto antes de enviarlo al LLM.
    """

    def __init__(self):
        self.min_score_threshold = 0.3  # Chunks bajo este score se descartan
        self.contradiction_threshold = 0.15  # Diferencia de score que sugiere contradicción

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="corrective_rag",
            version="1.0.0",
            description="Filtra y optimiza contexto eliminando ruido y contradicciones",
            author="ARGO Team",
            capabilities=[PluginCapability.INTELLIGENCE]
        )

    def execute(self, results: List, query: str, query_plan, **kwargs) -> CorrectedContext:
        """
        Corrige y optimiza el contexto

        Args:
            results: Resultados de búsqueda del RAG
            query: Query original
            query_plan: Plan de query
            **kwargs: Opciones adicionales

        Returns:
            CorrectedContext con contexto optimizado
        """

        correction_notes = []

        # 1. Filtrar chunks de bajo score
        filtered_results, filter_notes = self._filter_low_quality(results)
        correction_notes.extend(filter_notes)

        if not filtered_results:
            # Si no quedan resultados, volver a los originales pero marcar baja confianza
            filtered_results = results[:3] if results else []
            correction_notes.append("No high-quality results, using top 3")

        # 2. Detectar contradicciones
        has_contradictions, contradiction_notes = self._detect_contradictions(filtered_results)
        correction_notes.extend(contradiction_notes)

        # 3. Re-ordenar por relevancia
        reordered_results = self._reorder_by_relevance(filtered_results, query)

        # 4. Detectar información faltante
        missing_info = self._detect_missing_info(reordered_results, query, query_plan)

        # 5. Calcular nivel de confianza
        confidence_level = self._calculate_confidence_level(
            reordered_results, has_contradictions, missing_info
        )

        # 6. Formatear contexto optimizado
        formatted_context = self._format_context_enhanced(
            reordered_results, query, has_contradictions, missing_info
        )

        # 7. Extraer scores de relevancia
        relevance_scores = [r.score for r in reordered_results]

        return CorrectedContext(
            filtered_results=reordered_results,
            formatted_context=formatted_context,
            relevance_scores=relevance_scores,
            has_contradictions=has_contradictions,
            missing_info_detected=missing_info,
            confidence_level=confidence_level,
            correction_notes=correction_notes
        )

    def _filter_low_quality(self, results: List) -> Tuple[List, List[str]]:
        """
        Filtra chunks de baja calidad

        Returns:
            (filtered_results, notes)
        """

        if not results:
            return [], []

        notes = []
        original_count = len(results)

        # Filtrar por score mínimo
        filtered = [r for r in results if r.score >= self.min_score_threshold]

        if len(filtered) < original_count:
            removed = original_count - len(filtered)
            notes.append(f"Removed {removed} low-quality chunks (score < {self.min_score_threshold})")

        # Asegurar al menos 1 resultado si había alguno
        if not filtered and results:
            filtered = [results[0]]
            notes.append("Kept top result despite low score")

        return filtered, notes

    def _detect_contradictions(self, results: List) -> Tuple[bool, List[str]]:
        """
        Detecta posibles contradicciones entre chunks

        Por ahora usa heurística simple: si hay chunks con scores muy dispares
        del mismo documento, puede haber contradicción.

        Returns:
            (has_contradictions, notes)
        """

        if len(results) < 2:
            return False, []

        notes = []

        # Agrupar por source
        by_source = {}
        for r in results:
            source = r.metadata.get('source', 'unknown')
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(r)

        # Buscar sources con chunks de scores muy dispares
        for source, chunks in by_source.items():
            if len(chunks) < 2:
                continue

            scores = [c.score for c in chunks]
            score_range = max(scores) - min(scores)

            if score_range > self.contradiction_threshold:
                notes.append(f"Potential contradiction in {source}: score range {score_range:.2f}")
                return True, notes

        return False, notes

    def _reorder_by_relevance(self, results: List, query: str) -> List:
        """
        Re-ordena chunks por relevancia

        Prioriza:
        1. Score alto (similaridad)
        2. Diversidad de fuentes (no todos del mismo documento)
        """

        if not results:
            return []

        # Ya vienen ordenados por score, pero vamos a ajustar por diversidad
        reordered = []
        seen_sources = set()

        # Primera pasada: tomar top de cada source único
        for r in results:
            source = r.metadata.get('source', 'unknown')
            if source not in seen_sources:
                reordered.append(r)
                seen_sources.add(source)

        # Segunda pasada: agregar el resto
        for r in results:
            if r not in reordered:
                reordered.append(r)

        return reordered

    def _detect_missing_info(self, results: List, query: str, query_plan) -> bool:
        """
        Detecta si probablemente falta información para responder bien

        Heurísticas:
        - Query compleja pero pocos resultados
        - Scores todos bajos
        - Query pide múltiples aspectos pero solo tenemos de uno
        """

        if not results:
            return True

        # Si query es compleja pero tenemos < 3 chunks, probablemente falta info
        if query_plan.complexity.value == "complex" and len(results) < 3:
            return True

        # Si todos los scores son bajos, falta info
        avg_score = sum(r.score for r in results) / len(results)
        if avg_score < 0.5:
            return True

        return False

    def _calculate_confidence_level(self, results: List, has_contradictions: bool,
                                   missing_info: bool) -> str:
        """
        Calcula nivel de confianza en el contexto

        Returns:
            "high", "medium", "low"
        """

        if not results:
            return "low"

        if has_contradictions or missing_info:
            return "low"

        # Calcular score promedio
        avg_score = sum(r.score for r in results) / len(results)

        if avg_score > 0.75:
            return "high"
        elif avg_score > 0.55:
            return "medium"
        else:
            return "low"

    def _format_context_enhanced(self, results: List, query: str,
                                has_contradictions: bool, missing_info: bool) -> str:
        """
        Formatea el contexto de manera optimizada para el LLM

        Incluye:
        - Número de chunk
        - Source
        - Relevance score
        - Warnings si hay contradicciones
        """

        if not results:
            return "No relevant context found in the knowledge base."

        context_parts = []

        # Header con metadata
        context_parts.append("=== RETRIEVED CONTEXT ===\n")

        if has_contradictions:
            context_parts.append("⚠️  WARNING: Potential contradictions detected in sources. "
                               "Please carefully verify information.\n")

        if missing_info:
            context_parts.append("⚠️  NOTE: Limited context available. "
                               "Response may be incomplete.\n")

        context_parts.append(f"Found {len(results)} relevant chunks:\n")

        # Cada chunk con metadata
        for i, result in enumerate(results, 1):
            source = result.metadata.get('source', 'Unknown')
            score = result.score
            is_library = result.is_library

            source_type = "📚 [Library]" if is_library else "📄 [Project]"

            context_parts.append(f"\n--- Chunk {i} {source_type} ---")
            context_parts.append(f"Source: {source}")
            context_parts.append(f"Relevance: {score:.2f}")
            context_parts.append(f"Content:\n{result.content}\n")

        return "\n".join(context_parts)
