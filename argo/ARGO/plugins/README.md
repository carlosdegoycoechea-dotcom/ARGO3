# ARGO Plugins Directory

This directory contains plug & play plugins for ARGO.

## 📦 Installed Plugins

### Analysis Plugins

#### 1. OCR Plugin (`ocr_plugin.py`)
**Capability:** Text extraction from images

**Supported Formats:** `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.bmp`, `.gif`

**Dependencies:**
```bash
pip install pytesseract Pillow
```

Plus Tesseract OCR system binary:
- **Ubuntu/Debian:** `sudo apt-get install tesseract-ocr`
- **macOS:** `brew install tesseract`
- **Windows:** https://github.com/UB-Mannheim/tesseract/wiki

**Features:**
- Auto-OCR when image uploaded
- Multi-language support
- Confidence scoring
- Statistics (words, lines, characters)

**Events Emitted:**
- `ocr_completed` - When OCR finishes

**Hooks:**
- `post_extraction` - Enhances text extraction with OCR

---

#### 2. Excel Analyzer Plugin (`excel_plugin.py`)
**Capability:** Advanced Excel/CSV analysis

**Supported Formats:** `.xlsx`, `.xls`, `.xlsm`, `.csv`

**Dependencies:** Already in requirements.txt ✅
```bash
pandas>=2.2.3
openpyxl>=3.1.5
numpy>=1.26.4
```

**Features:**
- Auto header detection
- Data type analysis
- Summary statistics
- PMO metrics detection (schedules, activities, durations)
- Empty cell counting

**Events Emitted:**
- `excel_analyzed` - When analysis completes

---

### Intelligence Plugins (Advanced RAG)

#### 3. Corrective RAG Plugin (`corrective_rag_plugin.py`)
**Capability:** Verifies and corrects retrieval quality

**Dependencies:** None (uses existing langchain) ✅

**Features:**
- Relevance verification of retrieved documents
- Low-quality detection
- Web search fallback (when enabled)
- Adaptive retrieval strategy

**Hooks:**
- `POST_RAG_SEARCH` - Evaluates results after RAG search

**Configuration:**
```yaml
corrective_rag:
  relevance_threshold: 0.6
  use_web_search: false
```

---

#### 4. Self-Reflective RAG Plugin (`self_reflective_rag_plugin.py`)
**Capability:** Evaluates response quality and detects hallucinations

**Dependencies:** None (uses existing langchain) ✅

**Features:**
- Self-evaluation of responses (relevance, support, consistency)
- Hallucination detection
- Confidence scoring
- Automatic regeneration triggers

**Hooks:**
- `POST_LLM_CALL` - Evaluates after LLM generates response

**Configuration:**
```yaml
self_reflective_rag:
  quality_threshold: 0.6
  check_hallucinations: true
```

---

#### 5. Query Planning Plugin (`query_planning_plugin.py`)
**Capability:** Decomposes complex queries into sub-queries

**Dependencies:** None (uses existing langchain) ✅

**Features:**
- Complexity measurement
- Query decomposition
- Execution planning
- Sequential sub-query handling

**Hooks:**
- `PRE_QUERY_PROCESSING` - Plans before query execution

**Configuration:**
```yaml
query_planning:
  complexity_threshold: 15  # words
  max_subqueries: 5
```

---

#### 6. Agentic Retrieval Plugin (`agentic_retrieval_plugin.py`)
**Capability:** Intelligent multi-agent retrieval

**Dependencies:** None (uses existing langchain) ✅

**Features:**
- Multiple specialized agents (Factual, Analytical, Comparison, Exploratory)
- Dynamic agent selection
- Query type classification
- Adaptive retrieval strategies

**Hooks:**
- `PRE_RAG_SEARCH` - Plans retrieval before search

**Agents:**
- `FactualAgent` - Simple fact lookup
- `AnalyticalAgent` - In-depth analysis
- `ComparisonAgent` - Comparing items
- `ExploratoryAgent` - Open-ended research

---

## 🚀 How to Create a New Plugin

### 1. Create Plugin File

```python
# plugins/my_analyzer_plugin.py

from core.plugins import (
    Plugin,
    BaseAnalyzer,
    AnalysisResult,
    PluginMetadata,
    PluginCapability
)

class MyAnalyzer(BaseAnalyzer):
    @property
    def name(self) -> str:
        return "my_analyzer"

    @property
    def supported_formats(self) -> List[str]:
        return ['.myformat']

    def analyze(self, file_path: str, options=None) -> AnalysisResult:
        # Your analysis logic here
        return AnalysisResult(
            status='success',
            data={'result': 'analyzed!'},
            metadata={'analyzer': self.name}
        )

class MyAnalyzerPlugin(Plugin):
    def __init__(self):
        self.metadata = PluginMetadata(
            name="my_analyzer",
            version="1.0.0",
            description="My custom analyzer",
            capabilities=[PluginCapability.ANALYZER],
            enabled=True
        )

    def initialize(self, system):
        analyzer = MyAnalyzer()
        system.plugins.register_analyzer(analyzer)

    def shutdown(self):
        pass

    def health_check(self) -> bool:
        return True
```

### 2. Plugin is Auto-Discovered

The PluginManager automatically loads all `*_plugin.py` files from this directory.

### 3. Use Events and Hooks

```python
# Register event handler
system.plugins.events.on('document_uploaded', my_handler)

# Register hook
system.plugins.hooks.register(
    HookPoint.POST_ANALYSIS,
    my_hook_function,
    priority=10
)
```

---

## 📋 Plugin Development Checklist

- [ ] Implement required abstract methods
- [ ] Add proper error handling
- [ ] Include health_check() method
- [ ] Document supported formats/capabilities
- [ ] List dependencies clearly
- [ ] Add configuration options
- [ ] Register appropriate events/hooks
- [ ] Write unit tests

---

## 🔧 Configuration

Plugins can be configured in `core/config/settings.yaml`:

```yaml
# Plugin-specific settings
ocr:
  language: eng
  psm: 3

excel:
  pmo_mode: true

corrective_rag:
  relevance_threshold: 0.6
  use_web_search: false

# ... etc
```

---

## ✅ Dependencies Status

| Plugin | Dependencies | Status |
|--------|--------------|--------|
| OCR | pytesseract, Pillow | ⚠️ Optional |
| Excel | pandas, openpyxl, numpy | ✅ In requirements.txt |
| Corrective RAG | - | ✅ Uses existing |
| Self-Reflective RAG | - | ✅ Uses existing |
| Query Planning | - | ✅ Uses existing |
| Agentic Retrieval | - | ✅ Uses existing |

**No dependency conflicts!** ✅

---

## 📊 Architecture Benefits

✅ **Modular** - Add features without touching core
✅ **Testable** - Test plugins independently
✅ **Maintainable** - Clear separation of concerns
✅ **Extensible** - Easy to add new capabilities
✅ **Event-driven** - Loose coupling via events
✅ **Configurable** - YAML-based configuration

---

**Next Steps:**
- Add PMO schedule analyzer plugin
- Add DCMA evaluator plugin
- Add more intelligence plugins
- Create plugin marketplace
