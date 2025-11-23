"""
Intelligence Pipeline - Orquestador de plugins de inteligencia

Este módulo integra los 4 plugins de inteligencia en un pipeline coherente:

1. QueryPlanningPlugin → Analiza la query y crea un plan
2. AgenticRetrievalPlugin → Ejecuta búsqueda inteligente con el plan
3. CorrectiveRAGPlugin → Filtra y optimiza el contexto
4. SelfReflectiveRAGPlugin → Valida la respuesta final

El pipeline se inyecta en el flujo del chat para aumentar la "inteligencia" del sistema.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

from core.logger import get_logger
from plugins.intelligence import (
    QueryPlanningPlugin,
    AgenticRetrievalPlugin,
    CorrectiveRAGPlugin,
    SelfReflectiveRAGPlugin
)

logger = get_logger("IntelligencePipeline")


@dataclass
class PipelineResult:
    """Resultado completo del pipeline de inteligencia"""

    # Outputs principales
    final_response: str
    formatted_context: str
    sources: List[Dict]

    # Metadata del pipeline
    query_plan: Dict
    retrieval_result: Dict
    corrected_context: Dict
    reflection_result: Dict

    # Métricas
    confidence: float
    hallucination_risk: str
    pipeline_notes: List[str]


class IntelligencePipeline:
    """
    Pipeline de inteligencia que coordina los 4 plugins
    """

    def __init__(self):
        """Inicializa el pipeline y carga los plugins"""

        logger.info("Initializing Intelligence Pipeline...")

        # Instanciar plugins
        self.query_planner = QueryPlanningPlugin()
        self.agentic_retrieval = AgenticRetrievalPlugin()
        self.corrective_rag = CorrectiveRAGPlugin()
        self.self_reflective = SelfReflectiveRAGPlugin()

        logger.info("✅ Intelligence Pipeline ready")

    def execute(
        self,
        query: str,
        rag_engine,
        model_router,
        project_id: str,
        request_options: Optional[Dict] = None
    ) -> PipelineResult:
        """
        Ejecuta el pipeline completo de inteligencia

        Args:
            query: Query del usuario
            rag_engine: Motor RAG del sistema
            model_router: Router de modelos LLM
            project_id: ID del proyecto activo
            request_options: Opciones del request (use_hyde, etc.)

        Returns:
            PipelineResult con respuesta optimizada y metadata completa
        """

        request_options = request_options or {}
        pipeline_notes = []

        logger.info(f"🧠 Starting Intelligence Pipeline for: {query[:50]}...")

        # ========================================================================
        # PASO 1: Query Planning
        # ========================================================================
        logger.info("Step 1/4: Query Planning...")

        query_plan = self.query_planner.execute(query)

        pipeline_notes.append(f"Query classified as: {query_plan.query_type.value}")
        pipeline_notes.append(f"Complexity: {query_plan.complexity.value}")
        pipeline_notes.append(query_plan.reasoning)

        logger.info(f"  → Type: {query_plan.query_type.value}, "
                   f"Complexity: {query_plan.complexity.value}")

        # ========================================================================
        # PASO 2: Agentic Retrieval
        # ========================================================================
        logger.info("Step 2/4: Agentic Retrieval...")

        # Override con opciones del request si están presentes
        if 'use_hyde' in request_options:
            query_plan.use_hyde = request_options['use_hyde']
        if 'use_reranker' in request_options:
            query_plan.use_reranker = request_options['use_reranker']

        retrieval_result = self.agentic_retrieval.execute(
            rag_engine=rag_engine,
            query=query,
            query_plan=query_plan,
            allow_refinement=True
        )

        pipeline_notes.append(f"Retrieved {len(retrieval_result.results)} chunks")
        pipeline_notes.append(f"Retrieval confidence: {retrieval_result.confidence:.2f}")
        pipeline_notes.extend(retrieval_result.metadata.get('suggestions_applied', []))

        logger.info(f"  → Retrieved {len(retrieval_result.results)} chunks, "
                   f"confidence: {retrieval_result.confidence:.2f}")

        # ========================================================================
        # PASO 3: Corrective RAG
        # ========================================================================
        logger.info("Step 3/4: Corrective RAG...")

        corrected_context = self.corrective_rag.execute(
            results=retrieval_result.results,
            query=query,
            query_plan=query_plan
        )

        pipeline_notes.append(f"Context confidence: {corrected_context.confidence_level}")
        pipeline_notes.extend(corrected_context.correction_notes)

        logger.info(f"  → Filtered to {len(corrected_context.filtered_results)} chunks, "
                   f"confidence: {corrected_context.confidence_level}")

        # ========================================================================
        # PASO 3.5: Generate Response
        # ========================================================================
        logger.info("Step 3.5/4: Generating LLM Response...")

        # Usar el contexto formateado por CorrectiveRAG
        system_prompt = f"""You are ARGO, an enterprise project management assistant.

Use the following context to answer the user's question accurately and professionally.

{corrected_context.formatted_context}

Guidelines:
- Answer based on the context provided
- Be concise and professional
- Cite sources when appropriate
- If information is not in context, say so clearly
- Use proper business terminology
- IMPORTANT: Do not add information not present in the sources"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]

        # Generar respuesta
        llm_response = model_router.route(
            messages=messages,
            task_type="chat",
            project_id=project_id
        )

        initial_response = llm_response.content

        logger.info(f"  → Response generated ({len(initial_response)} chars)")

        # ========================================================================
        # PASO 4: Self-Reflective RAG
        # ========================================================================
        logger.info("Step 4/4: Self-Reflective Validation...")

        reflection_result = self.self_reflective.execute(
            response=initial_response,
            context=corrected_context.formatted_context,
            query=query,
            corrected_context=corrected_context,
            model_router=model_router,
            project_id=project_id,
            allow_regeneration=True
        )

        pipeline_notes.append(f"Hallucination risk: {reflection_result.hallucination_risk}")
        pipeline_notes.append(f"Consistency score: {reflection_result.consistency_score:.2f}")
        pipeline_notes.extend(reflection_result.reflection_notes)

        if reflection_result.was_regenerated:
            pipeline_notes.append("⚠️  Response was regenerated for quality")

        logger.info(f"  → Hallucination risk: {reflection_result.hallucination_risk}, "
                   f"Consistency: {reflection_result.consistency_score:.2f}")

        # ========================================================================
        # RESULTADO FINAL
        # ========================================================================

        # Preparar sources para el response
        sources = [
            {
                "source": r.metadata.get('source', 'Unknown'),
                "score": float(r.score),
                "rerank_score": float(r.rerank_score) if r.rerank_score else None,
                "is_library": r.is_library
            }
            for r in corrected_context.filtered_results
        ]

        # Calcular confidence final (weighted average)
        final_confidence = (
            retrieval_result.confidence * 0.3 +
            (1.0 if corrected_context.confidence_level == "high" else
             0.6 if corrected_context.confidence_level == "medium" else 0.3) * 0.3 +
            reflection_result.consistency_score * 0.4
        )

        result = PipelineResult(
            final_response=reflection_result.final_response,
            formatted_context=corrected_context.formatted_context,
            sources=sources,
            query_plan=asdict(query_plan) if hasattr(query_plan, '__dict__') else {},
            retrieval_result={
                'confidence': retrieval_result.confidence,
                'strategy_used': retrieval_result.strategy_used,
                'needs_refinement': retrieval_result.needs_refinement
            },
            corrected_context={
                'confidence_level': corrected_context.confidence_level,
                'has_contradictions': corrected_context.has_contradictions,
                'missing_info_detected': corrected_context.missing_info_detected,
                'num_chunks': len(corrected_context.filtered_results)
            },
            reflection_result={
                'hallucination_risk': reflection_result.hallucination_risk,
                'consistency_score': reflection_result.consistency_score,
                'was_regenerated': reflection_result.was_regenerated
            },
            confidence=final_confidence,
            hallucination_risk=reflection_result.hallucination_risk,
            pipeline_notes=pipeline_notes
        )

        logger.info(f"✅ Intelligence Pipeline complete - Final confidence: {final_confidence:.2f}")

        return result


# ============================================================================
# Helper function para usar en el endpoint
# ============================================================================

def apply_intelligence_pipeline(
    query: str,
    rag_engine,
    model_router,
    project_id: str,
    request_options: Optional[Dict] = None
) -> PipelineResult:
    """
    Función helper para aplicar el pipeline de inteligencia

    Esta función se llama desde backend/main.py en el endpoint /api/chat

    Args:
        query: Query del usuario
        rag_engine: Motor RAG
        model_router: Router de modelos
        project_id: ID del proyecto
        request_options: Opciones del request

    Returns:
        PipelineResult con respuesta optimizada
    """

    pipeline = IntelligencePipeline()
    return pipeline.execute(
        query=query,
        rag_engine=rag_engine,
        model_router=model_router,
        project_id=project_id,
        request_options=request_options
    )
