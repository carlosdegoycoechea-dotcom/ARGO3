# ARGO Plugin System Tests

Este directorio contiene **tests básicos** para el sistema de plugins de ARGO.

⚠️ **IMPORTANTE**: Estos son tests BÁSICOS. Tests completos y comprehensivos están pendientes.

## Estructura de Tests

```
tests/
├── conftest.py                      # Fixtures compartidos (mock_system, etc.)
├── test_plugin_system.py            # Tests para PluginManager, EventBus, HookManager
├── test_analysis_plugins.py         # Tests para plugins de análisis (OCR, Excel)
├── test_intelligence_plugins.py     # Tests para 4 bloques de inteligencia (CRAG, etc.)
├── test_integration.py              # Tests de integración básica
└── README.md                        # Este archivo
```

## Ejecutar Tests

### Instalar dependencias de desarrollo

```bash
# Opción 1: Instalar desde requirements-dev.txt (recomendado)
pip install -r requirements-dev.txt

# Opción 2: Instalar manualmente
pip install pytest pytest-asyncio pytest-cov
```

### Ejecutar todos los tests

```bash
# Desde el directorio ARGO/
pytest tests/ -v
```

### Ejecutar tests específicos

```bash
# Solo tests unitarios
pytest tests/ -v -m unit

# Solo tests de integración
pytest tests/ -v -m integration

# Solo un archivo
pytest tests/test_plugin_system.py -v

# Solo una clase de tests
pytest tests/test_plugin_system.py::TestPluginManager -v

# Solo un test específico
pytest tests/test_plugin_system.py::TestPluginManager::test_plugin_manager_creation -v
```

### Ejecutar con cobertura

```bash
pip install pytest-cov
pytest tests/ --cov=core.plugins --cov=plugins --cov-report=html
```

## Tipos de Tests

### 1. Tests Unitarios (`pytest.mark.unit`)
- Prueban componentes individuales en aislamiento
- No requieren dependencias externas
- Rápidos de ejecutar

### 2. Tests de Integración (`pytest.mark.integration`)
- Prueban múltiples componentes juntos
- Verifican que plugins se cargan correctamente
- Pueden requerir dependencias opcionales

## Plugins Testeados

### Plugins de Análisis
1. **OCR Plugin** (`ocr_plugin.py`)
   - Extracción de texto de imágenes
   - Requiere: pytesseract, Pillow

2. **Excel Plugin** (`excel_plugin.py`)
   - Análisis de hojas de cálculo
   - Requiere: pandas, openpyxl, numpy

### Plugins de Inteligencia (4 Bloques RAG Avanzados)
3. **Corrective RAG** (`corrective_rag_plugin.py`)
   - Verifica y corrige calidad de retrieval

4. **Self-Reflective RAG** (`self_reflective_rag_plugin.py`)
   - Evalúa calidad de respuestas
   - Detecta alucinaciones

5. **Query Planning** (`query_planning_plugin.py`)
   - Descompone queries complejos

6. **Agentic Retrieval** (`agentic_retrieval_plugin.py`)
   - Sistema multi-agente de retrieval

## Cobertura de Tests

### ✅ Implementado (Tests Básicos)
- Creación de instancias
- Validación de metadata
- Inicialización de plugins
- Health checks
- Registro de plugins
- Event bus (emit, handlers)
- Hook manager (registro, ejecución)
- Integración básica

### ❌ Pendiente (Tests Completos - TODO)
- Análisis de archivos reales
- Tests end-to-end completos
- Llamadas LLM reales
- Performance tests
- Tests de concurrencia
- Tests de error handling exhaustivos
- Tests con diferentes configuraciones
- Cobertura > 80%

## Fixtures Disponibles

### `mock_system`
Mock del sistema ARGO con:
- `config`: Configuración mock
- `active_project`: Proyecto de prueba
- `model_router`: Router mock
- `plugins`: PluginManager

### `mock_config`
Configuración mock con métodos `get()` y `set()`

## Dependencias de Tests

### Requeridas
```
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

### Opcionales (para tests completos)
```
pytesseract  # Para OCR tests
Pillow       # Para OCR tests
pandas       # Para Excel tests
openpyxl     # Para Excel tests
numpy        # Para Excel tests
```

## Notas Importantes

1. **Tests básicos vs completos**: Los tests actuales son BÁSICOS - verifican que el código no crashea y que la estructura es correcta. NO son tests comprehensivos.

2. **Dependencias opcionales**: Algunos plugins requieren dependencias opcionales (OCR, Excel). Los tests están diseñados para NO fallar si estas dependencias no están instaladas.

3. **Mock objects**: Los tests usan mocks para aislar componentes. Tests completos deberían usar el sistema real.

4. **Cobertura**: Actualmente cubrimos ~40% de funcionalidad básica. Target para tests completos: >80%.

## TODO: Tests Completos

Cuando implementemos tests completos, agregar:

```python
# Tests con archivos reales
def test_ocr_extracts_text_from_real_image():
    # Usar imagen de prueba real
    result = analyzer.analyze('tests/data/sample.png')
    assert 'text' in result.data
    assert len(result.data['text']) > 0

# Tests end-to-end
def test_full_rag_pipeline_with_plugins():
    # Query -> Planning -> Retrieval -> CRAG -> LLM -> Self-Reflection
    pass

# Tests de performance
@pytest.mark.slow
def test_plugin_loading_performance():
    # Medir tiempo de carga
    pass
```

## Contribuir Tests

Al agregar nuevos plugins, crear tests básicos:

```python
class TestMyNewPlugin:
    def test_creation(self):
        plugin = MyNewPlugin()
        assert plugin is not None

    def test_metadata(self):
        plugin = MyNewPlugin()
        assert plugin.metadata.name == 'my_plugin'

    def test_initialization(self, mock_system):
        plugin = MyNewPlugin()
        plugin.initialize(mock_system)
        assert plugin.system == mock_system

    def test_health_check(self):
        plugin = MyNewPlugin()
        health = plugin.health_check()
        assert isinstance(health, bool)
```

---

**Recuerda**: Estos son tests BÁSICOS. Los tests COMPLETOS están pendientes y deben implementarse antes de producción.
