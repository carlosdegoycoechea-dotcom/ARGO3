# ⚠️ PENDIENTES SEGÚN AUDITORÍAS - ARGO v10

**Fecha:** 2025-11-22
**Basado en:** 3 Auditorías (ChatGPT + 2 Claude)

---

## 📊 ESTADO ACTUAL

### ✅ LO QUE YA ESTÁ (Completado)

#### Fase 2: Sistema Plug & Play ✅
- ✅ **Core Plugin System** (PluginManager, EventBus, HookManager)
- ✅ **BaseAnalyzer abstract** (patrón común para analizadores)
- ✅ **Plugin discovery automático**
- ✅ **Event-driven architecture**
- ✅ **Hook system** (18 puntos de extensión)
- ✅ **2 Plugins de análisis** (OCR, Excel)
- ✅ **4 Bloques de inteligencia** (CRAG, Self-RAG, Query Planning, Agentic)
- ✅ **Tests básicos** (53+ tests)
- ✅ **Bootstrap integration** (Phase 7.5)

#### Core Técnico ✅
- ✅ **Bootstrap unificado** (95/100)
- ✅ **RAG moderno** (HyDE + Cache + Reranking) (80/100)
- ✅ **Model Router** (85/100)
- ✅ **Database SQLite** (80/100)
- ✅ **Frontend React** con Dashboard

---

## ❌ LO QUE FALTA (Pendiente)

### FASE 1: FUNCIONALIDADES PMO PERDIDAS

Según las auditorías, se **perdieron 16/19 funcionalidades** (84%) en la transición v9 → v10.

#### 1.1 Análisis de Cronogramas (CRÍTICO)

**Archivos que NO existen:**
```
❌ ARGO/core/tools/parsers/xer_parser.py
❌ ARGO/core/tools/parsers/mpp_parser.py
❌ ARGO/core/tools/analyzers/schedule_analyzer.py
❌ ARGO/core/tools/analyzers/critical_path.py
```

**Funcionalidades faltantes:**
- ❌ Parser de **Primavera P6 XER** files
- ❌ Parser de **MS Project MPP** files
- ❌ **Critical Path calculation** (CPM algorithm)
- ❌ **Float analysis** (Total Float, Free Float)
- ❌ **Schedule metrics** (SPI, CPI)
- ❌ **Resource loading analysis**
- ❌ **Baseline comparison**

**Dependencias faltantes en requirements.txt:**
```python
❌ PyP6XER          # Para parsing Primavera P6
❌ python-mpxj      # Para parsing MS Project
❌ networkx         # Para critical path analysis
❌ matplotlib       # Para visualizaciones
```

#### 1.2 Evaluaciones de Calidad (CRÍTICO)

**Archivos que NO existen:**
```
❌ ARGO/core/tools/evaluators/dcma_evaluator.py
❌ ARGO/core/tools/evaluators/gao_evaluator.py
```

**Funcionalidades faltantes:**
- ❌ **DCMA 14-Point Assessment Guide**
  - Logic (SS/FF < 5%)
  - Leads (< 5%)
  - Lags (< 5%)
  - Relationship Types
  - Hard Constraints
  - High Float (>44 days)
  - Negative Float
  - High Duration (>44 days)
  - Invalid Dates
  - Resources
  - Missed Tasks
  - Critical Path Test
  - Critical Path Length Index
  - Baseline

- ❌ **GAO Schedule Assessment Guide**
  - 10 best practices
  - Schedule quality metrics

#### 1.3 Database Schema para PMO

**Tablas que NO existen:**
```sql
❌ schedule_files
❌ activities
❌ relationships
❌ resources
❌ dcma_assessments
❌ gao_assessments
❌ baselines
```

#### 1.4 Backend Endpoints

**Endpoints que NO existen:**
```python
❌ POST   /api/schedule/upload
❌ GET    /api/schedule/{id}/analysis
❌ GET    /api/schedule/{id}/critical-path
❌ GET    /api/schedule/{id}/float
❌ GET    /api/schedule/{id}/dcma
❌ GET    /api/schedule/{id}/gao
❌ POST   /api/schedule/{id}/baseline
```

#### 1.5 Otras Funcionalidades

**ChatGPT identificó:**
- ❌ **Document indexing real** (backend/main.py tiene `# TODO: Index chunks in vectorstore`)
- ❌ **Web search integration** (Tavily, búsqueda externa)
- ❌ **Watchers / Monitoring** (carpeta `monitoring/` no existe)
- ❌ **Notes/Minutas persistence** (NotesPanel.tsx usa MOCK_NOTES)
- ❌ **Feedback system** (Thumbs up/down sin backend)
- ❌ **Multi-project UI** (solo un proyecto activo)

**Claude identificó:**
- ❌ **Metadata-aware retrieval** (filtros por tipo de documento)
- ❌ **Custom scorers hook** para RAG
- ❌ **Query planning** (descomposición de queries complejos) - ⚠️ PARCIAL (implementado como plugin)

---

## 🎯 PRIORIDADES DE IMPLEMENTACIÓN

### DECISIÓN ESTRATÉGICA TOMADA

**Usuario decidió:** Implementar **Fase 2 PRIMERO** (plug & play), luego Fase 1 (PMO)

**Razón:** PMO debe ser un **plugin**, no parte del core.

### Estado de Implementación

```
✅ Fase 2 (Plug & Play)   - COMPLETADA
⏳ Fase 1 (PMO Plugins)   - PENDIENTE
⏳ Tests Completos        - PENDIENTE
⏳ Fase 3 (Optimización)  - PENDIENTE
```

---

## 📋 PRÓXIMOS PASOS RECOMENDADOS

### Opción A: Implementar PMO como Plugins

Crear plugins siguiendo el patrón ya establecido:

```
ARGO/plugins/
├── schedule_analyzer_plugin.py     # Parser XER/MPP + CPM
├── dcma_plugin.py                  # DCMA 14-Point
├── gao_plugin.py                   # GAO Assessment
├── float_analyzer_plugin.py        # Float Analysis
└── baseline_comparator_plugin.py   # Baseline Comparison
```

**Ventajas:**
- ✅ Usa arquitectura plug & play ya implementada
- ✅ No modifica el core
- ✅ Fácil de habilitar/deshabilitar
- ✅ Tests aislados

**Duración estimada:** 2-3 semanas

### Opción B: Completar Tests del Sistema de Plugins

Implementar los tests completos pendientes (ver `TODO_TESTS_COMPLETOS.md`):

- Tests con archivos reales (OCR, Excel)
- Tests end-to-end del pipeline RAG
- Tests de performance
- Cobertura >80%

**Duración estimada:** 5-7 días

### Opción C: Funcionalidades Menores

Implementar funcionalidades más simples identificadas por ChatGPT:

- Document indexing real (completar TODO en backend)
- Notes persistence (API + Database)
- Feedback system (API endpoints)
- Web search integration (Tavily plugin)

**Duración estimada:** 1-2 semanas

---

## 📊 RESUMEN DE IMPACTO

| Componente | Estado | Impacto |
|-----------|--------|---------|
| **Plugin System** | ✅ COMPLETO | ALTO - Base para todo |
| **PMO Analyzers** | ❌ AUSENTE | CRÍTICO - Funcionalidad core |
| **DCMA/GAO** | ❌ AUSENTE | ALTO - Diferenciador clave |
| **Tests Completos** | ⚠️ BÁSICO | ALTO - Calidad/Producción |
| **Document Indexing** | ❌ TODO | MEDIO - UX |
| **Web Search** | ❌ AUSENTE | MEDIO - Capacidad |
| **Notes/Feedback** | ❌ MOCK | BAJO - UX |

---

## 💡 RECOMENDACIÓN

**Prioridad 1:** Implementar **PMO Plugins** (Schedule, DCMA, GAO)
- Es la funcionalidad más crítica según auditorías
- 84% de funcionalidad perdida está aquí
- Ya tenemos la arquitectura plug & play lista

**Prioridad 2:** **Tests Completos**
- Necesario antes de producción
- Validar que plugins funcionan correctamente

**Prioridad 3:** **Funcionalidades menores**
- Document indexing, Notes, Feedback
- Mejoras UX y capacidad

---

## 🔍 ANÁLISIS DE DEPENDENCIAS

### Sin Conflictos ✅

Las auditorías confirmaron:
- ✅ **requirements.txt actual sin conflictos**
- ✅ Todas las versiones son compatibles
- ✅ Numpy 1.26.4 (podría actualizar a 2.x, no crítico)

### A Agregar para PMO

```python
# requirements-pmo.txt
PyP6XER>=1.0.0          # Primavera P6 parsing
python-mpxj>=1.0.0      # MS Project parsing
networkx>=3.0           # Graph algorithms (CPM)
matplotlib>=3.7.0       # Visualizations
seaborn>=0.12.0         # Advanced charts
```

**Total nuevas dependencias:** 5
**Riesgo de conflictos:** BAJO

---

## ✅ CONCLUSIÓN

### Lo que YA funciona (Fase 2):
- ✅ Sistema de plugins completo y testeado
- ✅ 6 plugins funcionando (OCR, Excel, 4 bloques inteligencia)
- ✅ Arquitectura extensible lista para PMO

### Lo que FALTA (Fase 1):
- ❌ Parsers de schedule (XER, MPP)
- ❌ Análisis PMO (Critical Path, Float, DCMA, GAO)
- ❌ Database schema para schedules
- ❌ Backend endpoints para PMO
- ⚠️ Tests completos

### Siguiente paso sugerido:
**Implementar PMO como plugins** usando la arquitectura ya creada.

¿Quieres que empiece con los plugins de PMO (Schedule Analyzer, DCMA, GAO)?
