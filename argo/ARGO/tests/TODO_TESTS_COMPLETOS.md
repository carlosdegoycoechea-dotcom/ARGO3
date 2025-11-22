# TODO: Tests Completos - Recordatorio

⚠️ **IMPORTANTE**: Los tests actuales son BÁSICOS. Este documento enumera los tests COMPLETOS que faltan.

## Estado Actual

✅ **Completado** - Tests Básicos:
- Creación de instancias
- Validación de metadata
- Inicialización
- Health checks
- Registro de componentes
- Event bus básico
- Hook manager básico
- Integración básica (carga de plugins)

## Pendiente - Tests Completos

### 1. Tests con Archivos Reales

#### OCR Plugin
```python
# TODO: Test con imagen real
def test_ocr_extracts_text_from_sample_image():
    """Extract text from real test image"""
    # Crear tests/data/sample_text.png con texto conocido
    # Verificar que OCR extrae el texto correctamente
    pass

def test_ocr_handles_different_languages():
    """OCR with different languages"""
    # Probar español, inglés
    pass

def test_ocr_handles_poor_quality_images():
    """OCR with low quality images"""
    # Probar con imagen borrosa, bajo contraste
    pass
```

#### Excel Plugin
```python
# TODO: Test con Excel real
def test_excel_analyzes_schedule_file():
    """Analyze real schedule Excel file"""
    # Crear tests/data/sample_schedule.xlsx
    # Verificar detección de PMO metrics
    pass

def test_excel_handles_multiple_sheets():
    """Excel with multiple sheets"""
    pass

def test_excel_detects_formulas():
    """Excel formula detection"""
    # Requiere openpyxl avanzado
    pass
```

### 2. Tests de Plugins de Inteligencia

#### Corrective RAG
```python
# TODO: Test CRAG con RAG real
def test_crag_corrects_poor_retrieval():
    """CRAG corrects when retrieval quality is low"""
    # Mock RAG results con baja relevancia
    # Verificar que CRAG aplica correcciones
    pass

def test_crag_leaves_good_retrieval_unchanged():
    """CRAG doesn't modify good results"""
    pass
```

#### Self-Reflective RAG
```python
# TODO: Test Self-RAG con respuestas reales
def test_self_rag_detects_hallucinations():
    """Detect hallucinations in LLM responses"""
    # Respuesta con "I believe", "as far as I know"
    # Verificar detección
    pass

def test_self_rag_calculates_confidence():
    """Calculate confidence scores"""
    pass
```

#### Query Planning
```python
# TODO: Test descomposición con LLM real
def test_query_planning_decomposes_complex_query():
    """Decompose complex query with real LLM"""
    # Requiere model_router funcional
    pass

def test_query_planning_handles_simple_queries():
    """Don't decompose simple queries"""
    pass
```

#### Agentic Retrieval
```python
# TODO: Test agentes con queries reales
def test_agentic_selects_correct_agent():
    """Select appropriate agent for query type"""
    pass

def test_agentic_creates_appropriate_plan():
    """Create retrieval plan matching query complexity"""
    pass
```

### 3. Tests de Integración Completos

```python
# TODO: End-to-end pipeline
def test_full_rag_pipeline():
    """Complete RAG pipeline with all plugins"""
    # Query -> Planning -> Agentic Retrieval -> RAG -> CRAG -> LLM -> Self-Reflection
    pass

def test_plugins_communicate_via_events():
    """Plugins communicate through event system"""
    # Verificar que eventos se emiten y reciben correctamente
    pass

def test_hooks_chain_correctly():
    """Multiple hooks execute in correct order"""
    pass
```

### 4. Tests de Performance

```python
# TODO: Performance tests
@pytest.mark.slow
def test_plugin_loading_time():
    """Plugin loading completes in reasonable time"""
    # Medir tiempo < 1 segundo
    pass

@pytest.mark.slow
def test_analysis_performance():
    """Analysis completes in reasonable time"""
    # OCR, Excel con archivos grandes
    pass
```

### 5. Tests de Error Handling

```python
# TODO: Error scenarios
def test_plugin_fails_gracefully():
    """Plugin failure doesn't crash system"""
    pass

def test_missing_dependencies_handled():
    """Missing dependencies logged properly"""
    pass

def test_corrupted_file_handling():
    """Corrupted files handled gracefully"""
    pass
```

### 6. Tests de Configuración

```python
# TODO: Configuration tests
def test_plugin_custom_config():
    """Plugins accept custom configuration"""
    pass

def test_config_validation():
    """Invalid config rejected"""
    pass
```

### 7. Tests de Concurrencia

```python
# TODO: Concurrency tests
@pytest.mark.asyncio
async def test_concurrent_analysis():
    """Multiple analyses in parallel"""
    pass

@pytest.mark.asyncio
async def test_event_bus_async():
    """Async events work correctly"""
    pass
```

### 8. Tests de Cobertura

```bash
# TODO: Aumentar cobertura
# Objetivo: >80% code coverage
pytest tests/ --cov=core.plugins --cov=plugins --cov-report=html --cov-report=term

# Identificar líneas no cubiertas
# Agregar tests específicos para edge cases
```

## Archivos de Test Data Requeridos

Crear directorio `tests/data/` con:

```
tests/data/
├── images/
│   ├── sample_text.png          # Imagen con texto conocido
│   ├── spanish_text.png         # Texto en español
│   ├── poor_quality.png         # Imagen borrosa
│   └── no_text.png             # Imagen sin texto
├── excel/
│   ├── sample_schedule.xlsx     # Excel con schedule
│   ├── multi_sheet.xlsx        # Múltiples hojas
│   ├── formulas.xlsx           # Con fórmulas
│   ├── large_dataset.xlsx      # Dataset grande (>10k rows)
│   └── corrupted.xlsx          # Archivo corrupto
└── documents/
    ├── sample.pdf              # Para tests futuros
    └── sample.txt              # Documento simple
```

## Prioridad de Implementación

### Fase 1 (Alta Prioridad)
1. Tests con archivos reales (OCR, Excel)
2. Tests de error handling
3. Tests de integración end-to-end

### Fase 2 (Media Prioridad)
4. Tests de plugins de inteligencia con LLM real
5. Tests de configuración
6. Tests de performance básicos

### Fase 3 (Baja Prioridad)
7. Tests de concurrencia avanzados
8. Optimización de cobertura >80%
9. Tests de stress/carga

## Estimación

- **Tests Básicos Actuales**: ~40% de cobertura funcional
- **Tests Completos Objetivo**: >80% de cobertura
- **Tiempo Estimado**:
  - Fase 1: ~2-3 días
  - Fase 2: ~2 días
  - Fase 3: ~1-2 días
  - **Total**: ~5-7 días de desarrollo

## Notas

1. Algunos tests requieren dependencias opcionales instaladas (pytesseract, etc.)
2. Tests con LLM requieren model_router funcional y posiblemente API keys
3. Tests de performance deben ejecutarse en entorno similar a producción
4. Tests end-to-end pueden ser lentos - considerar marca `@pytest.mark.slow`

---

**Recordatorio**: NO olvidar implementar estos tests antes de producción.
Los tests básicos actuales son suficientes para desarrollo, pero NO para deployment.
