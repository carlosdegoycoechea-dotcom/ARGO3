"""
Self-Reflective RAG Plugin - Revisa y valida la respuesta del LLM

Este plugin analiza la respuesta generada y:
1. Detecta posibles alucinaciones (info no en el contexto)
2. Verifica consistencia con las fuentes
3. Calcula confidence score de la respuesta
4. Decide si necesita regeneración
5. Puede hacer una repregunta interna para mejorar
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from core.plugins.base import PluginMetadata, PluginCapability


@dataclass
class ReflectionResult:
    """Resultado de auto-reflexión sobre la respuesta"""
    final_response: str                # Respuesta final (original o mejorada)
    hallucination_risk: str            # "low", "medium", "high"
    consistency_score: float           # 0.0-1.0
    needs_regeneration: bool           # Si debería regenerarse
    regeneration_reason: Optional[str] # Por qué regenerar
    reflection_notes: List[str]        # Notas del análisis
    was_regenerated: bool              # Si se regeneró


class SelfReflectiveRAGPlugin:
    """
    Plugin de auto-reflexión sobre respuestas

    Analiza la respuesta del LLM para detectar problemas y mejorarla.
    """

    def __init__(self):
        # Patterns que indican posible alucinación
        self.hallucination_patterns = [
            # Afirmaciones muy específicas sin citar fuente
            r'\b(exactly|precisely|specifically)\s+\d+',
            # Fechas muy específicas
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b',
            # Nombres propios no mencionados en contexto (difícil de detectar sin NER)
        ]

        # Frases que indican el LLM sabe que no tiene info
        self.uncertainty_phrases = [
            "not mentioned",
            "not provided",
            "not specified",
            "no information",
            "cannot determine",
            "unclear from",
            "based on the context",
            "according to the document",
        ]

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="self_reflective_rag",
            version="1.0.0",
            description="Analiza respuestas para detectar alucinaciones y verificar consistencia",
            author="ARGO Team",
            capabilities=[PluginCapability.INTELLIGENCE]
        )

    def execute(self, response: str, context: str, query: str,
                corrected_context, model_router=None, **kwargs) -> ReflectionResult:
        """
        Analiza la respuesta generada

        Args:
            response: Respuesta del LLM
            context: Contexto usado
            query: Query original
            corrected_context: CorrectedContext del plugin anterior
            model_router: Router de modelos (para regenerar si es necesario)
            **kwargs: Opciones (allow_regeneration, etc.)

        Returns:
            ReflectionResult con análisis y posible respuesta mejorada
        """

        reflection_notes = []

        # 1. Detectar riesgo de alucinación
        hallucination_risk, hall_notes = self._detect_hallucination_risk(
            response, context, corrected_context
        )
        reflection_notes.extend(hall_notes)

        # 2. Verificar consistencia con fuentes
        consistency_score, cons_notes = self._verify_consistency(
            response, corrected_context.filtered_results
        )
        reflection_notes.extend(cons_notes)

        # 3. Decidir si necesita regeneración
        needs_regeneration, regen_reason = self._should_regenerate(
            hallucination_risk, consistency_score, corrected_context.confidence_level
        )

        # 4. Regenerar si es necesario y está permitido
        final_response = response
        was_regenerated = False

        if needs_regeneration and kwargs.get('allow_regeneration', True) and model_router:
            final_response, was_regenerated = self._regenerate_response(
                model_router, query, context, response,
                regen_reason, corrected_context, **kwargs
            )

            if was_regenerated:
                reflection_notes.append(f"Response regenerated: {regen_reason}")

                # Re-evaluar la nueva respuesta
                hallucination_risk, _ = self._detect_hallucination_risk(
                    final_response, context, corrected_context
                )
                consistency_score, _ = self._verify_consistency(
                    final_response, corrected_context.filtered_results
                )

        return ReflectionResult(
            final_response=final_response,
            hallucination_risk=hallucination_risk,
            consistency_score=consistency_score,
            needs_regeneration=needs_regeneration and not was_regenerated,
            regeneration_reason=regen_reason if needs_regeneration else None,
            reflection_notes=reflection_notes,
            was_regenerated=was_regenerated
        )

    def _detect_hallucination_risk(self, response: str, context: str,
                                  corrected_context) -> Tuple[str, List[str]]:
        """
        Detecta riesgo de alucinación

        Returns:
            (risk_level, notes)  donde risk_level = "low", "medium", "high"
        """

        notes = []
        risk_factors = 0

        response_lower = response.lower()

        # Factor 1: Respuesta muy larga para contexto pequeño
        if len(response.split()) > 200 and len(context.split()) < 500:
            risk_factors += 1
            notes.append("Response much longer than context - possible elaboration")

        # Factor 2: Contexto de baja confianza
        if corrected_context.confidence_level == "low":
            risk_factors += 1
            notes.append("Low confidence in source context")

        # Factor 3: Respuesta no menciona incertidumbre a pesar de info faltante
        has_uncertainty = any(phrase in response_lower for phrase in self.uncertainty_phrases)

        if corrected_context.missing_info_detected and not has_uncertainty:
            risk_factors += 2
            notes.append("Missing info but response shows no uncertainty - HIGH RISK")

        # Factor 4: Afirmaciones muy específicas (patterns)
        import re
        for pattern in self.hallucination_patterns:
            if re.search(pattern, response_lower):
                risk_factors += 1
                notes.append(f"Specific claim detected (pattern: {pattern[:30]}...)")
                break

        # Determinar nivel de riesgo
        if risk_factors == 0:
            return "low", notes
        elif risk_factors <= 2:
            return "medium", notes
        else:
            return "high", notes

    def _verify_consistency(self, response: str, results: List) -> Tuple[float, List[str]]:
        """
        Verifica consistencia de la respuesta con las fuentes

        Returns:
            (consistency_score, notes)  donde score = 0.0-1.0
        """

        notes = []

        if not results:
            notes.append("No sources to verify against")
            return 0.5, notes

        # Heurística simple: contar cuántas palabras clave de la respuesta
        # aparecen en el contexto

        response_words = set(response.lower().split())

        # Filtrar stop words comunes
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
                     'can', 'could', 'may', 'might', 'must', 'this', 'that', 'these', 'those'}

        response_keywords = response_words - stop_words

        # Combinar todo el contexto
        context_text = " ".join([r.content.lower() for r in results])
        context_words = set(context_text.split())

        # Calcular overlap
        if not response_keywords:
            return 0.5, notes

        overlap = len(response_keywords & context_words)
        consistency_score = overlap / len(response_keywords)

        # Ajustar score
        consistency_score = min(1.0, consistency_score * 1.2)  # Boost un poco

        if consistency_score < 0.5:
            notes.append(f"Low keyword overlap with sources ({consistency_score:.2f})")
        elif consistency_score > 0.8:
            notes.append(f"High consistency with sources ({consistency_score:.2f})")

        return consistency_score, notes

    def _should_regenerate(self, hallucination_risk: str, consistency_score: float,
                          context_confidence: str) -> Tuple[bool, Optional[str]]:
        """
        Decide si la respuesta debe regenerarse

        Returns:
            (should_regenerate, reason)
        """

        # Regenerar si:
        # 1. Riesgo alto de alucinación
        if hallucination_risk == "high":
            return True, "High hallucination risk detected"

        # 2. Consistencia muy baja con contexto de buena calidad
        if consistency_score < 0.4 and context_confidence in ["high", "medium"]:
            return True, f"Low consistency ({consistency_score:.2f}) despite good context"

        # 3. Combinación de factores medianos
        if hallucination_risk == "medium" and consistency_score < 0.5:
            return True, "Multiple moderate risk factors"

        return False, None

    def _regenerate_response(self, model_router, query: str, context: str,
                            original_response: str, reason: str,
                            corrected_context, **kwargs) -> Tuple[str, bool]:
        """
        Regenera la respuesta con prompt mejorado

        Returns:
            (new_response, was_regenerated)
        """

        try:
            # Crear prompt mejorado que enfatice adherencia a fuentes
            improved_prompt = f"""You are ARGO, an enterprise project management assistant.

IMPORTANT: Answer ONLY based on the provided context. Do not add information not present in the sources.

{context}

User question: {query}

Guidelines:
- Answer STRICTLY based on the context above
- If information is missing, explicitly state "This information is not available in the provided sources"
- Cite specific sources when making claims
- Be concise and professional
- Do NOT elaborate beyond what's in the sources

Your answer:"""

            messages = [
                {"role": "user", "content": improved_prompt}
            ]

            # Regenerar
            new_response = model_router.route(
                messages=messages,
                task_type="chat",
                project_id=kwargs.get('project_id', 'unknown')
            )

            return new_response.content, True

        except Exception as e:
            # Si falla, retornar original
            return original_response, False
