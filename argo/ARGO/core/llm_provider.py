"""
ARGO v9.0 - LLM Provider Abstraction
Sistema de abstracción para múltiples proveedores de LLM (OpenAI, Anthropic, etc.)
"""
from dataclasses import dataclass, field
from typing import Protocol, List, Dict, Any, Optional
from abc import ABC, abstractmethod
import time
import os

from core.logger import get_logger

logger = get_logger("LLMProvider")


@dataclass
class LLMResponse:
    """Respuesta estandarizada de cualquier proveedor LLM"""
    content: str
    provider: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_response: Any = None
    latency_ms: float = 0.0
    
    def __post_init__(self):
        # Asegurar estructura de usage
        if not self.usage:
            self.usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }


class LLMProvider(Protocol):
    """Protocol para todos los proveedores LLM"""
    
    @property
    def name(self) -> str:
        """Nombre del proveedor"""
        ...
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        tools: Optional[List] = None,
        system_prompt: Optional[str] = None,
        stream: bool = False,
    ) -> LLMResponse:
        """Genera respuesta del modelo"""
        ...


class BaseProvider(ABC):
    """Clase base para proveedores con funcionalidad común"""
    
    def __init__(self, api_key: str, default_model: str):
        self.api_key = api_key
        self.default_model = default_model
        self._client = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre del proveedor"""
        pass
    
    @abstractmethod
    def _initialize_client(self):
        """Inicializa el cliente del proveedor"""
        pass
    
    def _ensure_client(self):
        """Asegura que el cliente esté inicializado"""
        if self._client is None:
            self._initialize_client()
    
    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        tools: Optional[List] = None,
        system_prompt: Optional[str] = None,
        stream: bool = False,
    ) -> LLMResponse:
        """Genera respuesta del modelo"""
        pass


class OpenAIProvider(BaseProvider):
    """Proveedor para modelos OpenAI (GPT-4, GPT-5, o1, etc.)"""
    
    @property
    def name(self) -> str:
        return "openai"
    
    def _initialize_client(self):
        """Inicializa cliente OpenAI"""
        try:
            from langchain_openai import ChatOpenAI
            self._client = ChatOpenAI
            logger.info("Cliente OpenAI inicializado")
        except ImportError:
            logger.error("langchain_openai no está instalado")
            raise
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        tools: Optional[List] = None,
        system_prompt: Optional[str] = None,
        stream: bool = False,
    ) -> LLMResponse:
        """Genera respuesta con OpenAI"""
        self._ensure_client()
        
        start_time = time.time()
        
        try:
            # Preparar mensajes
            formatted_messages = self._format_messages(messages, system_prompt)
            
            # Crear instancia del modelo
            llm = self._client(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                openai_api_key=self.api_key
            )
            
            # Generar respuesta
            if tools:
                llm = llm.bind_tools(tools)
            
            response = llm.invoke(formatted_messages)
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Extraer usage
            usage = {}
            if hasattr(response, 'response_metadata'):
                token_usage = response.response_metadata.get('token_usage', {})
                usage = {
                    "prompt_tokens": token_usage.get('prompt_tokens', 0),
                    "completion_tokens": token_usage.get('completion_tokens', 0),
                    "total_tokens": token_usage.get('total_tokens', 0)
                }
            
            logger.debug(
                f"OpenAI response",
                model=model,
                tokens=usage.get('total_tokens', 0),
                latency_ms=round(latency_ms, 2)
            )
            
            return LLMResponse(
                content=response.content,
                provider=self.name,
                model=model,
                usage=usage,
                metadata={
                    "finish_reason": getattr(response, 'response_metadata', {}).get('finish_reason'),
                },
                raw_response=response,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            logger.error(f"Error en OpenAI generate", model=model, error=str(e))
            raise
    
    def _format_messages(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Formatea mensajes para OpenAI"""
        formatted = []
        
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})
        
        formatted.extend(messages)
        return formatted


class AnthropicProvider(BaseProvider):
    """Proveedor para modelos Anthropic (Claude)"""
    
    @property
    def name(self) -> str:
        return "anthropic"
    
    def _initialize_client(self):
        """Inicializa cliente Anthropic"""
        try:
            from langchain_anthropic import ChatAnthropic
            self._client = ChatAnthropic
            logger.info("Cliente Anthropic inicializado")
        except ImportError:
            logger.error("langchain_anthropic no está instalado")
            raise
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        tools: Optional[List] = None,
        system_prompt: Optional[str] = None,
        stream: bool = False,
    ) -> LLMResponse:
        """Genera respuesta con Anthropic"""
        self._ensure_client()
        
        start_time = time.time()
        
        try:
            # Preparar mensajes (Claude no usa system en messages)
            formatted_messages = [m for m in messages if m.get('role') != 'system']
            
            # Crear instancia del modelo
            llm = self._client(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens or 4096,
                anthropic_api_key=self.api_key
            )
            
            # System prompt va aparte en Claude
            if system_prompt:
                # Buscar system prompt en messages
                system_msgs = [m for m in messages if m.get('role') == 'system']
                if system_msgs:
                    system_prompt = system_msgs[0]['content']
            
            # Generar respuesta
            if tools:
                llm = llm.bind_tools(tools)
            
            response = llm.invoke(formatted_messages)
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Extraer usage
            usage = {}
            if hasattr(response, 'response_metadata'):
                usage_data = response.response_metadata.get('usage', {})
                usage = {
                    "prompt_tokens": usage_data.get('input_tokens', 0),
                    "completion_tokens": usage_data.get('output_tokens', 0),
                    "total_tokens": usage_data.get('input_tokens', 0) + usage_data.get('output_tokens', 0)
                }
            
            logger.debug(
                f"Anthropic response",
                model=model,
                tokens=usage.get('total_tokens', 0),
                latency_ms=round(latency_ms, 2)
            )
            
            return LLMResponse(
                content=response.content,
                provider=self.name,
                model=model,
                usage=usage,
                metadata={
                    "stop_reason": getattr(response, 'response_metadata', {}).get('stop_reason'),
                },
                raw_response=response,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            logger.error(f"Error en Anthropic generate", model=model, error=str(e))
            raise
    
    def _format_messages(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Formatea mensajes para Anthropic"""
        # Claude no incluye system en messages
        return [m for m in messages if m.get('role') != 'system']


def create_provider(provider_name: str, api_key: str, default_model: str) -> BaseProvider:
    """Factory para crear proveedores"""
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
    }

    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        raise ValueError(f"Proveedor desconocido: {provider_name}")

    return provider_class(api_key=api_key, default_model=default_model)


class LLMProviderManager:
    """
    Gestor de múltiples proveedores LLM
    Maneja OpenAI, Anthropic y otros proveedores
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el gestor de proveedores

        Args:
            config: Configuración con API keys y modelos por defecto
        """
        self.config = config
        self.providers: Dict[str, BaseProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Inicializa todos los proveedores configurados"""
        apis_config = self.config.get('apis', {})

        # Inicializar OpenAI si está configurado
        openai_config = apis_config.get('openai', {})
        if openai_config.get('enabled', True):
            api_key = openai_config.get('api_key') or os.environ.get('OPENAI_API_KEY')
            if api_key:
                try:
                    self.providers['openai'] = create_provider(
                        'openai',
                        api_key,
                        openai_config.get('default_model', 'gpt-4o')
                    )
                    logger.info("✅ OpenAI provider initialized")
                except Exception as e:
                    logger.warning(f"⚠️ OpenAI provider failed to initialize: {e}")

        # Inicializar Anthropic si está configurado
        anthropic_config = apis_config.get('anthropic', {})
        if anthropic_config.get('enabled', False):
            api_key = anthropic_config.get('api_key') or os.environ.get('ANTHROPIC_API_KEY')
            if api_key:
                try:
                    self.providers['anthropic'] = create_provider(
                        'anthropic',
                        api_key,
                        anthropic_config.get('default_model', 'claude-3-5-sonnet-20241022')
                    )
                    logger.info("✅ Anthropic provider initialized")
                except Exception as e:
                    logger.warning(f"⚠️ Anthropic provider failed to initialize: {e}")

        if not self.providers:
            raise RuntimeError("No se pudo inicializar ningún proveedor LLM. Verifica tus API keys.")

    def get_provider(self, provider_name: str) -> Optional[BaseProvider]:
        """Obtiene un proveedor específico"""
        return self.providers.get(provider_name.lower())

    def has_provider(self, provider_name: str) -> bool:
        """Verifica si un proveedor está disponible"""
        return provider_name.lower() in self.providers

    def list_providers(self) -> List[str]:
        """Lista todos los proveedores disponibles"""
        return list(self.providers.keys())

    def generate(
        self,
        messages: List[Dict[str, str]],
        provider: str = "openai",
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        tools: Optional[List] = None,
        system_prompt: Optional[str] = None,
        stream: bool = False,
    ) -> LLMResponse:
        """
        Genera respuesta usando el proveedor especificado

        Args:
            messages: Lista de mensajes
            provider: Nombre del proveedor ('openai', 'anthropic')
            model: Modelo específico (usa default del proveedor si no se especifica)
            ... otros parámetros

        Returns:
            LLMResponse con la respuesta generada
        """
        provider_obj = self.get_provider(provider)
        if not provider_obj:
            raise ValueError(f"Proveedor no disponible: {provider}. Disponibles: {self.list_providers()}")

        # Usar modelo por defecto si no se especifica
        if model is None:
            model = provider_obj.default_model

        return provider_obj.generate(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            system_prompt=system_prompt,
            stream=stream
        )
