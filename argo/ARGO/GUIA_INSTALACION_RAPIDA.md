# 🚀 GUÍA DE INSTALACIÓN RÁPIDA - ARGO v10

## ✅ REQUISITOS PREVIOS

Antes de instalar, necesitas tener instalado:

- **Python 3.11+** - [Descargar](https://www.python.org/downloads/)
- **Node.js 18+** - [Descargar](https://nodejs.org/)
- **OpenAI API Key** - [Obtener](https://platform.openai.com/api-keys)

---

## 📦 INSTALACIÓN EN 3 PASOS

### PASO 1: Descargar ARGO

Descarga el archivo ZIP desde:
```
https://github.com/carlosdegoycoechea-dotcom/ARGO-v10/archive/refs/heads/claude/initial-setup-01LBBMg5Hz5CeVrQRjznjHD9.zip
```

Extrae en: `C:\Users\TU_USUARIO\ARGO\`

### PASO 2: Ejecutar Instalador

Doble clic en:
```
INSTALAR.bat
```

Espera 5-10 minutos mientras se instalan todas las dependencias.

### PASO 3: Configurar API Key

1. Abre el archivo `.env` con el Bloc de notas
2. Reemplaza `sk-tu-api-key-aqui` con tu OpenAI API key real
3. Guarda el archivo

---

## 🚀 INICIAR ARGO

Doble clic en:
```
INICIAR.bat
```

Se abrirán 2 ventanas (Backend y Frontend) y tu navegador en http://localhost:5173

---

## 🛑 DETENER ARGO

Doble clic en:
```
DETENER.bat
```

O simplemente cierra las ventanas de Backend y Frontend.

---

## 📁 ESTRUCTURA DE ARCHIVOS

```
C:\Users\TU_USUARIO\ARGO\
├── INSTALAR.bat          ← Ejecutar primero (solo una vez)
├── INICIAR.bat           ← Ejecutar para iniciar ARGO
├── DETENER.bat           ← Ejecutar para detener ARGO
├── .env                  ← Configurar tu API key aquí
├── backend/              ← Backend FastAPI
├── frontend/             ← Frontend React
├── core/                 ← Motor de ARGO
├── plugins/              ← 6 plugins instalados
└── data/                 ← Base de datos (se crea automáticamente)
```

---

## ⚠️ SOLUCIÓN DE PROBLEMAS

### "Python 3.11 no encontrado"
- Instala Python 3.11 desde: https://www.python.org/downloads/
- Durante la instalación, marca "Add Python to PATH"

### "Node.js no encontrado"
- Instala Node.js desde: https://nodejs.org/
- Usa la versión LTS (recomendada)

### "No se pudo inicializar ningún proveedor LLM"
- Verifica que tu OpenAI API key sea válida
- Edita el archivo `.env` y asegúrate de que la key empiece con `sk-`

### Error de puerto 8000 en uso
- Cierra cualquier aplicación que use el puerto 8000
- O edita `INICIAR.bat` y cambia `--port 8000` por `--port 8001`

---

## 🎯 PRIMER USO

1. Ejecuta `INICIAR.bat`
2. Espera a que se abra el navegador en http://localhost:5173
3. Verás el Dashboard de ARGO
4. Crea un nuevo proyecto
5. Sube documentos (PDF, DOCX, Excel)
6. Haz preguntas en el Chat

---

## 📊 VERIFICAR QUE FUNCIONA

### Backend:
- Ve a: http://localhost:8000/docs
- Deberías ver la documentación de la API (Swagger)

### Plugins Cargados:
En la ventana del Backend deberías ver:
```
✅ OCR plugin initialized successfully
✅ Excel analyzer plugin initialized successfully
✅ Corrective RAG plugin initialized successfully
✅ Self-Reflective RAG plugin initialized successfully
✅ Query Planning plugin initialized successfully
✅ Agentic Retrieval plugin initialized successfully
```

---

## 🔧 ARCHIVOS IMPORTANTES

### `.env` - Configuración de API Keys
```env
OPENAI_API_KEY=sk-tu-api-key-aqui
ANTHROPIC_API_KEY=sk-ant-tu-api-key-aqui
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### `config/settings.yaml` - Configuración del Sistema
- Configuración de modelos LLM
- Configuración de RAG (chunking, retrieval)
- Configuración de base de datos
- Configuración de plugins

---

## 📞 SOPORTE

Si encuentras problemas:

1. Verifica que Python 3.11 y Node.js estén instalados
2. Verifica que tu OpenAI API key sea válida
3. Revisa los logs en la ventana del Backend
4. Revisa el archivo `logs/argo.log`

---

## ✅ RESUMEN

**Instalación:**
1. Descargar ZIP
2. Ejecutar `INSTALAR.bat`
3. Editar `.env` con tu API key

**Uso Diario:**
1. Ejecutar `INICIAR.bat`
2. Usar ARGO en http://localhost:5173
3. Ejecutar `DETENER.bat` al terminar

**¡Listo!** 🎉
