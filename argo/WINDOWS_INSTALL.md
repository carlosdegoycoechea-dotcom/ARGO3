# ARGO v10 - Guía de Instalación para Windows

## Tu Problema Actual

Intentaste ejecutar `./scripts/start.sh` pero obtuviste:
- **Error 1:** `no se encontró Python` - Python no está instalado o no está en PATH
- **Error 2:** `npm: command not found` - Node.js no está instalado

## Prerrequisitos a Instalar

### 1. Python 3.11 o superior

**Descargar:**
- Ve a: https://www.python.org/downloads/
- Descarga Python 3.11 o 3.12 (versión más reciente)

**Instalación:**
1. Ejecuta el instalador
2. **MUY IMPORTANTE:** Marca la casilla **"Add Python to PATH"**
3. Click "Install Now"

**Verificar instalación:**
```powershell
python --version
# Debería mostrar: Python 3.11.x o 3.12.x
```

### 2. Node.js 18 o superior

**Descargar:**
- Ve a: https://nodejs.org/
- Descarga la versión **LTS** (Long Term Support)

**Instalación:**
1. Ejecuta el instalador
2. Acepta las opciones por defecto (automáticamente agrega npm al PATH)
3. Click "Next" y luego "Install"

**Verificar instalación:**
```powershell
node --version
# Debería mostrar: v18.x.x o superior

npm --version
# Debería mostrar: 9.x.x o superior
```

## Instalación de ARGO v10

Una vez instalados Python y Node.js:

### Opción A: Scripts Automáticos para Windows

Usa los scripts `.bat` que cree para Windows:

```powershell
# Abrir PowerShell o CMD en la carpeta ARGO
cd C:\Users\crdegoycoechea\ARGO

# Iniciar todo el sistema
.\scripts\start-windows.bat
```

### Opción B: Instalación Manual Paso a Paso

#### Paso 1: Configurar Backend

```powershell
# Ir a carpeta backend
cd ARGO\backend

# Crear archivo .env
copy .env.example .env

# Editar .env y agregar tu API key
notepad .env
```

Dentro de `.env`, agrega:
```
OPENAI_API_KEY=sk-tu-key-aqui
```

Guardar y cerrar.

#### Paso 2: Instalar Dependencias Backend

```powershell
# Crear entorno virtual Python
python -m venv venv

# Activar entorno virtual
venv\Scripts\activate

# Deberías ver (venv) al inicio de tu prompt

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Esto tomará unos minutos...
```

#### Paso 3: Configurar Frontend

```powershell
# Volver a raíz y ir a frontend
cd ..
cd frontend

# Crear archivo .env (opcional, usa valores por defecto)
copy .env.example .env

# Instalar dependencias npm
npm install

# Esto tomará varios minutos...
```

#### Paso 4: Iniciar ARGO

**Necesitas 2 ventanas de terminal:**

**Terminal 1 - Backend:**
```powershell
cd ARGO\backend
venv\Scripts\activate
python main.py
```

Deberías ver:
```
✓ ARGO Backend initialized
✓ Database ready
✓ RAG Engine ready
Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Frontend:**
```powershell
cd ARGO\frontend
npm run dev:client
```

Deberías ver:
```
VITE ready in XXX ms
➜  Local:   http://localhost:5000/
```

## Acceder a ARGO

Una vez iniciado:

- **Frontend:** http://localhost:5000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## Problemas Comunes en Windows

### Error: "Python no encontrado"
**Solución:**
- Reinstala Python marcando "Add Python to PATH"
- O agrega manualmente Python al PATH de Windows

### Error: "npm: command not found"
**Solución:**
- Instala Node.js desde https://nodejs.org/
- Reinicia tu terminal después de instalar

### Error: "venv\Scripts\activate no funciona"
**Solución:**
Si PowerShell bloquea scripts:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Luego intenta nuevamente:
```powershell
venv\Scripts\activate
```

### Error: "Port 8000 already in use"
**Solución:**
```powershell
# Encontrar proceso usando puerto 8000
netstat -ano | findstr :8000

# Matar proceso (reemplaza PID con el número que te dio el comando anterior)
taskkill /PID <numero> /F
```

### Error: "Port 5000 already in use"
**Solución:**
```powershell
# Encontrar proceso usando puerto 5000
netstat -ano | findstr :5000

# Matar proceso
taskkill /PID <numero> /F
```

## Detener ARGO

Para detener el sistema:
- En cada terminal, presiona `Ctrl + C`
- Cierra las ventanas de terminal

## Estructura del Proyecto

```
ARGO/
├── backend/              ← API FastAPI + Python
│   ├── main.py          ← Punto de entrada backend
│   ├── requirements.txt ← Dependencias Python
│   └── .env            ← Configuración (API keys)
│
├── frontend/            ← UI React + TypeScript
│   ├── package.json    ← Dependencias npm
│   ├── src/            ← Código fuente React
│   └── .env           ← Configuración frontend
│
├── core/               ← Motor ARGO (RAG, LLM, etc.)
│   ├── bootstrap.py
│   ├── rag_engine.py
│   └── model_router.py
│
├── scripts/            ← Scripts de inicio
│   ├── start.sh       ← Para Linux/Mac
│   └── start-windows.bat ← Para Windows (nuevo)
│
└── docs/
    └── DEPLOYMENT.md  ← Guía completa
```

## Verificación Final

Para verificar que todo funciona:

1. **Backend funciona:**
   ```powershell
   curl http://localhost:8000/health
   # O abre en navegador: http://localhost:8000/health
   # Debería responder: {"status":"ok"}
   ```

2. **Frontend funciona:**
   - Abre navegador en http://localhost:5000
   - Deberías ver la interfaz de ARGO

3. **WebSocket funciona:**
   - En la interfaz, intenta enviar un mensaje
   - Si funciona, verás respuesta del asistente

## Próximos Pasos

Una vez funcionando:
1. Sube documentos de proyecto
2. Configura tu proyecto en Settings
3. Empieza a hacer consultas al asistente

## Ayuda Adicional

Si sigues teniendo problemas:
1. Verifica que Python 3.11+ está instalado: `python --version`
2. Verifica que Node.js 18+ está instalado: `node --version`
3. Verifica que npm está disponible: `npm --version`
4. Asegúrate de tener tu OpenAI API key en `backend/.env`
