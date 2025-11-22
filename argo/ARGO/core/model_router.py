"""
ARGO v9.0 - Model Router
Router inteligente que selecciona el mejor modelo según task_type, project_type y preferencias
Integra tracking automático de tokens y costes
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

from core.llm_provider import BaseProvider, LLMResponse, create_provider
from core.logger import get_logger

logger = get_logger("ModelRouter")


@dataclass
class RouterConfig:
    """Configuración del router"""
    pricing: Dict[str, Any]
    budget: Dict[str, float]
    defaults: Dict[str, Any]
    
    @classmethod
    def from_file(cls, config_path: Path):
        """Carga configuración desde archivo JSON"""
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls(
            pricing=data.get('pricing', {}),
            budget=data.get('budget', {}),
            defaults=data.get('defaults', {})
        )


class ModelRouter:
    """
    Router inteligente de modelos LLM
    
    Responsabilidades:
    - Seleccionar proveedor y modelo según contexto
    - Registrar uso de tokens y costes
    - Aplicar fallbacks si un proveedor falla
    - Respetar presupuestos configurados
    """
    
    def __init__(
        self,
        providers: Dict[str, BaseProvider],
        config: RouterConfig,
        db_manager=None  # UnifiedDatabase instance
    ):
        self.providers = providers
        self.config = config
        self.db = db_manager
        
        logger.info(
            f"ModelRouter inicializado - "
            f"Providers: {list(providers.keys())}, "
            f"Budget: ${config.budget.get('monthly_usd', 0)}/month"
        )
    
    def route(
        self,
        messages: List[Dict[str, str]],
        task_type: str = "chat",
        project_id: Optional[str] = None,
        project_type: str = "standard",
        conversation_id: Optional[str] = None,
        override_model: Optional[str] = None,
        override_provider: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List] = None,
    ) -> LLMResponse:
        """
        Rutea la petición al modelo apropiado
        
        Args:
            messages: Lista de mensajes de la conversación
            task_type: Tipo de tarea (chat, analysis, synthesis, technical, reasoning)
            project_id: ID del proyecto
            project_type: Tipo de proyecto (standard, ed_sto, library)
            conversation_id: ID de la conversación
            override_model: Forzar modelo específico
            override_provider: Forzar proveedor específico
            temperature: Temperatura del modelo (override)
            max_tokens: Max tokens (override)
            system_prompt: System prompt
            tools: Tools para function calling
            
        Returns:
            LLMResponse con la respuesta del modelo
        """
        
        # 1. Seleccionar proveedor y modelo
        provider_name, model_name = self._select_provider_and_model(
            task_type=task_type,
            project_type=project_type,
            override_model=override_model,
            override_provider=override_provider
        )
        
        # 2. Obtener configuración del task type
        task_config = self.config.defaults.get('task_types', {}).get(task_type, {})
        
        # 3. Aplicar overrides
        final_temperature = temperature if temperature is not None else task_config.get('temperature', 0.7)
        final_max_tokens = max_tokens if max_tokens is not None else task_config.get('max_tokens', 2000)
        
        # 4. Obtener provider
        provider = self.providers.get(provider_name)
        if not provider:
            logger.error(f"Proveedor no disponible: {provider_name}")
            # Fallback a primer proveedor disponible
            provider_name = list(self.providers.keys())[0]
            provider = self.providers[provider_name]
            logger.warning(f"Usando fallback provider: {provider_name}")
        
        # 5. Generar respuesta
        try:
            logger.debug(
                f"Routing request - Provider: {provider_name}, Model: {model_name}, "
                f"Task: {task_type}, Project: {project_type}"
            )
            
            response = provider.generate(
                messages=messages,
                model=model_name,
                temperature=final_temperature,
                max_tokens=final_max_tokens,
                system_prompt=system_prompt,
                tools=tools
            )
            
            # 6. Registrar uso
            if self.db:
                self._track_usage(
                    response=response,
                    project_id=project_id,
                    conversation_id=conversation_id,
                    task_type=task_type,
                    project_type=project_type
                )
            
            # 7. Verificar budget
            self._check_budget_alerts()
            
            return response
            
        except Exception as e:
            logger.error(
                f"Error en route - Provider: {provider_name}, Model: {model_name}, Error: {str(e)}"
            )
            
            # Intentar fallback si está configurado
            if len(self.providers) > 1:
                logger.warning("Intentando fallback provider")
                return self._fallback_route(
                    messages=messages,
                    failed_provider=provider_name,
                    task_type=task_type,
                    project_id=project_id,
                    temperature=final_temperature,
                    max_tokens=final_max_tokens,
                    system_prompt=system_prompt
                )
            
            raise
    
    def _select_provider_and_model(
        self,
        task_type: str,
        project_type: str,
        override_model: Optional[str] = None,
        override_provider: Optional[str] = None
    ) -> Tuple[str, str]:
        """Selecciona proveedor y modelo según contexto"""
        
        # Override directo
        if override_model and override_provider:
            return override_provider, override_model
        
        # Buscar configuración del task type
        task_config = self.config.defaults.get('task_types', {}).get(task_type, {})
        
        if not task_config:
            # Fallback a chat
            logger.warning(f"Task type desconocido: {task_type}, usando 'chat'")
            task_config = self.config.defaults.get('task_types', {}).get('chat', {})
        
        provider = override_provider or task_config.get('provider', 'openai')
        model = override_model or task_config.get('model', 'gpt-4o-mini')
        
        # Ajustes según project_type
        if project_type == "ed_sto" and task_type == "analysis":
            # ED/STO projects usan modelos más robustos para análisis
            project_config = self.config.defaults.get('project_types', {}).get('ed_sto', {})
            model = project_config.get('analysis_model', model)
        
        return provider, model
    
    def _track_usage(
        self,
        response: LLMResponse,
        project_id: Optional[str],
        conversation_id: Optional[str],
        task_type: str,
        project_type: str
    ):
        """Registra uso de tokens y coste en la base de datos"""
        
        usage = response.usage or {}
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        total_tokens = usage.get('total_tokens', prompt_tokens + completion_tokens)
        
        # Calcular coste
        cost = self._estimate_cost(
            provider=response.provider,
            model=response.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        # Registrar en DB
        try:
            self.db.insert_api_usage(
                timestamp=datetime.utcnow(),
                project_id=project_id,
                conversation_id=conversation_id,
                provider=response.provider,
                model=response.model,
                operation=task_type,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_estimated=cost,
                metadata_json={
                    "project_type": project_type,
                    "latency_ms": response.latency_ms,
                    "finish_reason": response.metadata.get('finish_reason') or response.metadata.get('stop_reason')
                }
            )
            
            logger.debug(
                f"Usage tracked - Tokens: {total_tokens}, Cost: ${round(cost, 4)}, "
                f"Provider: {response.provider}, Model: {response.model}"
            )
            
        except Exception as e:
            logger.error(f"Error tracking usage: {str(e)}")
    
    def _estimate_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Estima el coste de una petición"""
        
        pricing = self.config.pricing.get(provider, {}).get(model, {})
        
        if not pricing:
            logger.warning(f"No pricing data for {provider}/{model}")
            return 0.0
        
        input_per_1k = pricing.get('input_per_1k', 0)
        output_per_1k = pricing.get('output_per_1k', 0)
        
        cost_input = (prompt_tokens / 1000.0) * input_per_1k
        cost_output = (completion_tokens / 1000.0) * output_per_1k
        
        return cost_input + cost_output
    
    def _check_budget_alerts(self):
        """Verifica si se están acercando a los límites de presupuesto"""
        
        if not self.db:
            return
        
        try:
            # Obtener uso del mes actual
            monthly_usage = self.db.get_monthly_usage()
            monthly_cost = monthly_usage.get('total_cost', 0)
            
            budget_monthly = self.config.budget.get('monthly_usd', 0)
            
            if budget_monthly > 0:
                percent_used = (monthly_cost / budget_monthly) * 100
                
                alert_threshold = self.config.budget.get('alert_threshold_percent', 80)
                critical_threshold = self.config.budget.get('critical_threshold_percent', 95)
                
                if percent_used >= critical_threshold:
                    logger.critical(
                        f"⚠️ PRESUPUESTO CRÍTICO: {percent_used:.1f}% usado (${monthly_cost:.2f}/${budget_monthly:.2f})"
                    )
                elif percent_used >= alert_threshold:
                    logger.warning(
                        f"⚠️ Presupuesto alto: {percent_used:.1f}% usado (${monthly_cost:.2f}/${budget_monthly:.2f})"
                    )
                    
        except Exception as e:
            logger.error(f"Error checking budget: {str(e)}")
    
    def _fallback_route(
        self,
        messages: List[Dict[str, str]],
        failed_provider: str,
        task_type: str,
        project_id: Optional[str],
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str]
    ) -> LLMResponse:
        """Intenta con otro proveedor si el principal falla"""
        
        # Buscar proveedor alternativo
        available = [p for p in self.providers.keys() if p != failed_provider]
        
        if not available:
            raise Exception("No hay proveedores alternativos disponibles")
        
        fallback_provider = available[0]
        provider = self.providers[fallback_provider]
        
        # Usar modelo por defecto del proveedor
        fallback_model = provider.default_model
        
        logger.info(
            f"Fallback activado - From: {failed_provider}, To: {fallback_provider}, Model: {fallback_model}"
        )
        
        return provider.generate(
            messages=messages,
            model=fallback_model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt
        )
    
    def get_usage_stats(
        self,
        project_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Obtiene estadísticas de uso"""
        
        if not self.db:
            return {}
        
        try:
            stats = self.db.get_usage_stats(project_id=project_id, days=days)
            
            # Agregar info de presupuesto
            monthly_cost = stats.get('total_cost', 0)
            budget_monthly = self.config.budget.get('monthly_usd', 0)
            
            if budget_monthly > 0:
                stats['budget'] = {
                    'monthly_limit': budget_monthly,
                    'used': monthly_cost,
                    'remaining': budget_monthly - monthly_cost,
                    'percent_used': (monthly_cost / budget_monthly) * 100
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting usage stats: {str(e)}")
            return {}


def create_router_from_config(
    config_path: Path,
    openai_key: str,
    anthropic_key: Optional[str] = None,
    db_manager=None
) -> ModelRouter:
    """Factory para crear router desde configuración"""
    
    # Cargar config
    config = RouterConfig.from_file(config_path)
    
    # Crear proveedores
    providers = {}
    
    # OpenAI siempre disponible
    providers['openai'] = create_provider(
        provider_name='openai',
        api_key=openai_key,
        default_model='gpt-4o-mini'
    )
    
    # Anthropic opcional
    if anthropic_key:
        providers['anthropic'] = create_provider(
            provider_name='anthropic',
            api_key=anthropic_key,
            default_model='claude-3-5-sonnet-20241022'
        )
    
    return ModelRouter(
        providers=providers,
        config=config,
        db_manager=db_manager
    )
