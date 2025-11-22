# ARGO v10.01 - Sistema de Plugins: Especificación Técnica Definitiva

**Versión:** 2.0 FINAL  
**Fecha:** 22 de Noviembre, 2025  
**Destinatario:** Claude Code  
**Propósito:** Implementación de arquitectura modular plug-and-play para análisis de cronogramas

---

## 🎯 EXECUTIVE SUMMARY

Implementar sistema de plugins modular para ARGO v10.01 que permita análisis especializado de cronogramas de proyectos nucleares (PALLAS reactor) mediante:

- **Parser XER**: Primavera P6 usando PyP6Xer (100% Python nativo)
- **Parser XML**: Microsoft Project usando ElementTree (built-in Python)
- **Análisis DCMA 14-Point**: Evaluación de calidad de cronogramas
- **Análisis CPM**: Critical Path Method y float analysis
- **Análisis EVM**: Earned Value Management

**Objetivo:** Sistema production-ready, extensible, sin dependencias externas complejas.

---

## 📦 STACK TECNOLÓGICO DEFINITIVO

### Decisiones Tecnológicas

```python
# requirements_plugins.txt

# === PARSERS ===
PyP6XER>=1.16.0              # XER parsing - 100% Python, sin dependencias
# ElementTree (built-in)     # XML parsing - ya incluido en Python

# === DATA PROCESSING ===
pandas>=2.0.0                # DataFrames para análisis
numpy>=1.24.0                # Operaciones numéricas

# === GRAPH ALGORITHMS ===
networkx>=3.0                # CPM, critical path, network analysis

# === DATE HANDLING ===
python-dateutil>=2.8.0       # Parsing y manipulación de fechas

# === EXISTING ARGO ===
streamlit>=1.28.0            # Ya instalado en ARGO
chromadb>=0.4.0              # Ya instalado en ARGO
```

### ❌ Dependencias EXCLUIDAS (y por qué)

```python
# NO INCLUIR:
# mpxj          - Requiere Java/JPype (overhead innecesario)
# aspose-tasks  - Comercial ($$$)
# pywin32       - Solo Windows, requiere MS Project instalado
# openpyxl      - No necesario para cronogramas
```

---

## 🏗️ ARQUITECTURA DEL SISTEMA

### Estructura de Directorios

```
argo/
├── core/
│   ├── __init__.py
│   ├── engine.py                    # Motor principal (existente)
│   ├── rag_engine.py               # RAG (existente)
│   ├── model_router.py             # GPT/Claude routing (existente)
│   └── database.py                 # SQLite (existente)
│
├── plugins/
│   ├── __init__.py
│   ├── base_plugin.py              # ✅ CREAR - Clase abstracta base
│   ├── plugin_manager.py           # ✅ CREAR - Gestor central
│   ├── plugin_registry.json        # ✅ CREAR - Registro persistente
│   │
│   ├── parsers/                    # ✅ CREAR - Parsers de cronogramas
│   │   ├── __init__.py
│   │   ├── xer_parser_plugin.py          # Parser Primavera P6 XER
│   │   ├── xml_parser_plugin.py          # Parser MS Project XML
│   │   └── universal_parser_plugin.py    # Wrapper unificado
│   │
│   ├── analysis/                   # ✅ CREAR - Análisis de cronogramas
│   │   ├── __init__.py
│   │   ├── dcma14_plugin.py              # DCMA 14-Point Assessment
│   │   ├── critical_path_plugin.py       # CPM Analysis
│   │   ├── float_analysis_plugin.py      # Float/Slack Analysis
│   │   └── evm_plugin.py                 # Earned Value Management
│   │
│   └── utils/                      # ✅ CREAR - Utilidades comunes
│       ├── __init__.py
│       ├── schedule_normalizer.py        # Normalización XER/XML → DataFrame
│       ├── date_utils.py                 # Utilidades de fechas
│       └── validators.py                 # Validaciones de datos
│
├── tests/                          # ✅ CREAR - Tests comprehensivos
│   ├── test_plugins/
│   │   ├── test_base_plugin.py
│   │   ├── test_plugin_manager.py
│   │   ├── test_xer_parser.py
│   │   ├── test_xml_parser.py
│   │   ├── test_dcma14.py
│   │   └── test_critical_path.py
│   │
│   └── fixtures/
│       ├── sample_pallas.xer             # Cronograma ejemplo PALLAS
│       ├── sample_project.xml            # MS Project ejemplo
│       └── expected_results.json         # Resultados esperados
│
└── ui/                             # ✅ MODIFICAR - Interfaz existente
    ├── plugin_interface.py               # Nueva UI para plugins
    └── schedule_analysis_ui.py           # UI análisis de cronogramas
```

---

## 🔧 COMPONENTES CORE

### 1. BasePlugin (Clase Abstracta)

**Archivo:** `plugins/base_plugin.py`

```python
"""
Clase base abstracta para todos los plugins de ARGO.
Proporciona interfaz estándar y gestión de lifecycle.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime

class PluginCategory(Enum):
    """Categorías de plugins"""
    PARSER = "parser"           # Parsers de archivos
    ANALYSIS = "analysis"       # Análisis de cronogramas
    VISUALIZATION = "viz"       # Visualizaciones
    EXPORT = "export"          # Exportadores
    UTILITY = "utility"        # Utilidades

class PluginStatus(Enum):
    """Estados del plugin"""
    INACTIVE = "inactive"      # No cargado
    LOADING = "loading"        # Cargando
    ACTIVE = "active"          # Activo y listo
    ERROR = "error"            # Error
    DISABLED = "disabled"      # Deshabilitado manualmente

@dataclass
class PluginMetadata:
    """Metadata del plugin"""
    name: str                           # Nombre del plugin
    version: str                        # Versión (semver)
    description: str                    # Descripción
    author: str                         # Autor
    category: PluginCategory            # Categoría
    dependencies: List[str]             # Dependencias Python
    supported_formats: List[str]        # Formatos soportados
    priority: int = 100                 # Prioridad (menor = mayor prioridad)
    enabled_by_default: bool = False    # Auto-habilitar
    requires_config: bool = False       # Requiere configuración

class PluginError(Exception):
    """Excepción base para errores de plugins"""
    pass

class PluginValidationError(PluginError):
    """Error de validación de entrada"""
    pass

class PluginExecutionError(PluginError):
    """Error durante ejecución"""
    pass

class BasePlugin(ABC):
    """
    Clase base abstracta para todos los plugins de ARGO.
    
    Cada plugin debe:
    1. Heredar de esta clase
    2. Implementar métodos abstractos
    3. Seguir convenciones de naming: *Plugin
    
    Lifecycle:
    1. __init__() - Construcción
    2. initialize() - Configuración
    3. execute() - Operación principal
    4. cleanup() - Limpieza de recursos
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.status = PluginStatus.INACTIVE
        self._metadata: Optional[PluginMetadata] = None
        self._config: Dict[str, Any] = {}
        self._initialized = False
        self._creation_time = datetime.now()
        self._execution_count = 0
        self._last_execution_time: Optional[datetime] = None
    
    # ==================== MÉTODOS ABSTRACTOS ====================
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """
        Retorna metadata del plugin.
        
        DEBE implementarse en cada plugin.
        
        Returns:
            PluginMetadata con información completa del plugin
            
        Example:
            return PluginMetadata(
                name="XER Parser",
                version="1.0.0",
                description="Parser para Primavera P6 XER",
                author="ARGO Team",
                category=PluginCategory.PARSER,
                dependencies=["xerparser", "pandas"],
                supported_formats=["xer"]
            )
        """
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Inicializa el plugin con configuración.
        
        DEBE implementarse en cada plugin.
        
        Args:
            config: Diccionario con parámetros de configuración
                   específicos del plugin
            
        Returns:
            True si inicialización exitosa, False en caso contrario
            
        Raises:
            PluginError: Si hay error crítico en inicialización
        """
        pass
    
    @abstractmethod
    def execute(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta la funcionalidad principal del plugin.
        
        DEBE implementarse en cada plugin.
        
        Args:
            input_data: Datos de entrada (tipo depende del plugin)
            **kwargs: Parámetros adicionales opcionales
            
        Returns:
            Diccionario con resultados:
            {
                "success": bool,
                "data": Any,           # Datos resultantes
                "metadata": Dict,      # Metadata de la operación
                "errors": List[str]    # Errores si los hay
            }
            
        Raises:
            PluginValidationError: Si input_data es inválido
            PluginExecutionError: Si hay error durante ejecución
        """
        pass
    
    # ==================== MÉTODOS OPCIONALES ====================
    
    def validate_input(self, input_data: Any) -> bool:
        """
        Valida datos de entrada antes de ejecutar.
        
        Override para validación personalizada.
        Default: retorna True (sin validación).
        
        Args:
            input_data: Datos a validar
            
        Returns:
            True si válido, False en caso contrario
        """
        return True
    
    def cleanup(self) -> None:
        """
        Limpia recursos del plugin al desactivar.
        
        Override para limpieza personalizada.
        Default: marca como inactivo.
        """
        self.status = PluginStatus.INACTIVE
        self._initialized = False
        self.logger.info(f"{self.__class__.__name__} limpiado")
    
    def on_error(self, error: Exception) -> Dict[str, Any]:
        """
        Handler de errores del plugin.
        
        Override para manejo personalizado de errores.
        
        Args:
            error: Excepción capturada
            
        Returns:
            Diccionario con información del error
        """
        self.logger.error(f"Error en {self.__class__.__name__}: {str(error)}", exc_info=True)
        self.status = PluginStatus.ERROR
        
        return {
            "success": False,
            "error": str(error),
            "error_type": type(error).__name__,
            "plugin": self.__class__.__name__,
            "timestamp": datetime.now().isoformat()
        }
    
    # ==================== MÉTODOS DE INFORMACIÓN ====================
    
    def get_status(self) -> PluginStatus:
        """Retorna estado actual del plugin"""
        return self.status
    
    def is_initialized(self) -> bool:
        """Verifica si plugin está inicializado"""
        return self._initialized
    
    def get_config(self) -> Dict[str, Any]:
        """Retorna configuración actual del plugin"""
        return self._config.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas de uso del plugin.
        
        Returns:
            Dict con estadísticas de ejecución
        """
        return {
            "creation_time": self._creation_time.isoformat(),
            "execution_count": self._execution_count,
            "last_execution": self._last_execution_time.isoformat() if self._last_execution_time else None,
            "status": self.status.value,
            "initialized": self._initialized
        }
    
    # ==================== HELPERS INTERNOS ====================
    
    def _mark_execution(self) -> None:
        """Marca que el plugin fue ejecutado (tracking interno)"""
        self._execution_count += 1
        self._last_execution_time = datetime.now()
    
    def __repr__(self) -> str:
        metadata = self.get_metadata()
        return f"<{self.__class__.__name__} v{metadata.version} [{self.status.value}]>"
```

---

### 2. PluginManager (Gestor Central)

**Archivo:** `plugins/plugin_manager.py`

```python
"""
Gestor central de plugins para ARGO.
Maneja descubrimiento, carga, ejecución y lifecycle de plugins.
"""

import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type, Any, Set
import logging

from plugins.base_plugin import (
    BasePlugin, 
    PluginCategory, 
    PluginStatus, 
    PluginMetadata,
    PluginError
)

class PluginManager:
    """
    Gestor central de plugins para ARGO.
    
    Responsabilidades:
    1. Descubrimiento automático de plugins
    2. Carga/descarga dinámica
    3. Gestión de dependencias
    4. Ejecución coordinada
    5. Persistencia de estado
    
    Usage:
        manager = PluginManager()
        manager.discover_plugins()
        manager.load_plugin("XERParserPlugin")
        result = manager.execute_plugin("XERParserPlugin", "file.xer")
    """
    
    def __init__(self, plugins_dir: str = "plugins", config_file: str = "plugin_registry.json"):
        """
        Inicializa el gestor de plugins.
        
        Args:
            plugins_dir: Directorio raíz de plugins
            config_file: Archivo JSON para persistencia
        """
        self.plugins_dir = Path(plugins_dir)
        self.config_file = self.plugins_dir / config_file
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Registros internos
        self.registered_plugins: Dict[str, Type[BasePlugin]] = {}
        self.active_plugins: Dict[str, BasePlugin] = {}
        self.plugin_metadata: Dict[str, PluginMetadata] = {}
        self.plugin_dependencies: Dict[str, Set[str]] = {}
        
        # Cargar registro persistente si existe
        self._load_registry()
        
        self.logger.info("PluginManager inicializado")
    
    # ==================== DESCUBRIMIENTO ====================
    
    def discover_plugins(self, auto_load_defaults: bool = True) -> List[str]:
        """
        Descubre automáticamente todos los plugins disponibles.
        
        Escanea directorios buscando clases que hereden de BasePlugin.
        
        Args:
            auto_load_defaults: Si cargar plugins habilitados por defecto
            
        Returns:
            Lista de nombres de plugins descubiertos
        """
        discovered = []
        
        self.logger.info(f"Escaneando plugins en {self.plugins_dir}")
        
        # Escanear subdirectorios (parsers, analysis, etc.)
        for category_dir in self.plugins_dir.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith('__'):
                continue
            
            if category_dir.name in ['utils', 'tests']:
                continue  # Skip utility directories
            
            # Buscar archivos *_plugin.py
            for plugin_file in category_dir.glob('*_plugin.py'):
                try:
                    # Construir nombre del módulo
                    module_path = f"plugins.{category_dir.name}.{plugin_file.stem}"
                    
                    # Importar módulo
                    module = importlib.import_module(module_path)
                    
                    # Buscar clases que hereden de BasePlugin
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, BasePlugin) and obj != BasePlugin:
                            plugin_name = obj.__name__
                            
                            # Registrar
                            self.registered_plugins[plugin_name] = obj
                            discovered.append(plugin_name)
                            
                            # Obtener metadata temporal
                            temp_instance = obj()
                            metadata = temp_instance.get_metadata()
                            self.plugin_metadata[plugin_name] = metadata
                            self.plugin_dependencies[plugin_name] = set(metadata.dependencies)
                            
                            self.logger.info(
                                f"✓ Plugin descubierto: {plugin_name} "
                                f"v{metadata.version} [{metadata.category.value}]"
                            )
                            
                            # Auto-cargar si está habilitado por defecto
                            if auto_load_defaults and metadata.enabled_by_default:
                                self.load_plugin(plugin_name)
                
                except Exception as e:
                    self.logger.error(f"✗ Error descubriendo plugin en {plugin_file}: {e}")
        
        self.logger.info(f"Descubrimiento completado: {len(discovered)} plugins encontrados")
        return discovered
    
    # ==================== CARGA/DESCARGA ====================
    
    def load_plugin(self, plugin_name: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Carga e inicializa un plugin.
        
        Args:
            plugin_name: Nombre del plugin a cargar
            config: Configuración opcional del plugin
            
        Returns:
            True si carga exitosa, False en caso contrario
        """
        # Ya está cargado
        if plugin_name in self.active_plugins:
            self.logger.warning(f"Plugin {plugin_name} ya está cargado")
            return True
        
        # No está registrado
        if plugin_name not in self.registered_plugins:
            self.logger.error(f"Plugin {plugin_name} no está registrado")
            return False
        
        try:
            # Obtener metadata
            metadata = self.plugin_metadata[plugin_name]
            
            # Verificar dependencias Python
            missing_deps = self._check_dependencies(metadata.dependencies)
            if missing_deps:
                self.logger.error(
                    f"Dependencias faltantes para {plugin_name}: {', '.join(missing_deps)}"
                )
                return False
            
            # Instanciar plugin
            plugin_class = self.registered_plugins[plugin_name]
            plugin_instance = plugin_class()
            plugin_instance.status = PluginStatus.LOADING
            
            # Inicializar
            config = config or {}
            if plugin_instance.initialize(config):
                self.active_plugins[plugin_name] = plugin_instance
                plugin_instance.status = PluginStatus.ACTIVE
                plugin_instance._initialized = True
                
                self.logger.info(f"✓ Plugin {plugin_name} cargado exitosamente")
                self._save_registry()
                return True
            else:
                self.logger.error(f"✗ Error inicializando plugin {plugin_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"✗ Error cargando plugin {plugin_name}: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Descarga un plugin activo.
        
        Args:
            plugin_name: Nombre del plugin a descargar
            
        Returns:
            True si descarga exitosa, False en caso contrario
        """
        if plugin_name not in self.active_plugins:
            self.logger.warning(f"Plugin {plugin_name} no está activo")
            return False
        
        try:
            plugin = self.active_plugins[plugin_name]
            plugin.cleanup()
            del self.active_plugins[plugin_name]
            
            self.logger.info(f"✓ Plugin {plugin_name} descargado")
            self._save_registry()
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Error descargando plugin {plugin_name}: {e}")
            return False
    
    def reload_plugin(self, plugin_name: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Recarga un plugin (descarga y vuelve a cargar).
        
        Args:
            plugin_name: Nombre del plugin
            config: Nueva configuración opcional
            
        Returns:
            True si recarga exitosa
        """
        self.logger.info(f"Recargando plugin {plugin_name}")
        
        if plugin_name in self.active_plugins:
            self.unload_plugin(plugin_name)
        
        return self.load_plugin(plugin_name, config)
    
    # ==================== EJECUCIÓN ====================
    
    def execute_plugin(
        self, 
        plugin_name: str, 
        input_data: Any, 
        validate: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Ejecuta un plugin activo.
        
        Args:
            plugin_name: Nombre del plugin a ejecutar
            input_data: Datos de entrada
            validate: Si validar input antes de ejecutar
            **kwargs: Parámetros adicionales para el plugin
            
        Returns:
            Diccionario con resultados de la ejecución
        """
        # Verificar que está activo
        if plugin_name not in self.active_plugins:
            return {
                "success": False,
                "error": f"Plugin {plugin_name} no está activo",
                "hint": "Usar load_plugin() primero"
            }
        
        plugin = self.active_plugins[plugin_name]
        
        try:
            # Validar entrada si requerido
            if validate and not plugin.validate_input(input_data):
                return {
                    "success": False,
                    "error": "Validación de entrada fallida",
                    "plugin": plugin_name
                }
            
            # Ejecutar
            self.logger.info(f"Ejecutando plugin {plugin_name}")
            result = plugin.execute(input_data, **kwargs)
            
            # Marcar ejecución
            plugin._mark_execution()
            
            # Asegurar que result tenga success
            if "success" not in result:
                result["success"] = True
            
            result["plugin"] = plugin_name
            result["execution_time"] = plugin._last_execution_time.isoformat()
            
            return result
            
        except Exception as e:
            return plugin.on_error(e)
    
    # ==================== CONSULTAS ====================
    
    def list_plugins(self, category: Optional[PluginCategory] = None, active_only: bool = False) -> List[str]:
        """
        Lista plugins según filtros.
        
        Args:
            category: Filtrar por categoría (None = todos)
            active_only: Solo plugins activos
            
        Returns:
            Lista de nombres de plugins
        """
        if active_only:
            plugins = list(self.active_plugins.keys())
        else:
            plugins = list(self.registered_plugins.keys())
        
        if category:
            plugins = [
                name for name in plugins
                if self.plugin_metadata[name].category == category
            ]
        
        return plugins
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información completa de un plugin.
        
        Args:
            plugin_name: Nombre del plugin
            
        Returns:
            Diccionario con información completa o None si no existe
        """
        if plugin_name not in self.registered_plugins:
            return None
        
        metadata = self.plugin_metadata[plugin_name]
        is_active = plugin_name in self.active_plugins
        
        info = {
            "name": metadata.name,
            "version": metadata.version,
            "description": metadata.description,
            "author": metadata.author,
            "category": metadata.category.value,
            "dependencies": metadata.dependencies,
            "supported_formats": metadata.supported_formats,
            "priority": metadata.priority,
            "enabled_by_default": metadata.enabled_by_default,
            "is_active": is_active,
            "status": self.active_plugins[plugin_name].status.value if is_active else "inactive"
        }
        
        # Agregar stats si está activo
        if is_active:
            info["stats"] = self.active_plugins[plugin_name].get_stats()
        
        return info
    
    def get_plugins_by_category(self, category: PluginCategory) -> List[str]:
        """Retorna lista de plugins por categoría"""
        return [
            name for name, metadata in self.plugin_metadata.items()
            if metadata.category == category
        ]
    
    def is_plugin_active(self, plugin_name: str) -> bool:
        """Verifica si un plugin está activo"""
        return plugin_name in self.active_plugins
    
    # ==================== DEPENDENCIAS ====================
    
    def _check_dependencies(self, dependencies: List[str]) -> List[str]:
        """
        Verifica dependencias Python y retorna las faltantes.
        
        Args:
            dependencies: Lista de nombres de paquetes
            
        Returns:
            Lista de dependencias faltantes (vacía si todas están)
        """
        missing = []
        
        for dep in dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                missing.append(dep)
        
        return missing
    
    def check_all_dependencies(self) -> Dict[str, List[str]]:
        """
        Verifica dependencias de todos los plugins.
        
        Returns:
            Dict[plugin_name -> lista de dependencias faltantes]
        """
        result = {}
        
        for plugin_name, deps in self.plugin_dependencies.items():
            missing = self._check_dependencies(list(deps))
            if missing:
                result[plugin_name] = missing
        
        return result
    
    # ==================== PERSISTENCIA ====================
    
    def _load_registry(self) -> None:
        """Carga registro de plugins desde archivo JSON"""
        if not self.config_file.exists():
            self.logger.info("No existe registro previo, creando nuevo")
            return
        
        try:
            with open(self.config_file, 'r') as f:
                registry = json.load(f)
            
            self.logger.info(f"Registro cargado desde {self.config_file}")
            
            # Aquí podrías auto-cargar plugins que estaban activos
            # Por ahora solo informativo
            
        except Exception as e:
            self.logger.error(f"Error cargando registro: {e}")
    
    def _save_registry(self) -> None:
        """Guarda registro de plugins a archivo JSON"""
        try:
            registry = {
                "active_plugins": list(self.active_plugins.keys()),
                "registered_plugins": list(self.registered_plugins.keys()),
                "last_updated": datetime.now().isoformat()
            }
            
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(registry, f, indent=2)
            
            self.logger.debug(f"Registro guardado en {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Error guardando registro: {e}")
    
    # ==================== UTILIDADES ====================
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Retorna resumen del estado del sistema de plugins.
        
        Returns:
            Dict con estadísticas globales
        """
        return {
            "total_registered": len(self.registered_plugins),
            "total_active": len(self.active_plugins),
            "by_category": {
                cat.value: len(self.get_plugins_by_category(cat))
                for cat in PluginCategory
            },
            "active_plugins": list(self.active_plugins.keys()),
            "missing_dependencies": self.check_all_dependencies()
        }
    
    def __repr__(self) -> str:
        return f"<PluginManager: {len(self.active_plugins)}/{len(self.registered_plugins)} plugins activos>"
```

---

## 📊 PLUGINS ESPECÍFICOS

### 3. XER Parser Plugin

**Archivo:** `plugins/parsers/xer_parser_plugin.py`

```python
"""
Parser para archivos Primavera P6 XER usando PyP6Xer.
100% Python nativo, sin dependencias externas.
"""

from typing import Dict, Any, List
from pathlib import Path
import pandas as pd
from datetime import datetime

from plugins.base_plugin import (
    BasePlugin, 
    PluginMetadata, 
    PluginCategory, 
    PluginStatus,
    PluginValidationError,
    PluginExecutionError
)

try:
    from xerparser import Xer
    XER_AVAILABLE = True
except ImportError:
    XER_AVAILABLE = False

class XERParserPlugin(BasePlugin):
    """
    Parser para archivos Primavera P6 XER.
    
    Utiliza PyP6Xer para extraer:
    - Proyectos y metadata
    - Actividades/Tareas con duraciones, fechas, progreso
    - Recursos y asignaciones
    - Calendarios
    - Relaciones (predecessors/successors) con lags
    - Códigos WBS
    - Float calculations
    
    Supported XER versions: 15.2, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0
    """
    
    def __init__(self):
        super().__init__()
        self.xer_data = None
        self.encoding = 'cp1252'  # Default Windows encoding for XER
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="XER Parser",
            version="1.0.0",
            description="Parser para archivos Primavera P6 XER usando PyP6Xer",
            author="ARGO Development Team",
            category=PluginCategory.PARSER,
            dependencies=["xerparser", "pandas"],
            supported_formats=["xer"],
            priority=100,
            enabled_by_default=True
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Inicializa el parser XER.
        
        Args:
            config: Configuración opcional:
                - encoding: Codificación del archivo (default: 'cp1252')
        """
        if not XER_AVAILABLE:
            self.logger.error("PyP6Xer no instalado. Instalar: pip install PyP6XER")
            return False
        
        self.encoding = config.get('encoding', 'cp1252')
        
        self._initialized = True
        self.status = PluginStatus.ACTIVE
        self.logger.info("XER Parser Plugin inicializado")
        return True
    
    def validate_input(self, input_data: Any) -> bool:
        """
        Valida que el input sea un archivo XER válido.
        
        Args:
            input_data: Path al archivo XER (str o Path)
        """
        try:
            file_path = Path(input_data)
            
            if not file_path.exists():
                raise PluginValidationError(f"Archivo no existe: {file_path}")
            
            if file_path.suffix.lower() != '.xer':
                raise PluginValidationError(f"Archivo no es XER: {file_path.suffix}")
            
            # Verificar que sea legible
            with open(file_path, 'r', encoding=self.encoding, errors='ignore') as f:
                first_line = f.readline()
                if not first_line.startswith('ERMHDR'):
                    raise PluginValidationError("Archivo no tiene formato XER válido")
            
            return True
            
        except PluginValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error validando archivo XER: {e}")
            return False
    
    def execute(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        Parsea archivo XER y extrae información completa.
        
        Args:
            input_data: Path al archivo XER
            **kwargs: Opciones:
                - extract_all: Extraer todos los datos (default: True)
                - projects_only: Solo info de proyectos (default: False)
                - include_baseline: Incluir baseline data (default: False)
        
        Returns:
            Dict con estructura normalizada:
            {
                "success": bool,
                "format": "XER",
                "file_info": {...},          # Metadata del archivo
                "projects": [...],           # Lista de proyectos
                "activities": DataFrame,     # Todas las actividades
                "relationships": DataFrame,  # Relaciones pred/succ
                "resources": DataFrame,      # Recursos
                "calendars": [...],          # Calendarios
                "stats": {...}               # Estadísticas
            }
        """
        try:
            file_path = Path(input_data)
            extract_all = kwargs.get('extract_all', True)
            projects_only = kwargs.get('projects_only', False)
            
            self.logger.info(f"Parseando archivo XER: {file_path.name}")
            
            # Parsear archivo XER
            xer = Xer(str(file_path))
            self.xer_data = xer
            
            # Estructura base del resultado
            result = {
                "success": True,
                "format": "XER",
                "file_path": str(file_path),
                "file_info": self._extract_file_info(xer)
            }
            
            # Si solo proyectos
            if projects_only:
                result["projects"] = self._extract_projects(xer)
                return result
            
            # Extracción completa
            if extract_all:
                result["projects"] = self._extract_projects(xer)
                result["activities"] = self._extract_activities(xer)
                result["relationships"] = self._extract_relationships(xer)
                result["resources"] = self._extract_resources(xer)
                result["calendars"] = self._extract_calendars(xer)
                result["stats"] = self._calculate_stats(xer, result)
            
            activities_count = len(result.get('activities', []))
            self.logger.info(f"✓ XER parseado: {activities_count} actividades")
            
            return result
            
        except Exception as e:
            raise PluginExecutionError(f"Error parseando XER: {e}")
    
    # ==================== EXTRACTORES ====================
    
    def _extract_file_info(self, xer: Xer) -> Dict[str, Any]:
        """Extrae metadata del archivo XER"""
        return {
            "export_date": xer.export_date.isoformat() if xer.export_date else None,
            "export_user": xer.export_user,
            "export_version": xer.export_version,
            "encoding": self.encoding,
            "file_type": "Primavera P6 XER"
        }
    
    def _extract_projects(self, xer: Xer) -> List[Dict[str, Any]]:
        """Extrae información de proyectos"""
        projects = []
        
        for project in xer.projects:
            projects.append({
                "project_id": project.proj_id,
                "project_code": project.proj_short_name,
                "project_name": project.proj_name,
                "start_date": project.plan_start_date.isoformat() if project.plan_start_date else None,
                "finish_date": project.plan_end_date.isoformat() if project.plan_end_date else None,
                "data_date": project.last_recalc_date.isoformat() if project.last_recalc_date else None,
                "total_activities": len(project.activities) if hasattr(project, 'activities') else 0,
                "status": project.proj_status if hasattr(project, 'proj_status') else None
            })
        
        return projects
    
    def _extract_activities(self, xer: Xer) -> pd.DataFrame:
        """
        Extrae todas las actividades como DataFrame normalizado.
        
        Columnas estándar:
        - activity_id, activity_code, activity_name
        - duration_days, start_date, finish_date
        - percent_complete, status
        - total_float_days, free_float_days
        - is_critical, wbs_id, calendar_id
        - project_id
        """
        activities_data = []
        
        for project in xer.projects:
            if not hasattr(project, 'activities'):
                continue
            
            for activity in project.activities:
                # Convertir horas a días (P6 usa horas internamente)
                duration_days = (activity.target_drtn_hr_cnt / 8.0) if activity.target_drtn_hr_cnt else 0.0
                total_float_days = (activity.total_float_hr_cnt / 8.0) if activity.total_float_hr_cnt else None
                free_float_days = (activity.free_float_hr_cnt / 8.0) if activity.free_float_hr_cnt else None
                
                # Determinar si es crítica (float <= 0)
                is_critical = total_float_days is not None and total_float_days <= 0
                
                activities_data.append({
                    # Identificación
                    "activity_id": activity.task_id,
                    "activity_code": activity.task_code,
                    "activity_name": activity.task_name,
                    
                    # Duración y fechas
                    "duration_days": duration_days,
                    "start_date": activity.act_start_date.isoformat() if activity.act_start_date else None,
                    "finish_date": activity.act_end_date.isoformat() if activity.act_end_date else None,
                    "early_start": activity.early_start_date.isoformat() if hasattr(activity, 'early_start_date') and activity.early_start_date else None,
                    "early_finish": activity.early_end_date.isoformat() if hasattr(activity, 'early_end_date') and activity.early_end_date else None,
                    "late_start": activity.late_start_date.isoformat() if hasattr(activity, 'late_start_date') and activity.late_start_date else None,
                    "late_finish": activity.late_end_date.isoformat() if hasattr(activity, 'late_end_date') and activity.late_end_date else None,
                    
                    # Progreso y estado
                    "percent_complete": activity.phys_complete_pct if activity.phys_complete_pct else 0.0,
                    "status": activity.status_code,
                    
                    # Float y criticidad
                    "total_float_days": total_float_days,
                    "free_float_days": free_float_days,
                    "is_critical": is_critical,
                    
                    # Referencias
                    "wbs_id": activity.wbs_id,
                    "calendar_id": activity.clndr_id,
                    "project_id": project.proj_id,
                    
                    # Tipo de actividad
                    "task_type": activity.task_type if hasattr(activity, 'task_type') else None,
                    
                    # Constraint (si existe)
                    "constraint_type": activity.cstr_type if hasattr(activity, 'cstr_type') else None,
                    "constraint_date": activity.cstr_date.isoformat() if hasattr(activity, 'cstr_date') and activity.cstr_date else None
                })
        
        df = pd.DataFrame(activities_data)
        
        # Convertir fechas a datetime
        date_columns = ['start_date', 'finish_date', 'early_start', 'early_finish', 'late_start', 'late_finish', 'constraint_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    
    def _extract_relationships(self, xer: Xer) -> pd.DataFrame:
        """
        Extrae relaciones entre actividades.
        
        Columnas:
        - predecessor_id, successor_id
        - relationship_type (PR_FS, PR_SS, PR_FF, PR_SF)
        - lag_days
        """
        relationships_data = []
        
        for relationship in xer.taskpreds:
            # Convertir lag de horas a días
            lag_days = (relationship.lag_hr_cnt / 8.0) if relationship.lag_hr_cnt else 0.0
            
            relationships_data.append({
                "predecessor_id": relationship.pred_task_id,
                "successor_id": relationship.task_id,
                "relationship_type": relationship.pred_type,  # PR_FS, PR_SS, etc.
                "lag_days": lag_days
            })
        
        return pd.DataFrame(relationships_data)
    
    def _extract_resources(self, xer: Xer) -> pd.DataFrame:
        """Extrae recursos del proyecto"""
        resources_data = []
        
        for resource in xer.resources:
            resources_data.append({
                "resource_id": resource.rsrc_id,
                "resource_name": resource.rsrc_name,
                "resource_type": resource.rsrc_type,
                "parent_id": resource.parent_rsrc_id
            })
        
        return pd.DataFrame(resources_data)
    
    def _extract_calendars(self, xer: Xer) -> List[Dict[str, Any]]:
        """Extrae información de calendarios"""
        calendars = []
        
        for calendar in xer.calendars:
            calendars.append({
                "calendar_id": calendar.clndr_id,
                "calendar_name": calendar.clndr_name,
                "is_default": calendar.default_flag,
                "hours_per_day": calendar.day_hr_cnt if hasattr(calendar, 'day_hr_cnt') else 8.0
            })
        
        return calendars
    
    def _calculate_stats(self, xer: Xer, result: Dict) -> Dict[str, Any]:
        """Calcula estadísticas del cronograma"""
        activities_df = result.get('activities')
        
        if activities_df is None or len(activities_df) == 0:
            return {}
        
        # Filtrar actividades activas (no completadas)
        active_activities = activities_df[activities_df['status'] != 'TK_Complete']
        
        stats = {
            "total_projects": len(xer.projects),
            "total_activities": len(activities_df),
            "active_activities": len(active_activities),
            "completed_activities": len(activities_df[activities_df['status'] == 'TK_Complete']),
            "total_resources": len(xer.resources),
            "total_calendars": len(xer.calendars),
            "total_relationships": len(result.get('relationships', [])),
            
            # Criticidad
            "critical_activities": len(activities_df[activities_df['is_critical'] == True]),
            "critical_path_length": activities_df[activities_df['is_critical'] == True]['duration_days'].sum(),
            
            # Progreso
            "average_completion": activities_df['percent_complete'].mean(),
            
            # Float
            "activities_with_negative_float": len(active_activities[active_activities['total_float_days'] < 0]),
            "activities_with_high_float": len(active_activities[active_activities['total_float_days'] > 44]),
        }
        
        return stats
    
    # ==================== UTILIDADES PÚBLICAS ====================
    
    def get_critical_path_activities(self) -> pd.DataFrame:
        """
        Retorna solo actividades de ruta crítica.
        
        Requiere haber ejecutado execute() primero.
        """
        if self.xer_data is None:
            raise PluginExecutionError("No hay datos XER. Ejecutar execute() primero.")
        
        # Re-extraer actividades y filtrar críticas
        activities_df = self._extract_activities(self.xer_data)
        critical = activities_df[activities_df['is_critical'] == True]
        
        return critical.sort_values('start_date')
```

---

### 4. XML Parser Plugin (MS Project)

**Archivo:** `plugins/parsers/xml_parser_plugin.py`

```python
"""
Parser para archivos MS Project XML (MSPDI format).
100% Python nativo usando ElementTree (built-in).
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from pathlib import Path
import pandas as pd
from datetime import datetime

from plugins.base_plugin import (
    BasePlugin, 
    PluginMetadata, 
    PluginCategory, 
    PluginStatus,
    PluginValidationError,
    PluginExecutionError
)

class XMLParserPlugin(BasePlugin):
    """
    Parser para archivos MS Project XML (MSPDI - Microsoft Project Data Interchange).
    
    Extrae:
    - Proyectos y metadata
    - Tareas con duraciones, fechas, progreso
    - Recursos y asignaciones
    - Relaciones entre tareas (predecessors/successors)
    - WBS (Work Breakdown Structure)
    - Calendarios
    
    Formato soportado: MS Project 2007-2021 XML
    """
    
    # Namespace de MS Project XML
    NS = {'ms': 'http://schemas.microsoft.com/project'}
    
    def __init__(self):
        super().__init__()
        self.tree = None
        self.root = None
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="XML Parser (MS Project)",
            version="1.0.0",
            description="Parser para MS Project XML usando ElementTree nativo",
            author="ARGO Development Team",
            category=PluginCategory.PARSER,
            dependencies=["pandas"],  # ElementTree es built-in
            supported_formats=["xml"],
            priority=101,
            enabled_by_default=True
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Inicializa el parser XML"""
        self._initialized = True
        self.status = PluginStatus.ACTIVE
        self.logger.info("XML Parser Plugin inicializado")
        return True
    
    def validate_input(self, input_data: Any) -> bool:
        """
        Valida que el input sea un archivo XML válido de MS Project.
        """
        try:
            file_path = Path(input_data)
            
            if not file_path.exists():
                raise PluginValidationError(f"Archivo no existe: {file_path}")
            
            if file_path.suffix.lower() != '.xml':
                raise PluginValidationError(f"Archivo no es XML: {file_path.suffix}")
            
            # Intentar parsear XML
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Verificar que sea MS Project XML
            if 'microsoft.com/project' not in root.tag:
                raise PluginValidationError("XML no es formato MS Project (MSPDI)")
            
            return True
            
        except ET.ParseError as e:
            raise PluginValidationError(f"XML malformado: {e}")
        except PluginValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error validando XML: {e}")
            return False
    
    def execute(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        Parsea archivo XML de MS Project.
        
        Args:
            input_data: Path al archivo XML
            **kwargs: Opciones:
                - extract_all: Extraer todos los datos (default: True)
                - projects_only: Solo info de proyectos (default: False)
        
        Returns:
            Dict con estructura normalizada (igual que XER):
            {
                "success": bool,
                "format": "MS Project XML",
                "file_info": {...},
                "projects": [...],
                "activities": DataFrame,
                "relationships": DataFrame,
                "resources": DataFrame,
                "calendars": [...],
                "stats": {...}
            }
        """
        try:
            file_path = Path(input_data)
            extract_all = kwargs.get('extract_all', True)
            projects_only = kwargs.get('projects_only', False)
            
            self.logger.info(f"Parseando archivo XML: {file_path.name}")
            
            # Parsear XML
            self.tree = ET.parse(file_path)
            self.root = self.tree.getroot()
            
            # Estructura base
            result = {
                "success": True,
                "format": "MS Project XML",
                "file_path": str(file_path),
                "file_info": self._extract_file_info()
            }
            
            # Si solo proyectos
            if projects_only:
                result["projects"] = self._extract_projects()
                return result
            
            # Extracción completa
            if extract_all:
                result["projects"] = self._extract_projects()
                result["activities"] = self._extract_activities()
                result["relationships"] = self._extract_relationships()
                result["resources"] = self._extract_resources()
                result["calendars"] = self._extract_calendars()
                result["stats"] = self._calculate_stats(result)
            
            activities_count = len(result.get('activities', []))
            self.logger.info(f"✓ XML parseado: {activities_count} actividades")
            
            return result
            
        except Exception as e:
            raise PluginExecutionError(f"Error parseando XML: {e}")
    
    # ==================== EXTRACTORES ====================
    
    def _extract_file_info(self) -> Dict[str, Any]:
        """Extrae metadata del archivo XML"""
        return {
            "creation_date": self._get_text('.//ms:CreationDate'),
            "last_saved": self._get_text('.//ms:LastSaved'),
            "author": self._get_text('.//ms:Author'),
            "company": self._get_text('.//ms:Company'),
            "save_version": self._get_text('.//ms:SaveVersion'),
            "file_type": "Microsoft Project XML (MSPDI)"
        }
    
    def _extract_projects(self) -> List[Dict[str, Any]]:
        """Extrae información del proyecto"""
        projects = [{
            "project_id": 1,  # MS Project XML típicamente tiene 1 proyecto por archivo
            "project_code": self._get_text('.//ms:Title') or "Untitled",
            "project_name": self._get_text('.//ms:Title') or "Untitled Project",
            "start_date": self._get_text('.//ms:StartDate'),
            "finish_date": self._get_text('.//ms:FinishDate'),
            "data_date": self._get_text('.//ms:StatusDate'),
            "total_activities": len(self.root.findall('.//ms:Task', self.NS)),
            "status": self._get_text('.//ms:Status')
        }]
        
        return projects
    
    def _extract_activities(self) -> pd.DataFrame:
        """
        Extrae todas las tareas como DataFrame normalizado.
        
        Estructura compatible con XER parser.
        """
        activities_data = []
        
        for task in self.root.findall('.//ms:Task', self.NS):
            # IDs y nombres
            task_id = self._get_text_from_element(task, 'ms:UID')
            task_name = self._get_text_from_element(task, 'ms:Name')
            
            # Duración (MS Project usa formato PT...H - ISO 8601 duration)
            duration_text = self._get_text_from_element(task, 'ms:Duration')
            duration_days = self._parse_duration(duration_text)
            
            # Fechas
            start_date = self._get_text_from_element(task, 'ms:Start')
            finish_date = self._get_text_from_element(task, 'ms:Finish')
            
            # Progreso
            percent_complete = self._get_float_from_element(task, 'ms:PercentComplete')
            
            # WBS
            wbs = self._get_text_from_element(task, 'ms:WBS')
            outline_level = self._get_int_from_element(task, 'ms:OutlineLevel')
            
            # Constraint
            constraint_type = self._get_text_from_element(task, 'ms:ConstraintType')
            constraint_date = self._get_text_from_element(task, 'ms:ConstraintDate')
            
            # Milestone
            is_milestone = self._get_text_from_element(task, 'ms:Milestone') == '1'
            
            # Critical (en MS Project)
            is_critical = self._get_text_from_element(task, 'ms:Critical') == '1'
            
            activities_data.append({
                # Identificación
                "activity_id": task_id,
                "activity_code": wbs or task_id,
                "activity_name": task_name,
                
                # Duración y fechas
                "duration_days": duration_days,
                "start_date": start_date,
                "finish_date": finish_date,
                "early_start": None,  # MS Project no expone directamente
                "early_finish": None,
                "late_start": None,
                "late_finish": None,
                
                # Progreso y estado
                "percent_complete": percent_complete,
                "status": "Active" if percent_complete < 100 else "Complete",
                
                # Float y criticidad
                "total_float_days": None,  # Calcular después si es necesario
                "free_float_days": None,
                "is_critical": is_critical,
                
                # Referencias
                "wbs_id": wbs,
                "calendar_id": None,
                "project_id": 1,
                
                # Tipo
                "task_type": "Milestone" if is_milestone else "Task",
                
                # Constraint
                "constraint_type": self._map_constraint_type(constraint_type),
                "constraint_date": constraint_date,
                
                # Outline level
                "outline_level": outline_level
            })
        
        df = pd.DataFrame(activities_data)
        
        # Convertir fechas a datetime
        date_columns = ['start_date', 'finish_date', 'constraint_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    
    def _extract_relationships(self) -> pd.DataFrame:
        """
        Extrae relaciones (predecessors) entre tareas.
        """
        relationships_data = []
        
        for task in self.root.findall('.//ms:Task', self.NS):
            successor_id = self._get_text_from_element(task, 'ms:UID')
            
            # PredecessorLink puede estar múltiple
            pred_links = task.findall('ms:PredecessorLink', self.NS)
            
            for pred_link in pred_links:
                predecessor_id = self._get_text_from_element(pred_link, 'ms:PredecessorUID')
                relationship_type = self._get_text_from_element(pred_link, 'ms:Type')
                
                # Lag en MS Project está en formato ISO 8601 duration
                lag_text = self._get_text_from_element(pred_link, 'ms:LinkLag')
                lag_days = self._parse_duration(lag_text)
                
                relationships_data.append({
                    "predecessor_id": predecessor_id,
                    "successor_id": successor_id,
                    "relationship_type": self._map_relationship_type(relationship_type),
                    "lag_days": lag_days
                })
        
        return pd.DataFrame(relationships_data)
    
    def _extract_resources(self) -> pd.DataFrame:
        """Extrae recursos del proyecto"""
        resources_data = []
        
        for resource in self.root.findall('.//ms:Resource', self.NS):
            resources_data.append({
                "resource_id": self._get_text_from_element(resource, 'ms:UID'),
                "resource_name": self._get_text_from_element(resource, 'ms:Name'),
                "resource_type": self._get_text_from_element(resource, 'ms:Type'),
                "parent_id": None
            })
        
        return pd.DataFrame(resources_data)
    
    def _extract_calendars(self) -> List[Dict[str, Any]]:
        """Extrae información de calendarios"""
        calendars = []
        
        for calendar in self.root.findall('.//ms:Calendar', self.NS):
            calendars.append({
                "calendar_id": self._get_text_from_element(calendar, 'ms:UID'),
                "calendar_name": self._get_text_from_element(calendar, 'ms:Name'),
                "is_default": self._get_text_from_element(calendar, 'ms:IsBaseCalendar') == '1',
                "hours_per_day": 8.0  # Default
            })
        
        return calendars
    
    def _calculate_stats(self, result: Dict) -> Dict[str, Any]:
        """Calcula estadísticas del cronograma"""
        activities_df = result.get('activities')
        
        if activities_df is None or len(activities_df) == 0:
            return {}
        
        active_activities = activities_df[activities_df['status'] != 'Complete']
        
        stats = {
            "total_projects": 1,
            "total_activities": len(activities_df),
            "active_activities": len(active_activities),
            "completed_activities": len(activities_df[activities_df['status'] == 'Complete']),
            "total_resources": len(result.get('resources', [])),
            "total_calendars": len(result.get('calendars', [])),
            "total_relationships": len(result.get('relationships', [])),
            
            # Criticidad
            "critical_activities": len(activities_df[activities_df['is_critical'] == True]),
            
            # Progreso
            "average_completion": activities_df['percent_complete'].mean(),
            
            # Milestones
            "total_milestones": len(activities_df[activities_df['task_type'] == 'Milestone'])
        }
        
        return stats
    
    # ==================== HELPERS ====================
    
    def _get_text(self, xpath: str) -> str:
        """Helper para extraer texto vía XPath"""
        element = self.root.find(xpath, self.NS)
        return element.text if element is not None else None
    
    def _get_text_from_element(self, element: ET.Element, tag: str) -> str:
        """Helper para extraer texto de sub-elemento"""
        sub_element = element.find(tag, self.NS)
        return sub_element.text if sub_element is not None else None
    
    def _get_float_from_element(self, element: ET.Element, tag: str) -> float:
        """Helper para extraer float"""
        text = self._get_text_from_element(element, tag)
        try:
            return float(text) if text else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def _get_int_from_element(self, element: ET.Element, tag: str) -> int:
        """Helper para extraer int"""
        text = self._get_text_from_element(element, tag)
        try:
            return int(text) if text else 0
        except (ValueError, TypeError):
            return 0
    
    def _parse_duration(self, duration_text: str) -> float:
        """
        Parsea duración ISO 8601 (PT...H) a días.
        
        Ejemplo: PT80H0M0S = 80 horas = 10 días (8h/día)
        """
        if not duration_text:
            return 0.0
        
        try:
            # Formato típico: PT80H0M0S
            if duration_text.startswith('PT') and 'H' in duration_text:
                hours_str = duration_text.split('PT')[1].split('H')[0]
                hours = float(hours_str)
                return hours / 8.0  # Convertir a días (8h/día)
        except Exception as e:
            self.logger.warning(f"No se pudo parsear duración: {duration_text}")
        
        return 0.0
    
    def _map_relationship_type(self, ms_type: str) -> str:
        """
        Mapea tipo de relación de MS Project a formato P6.
        
        MS Project: 0=FF, 1=FS, 2=SF, 3=SS
        P6: PR_FF, PR_FS, PR_SF, PR_SS
        """
        mapping = {
            '0': 'PR_FF',
            '1': 'PR_FS',
            '2': 'PR_SF',
            '3': 'PR_SS'
        }
        return mapping.get(ms_type, 'PR_FS')  # Default FS
    
    def _map_constraint_type(self, ms_constraint: str) -> str:
        """
        Mapea tipo de constraint de MS Project a formato genérico.
        
        MS Project: 0=As Soon As Possible, 1=As Late As Possible, 
                    2=Must Start On, 3=Must Finish On, etc.
        """
        mapping = {
            '0': 'ASAP',
            '1': 'ALAP',
            '2': 'MSO',  # Must Start On
            '3': 'MFO',  # Must Finish On
            '4': 'SNET', # Start No Earlier Than
            '5': 'SNLT', # Start No Later Than
            '6': 'FNET', # Finish No Earlier Than
            '7': 'FNLT'  # Finish No Later Than
        }
        return mapping.get(ms_constraint, 'ASAP')
```

---

### 5. DCMA 14-Point Plugin (Continuación en próximo mensaje por límite de longitud)

**Archivo:** `plugins/analysis/dcma14_plugin.py`

El código del DCMA14Plugin es extenso. ¿Quieres que continúe con:

1. DCMA14Plugin completo
2. CriticalPathPlugin
3. EVMPlugin
4. Interfaz UI para Streamlit
5. Tests unitarios

O prefieres que genere un **segundo archivo** con todos los plugins de análisis juntos?

---

## 📋 PRÓXIMOS PASOS PARA CLAUDE CODE

### Fase 1: Infraestructura (AHORA)
```bash
# Crear estructura
mkdir -p plugins/{parsers,analysis,utils}
mkdir -p tests/{test_plugins,fixtures}

# Implementar base
1. plugins/base_plugin.py ✅
2. plugins/plugin_manager.py ✅
3. plugins/parsers/xer_parser_plugin.py ✅
4. plugins/parsers/xml_parser_plugin.py ✅
```

### Fase 2: Análisis
5. plugins/analysis/dcma14_plugin.py
6. plugins/analysis/critical_path_plugin.py
7. plugins/analysis/evm_plugin.py

### Fase 3: Integración
8. Modificar core/engine.py
9. Crear ui/plugin_interface.py
10. Tests comprehensivos

¿Quieres el resto de los plugins ahora o paso a paso?