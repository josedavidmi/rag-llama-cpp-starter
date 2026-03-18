# Chatbot RAG con `llama.cpp` + FastAPI + Chroma

Este repositorio deja montado un ejemplo completo de chatbot con RAG pensado para despliegue sencillo en Windows y Linux.

## Qué incluye

- `llama.cpp` como servidor del modelo local en Docker.
- Una app FastAPI que:
  - carga una base de conocimiento desde `docs/Documento_base.txt`
  - indexa los fragmentos en Chroma
  - recupera los fragmentos más relevantes
  - construye un prompt contextualizado
  - llama al modelo vía API OpenAI-compatible
- Una interfaz web mínima en `http://localhost:8000`
- `docker-compose.yml` para levantar todo con un solo comando
- Scripts de arranque para Windows y Linux

---

## Estructura del proyecto

```text
rag-llama-cpp-starter/
├── app/
│   ├── main.py
│   └── static/
│       ├── app.js
│       ├── index.html
│       └── styles.css
├── data/
│   └── chroma/
├── docs/
│   └── Documento_base.txt
├── models/
│   └── (aquí va tu modelo .gguf)
├── scripts/
│   ├── start-linux.sh
│   ├── start-windows.ps1
│   ├── test-model-linux.sh
│   └── test-model-windows.ps1
├── .env.example
├── .gitignore
├── Dockerfile.app
├── docker-compose.yml
├── README.md
└── requirements.txt
```

---

## Requisitos

### En cualquier sistema
- Docker y Docker Compose
- Un modelo GGUF dentro de la carpeta `models/`

### Probado especialmente para
- Windows con Docker Desktop
- Linux con Docker Engine o Docker Desktop

---

## Modelo recomendado

Ejemplo de nombre de fichero:

```text
Llama-3.2-3B-Instruct-Q4_K_M.gguf
```

Coloca ese fichero dentro de:

```text
models/
```

De modo que quede así:

```text
models/Llama-3.2-3B-Instruct-Q4_K_M.gguf
```

> Importante: el modelo **no** se sube normalmente al repositorio GitHub. Por eso `models/*.gguf` está incluido en `.gitignore`.

---

## Arranque rápido con Docker Compose

### 1. Clonar el repositorio

```bash
git clone <TU-REPO>
cd rag-llama-cpp-starter
```

### 2. Crear el archivo `.env`

#### Linux
```bash
cp .env.example .env
```

#### Windows PowerShell
```powershell
Copy-Item .env.example .env
```

### 3. Revisar `.env`

Contenido por defecto: 
Parametrizamos los valores para lanzar nuestro sistema dockerizado. Especificando que modelo queremos lanzar, con que memoria RAM queremos ejecutar dicho modelo, cuales es el nº de fragmentos a recuperar de Chroma más importantes, con que temperatura queremos que funcione el modelo y por último que imagen de llama.cpp queremos levantar como contenedor. 

```env
MODEL_FILE=Llama-3.2-3B-Instruct-Q4_K_M.gguf
CTX_SIZE=4096
TOP_K=2
TEMPERATURE=0.3
LLAMA_IMAGE=ghcr.io/ggml-org/llama.cpp:server
```

Asegúrate de que `MODEL_FILE` coincide exactamente con el nombre del archivo que hayas copiado a `models/`.

### 4. Levantar el proyecto

#### Linux
```bash
./scripts/start-linux.sh
```

#### Windows PowerShell
```powershell
./scripts/start-windows.ps1
```

También puedes hacerlo manualmente:

```bash
docker compose up --build
```

---

## URLs del sistema

Una vez arrancado:

- App RAG: `http://localhost:8000`
- Servidor del modelo: `http://localhost:8080`
- Estado de la app: `http://localhost:8000/health`

---

## Cómo funciona el RAG en este ejemplo

1. La app lee `docs/Documento_base.txt`
2. Divide el contenido por bloques separados por líneas en blanco
3. Guarda esos bloques en Chroma
4. Cuando el usuario pregunta algo:
   - se recuperan los `TOP_K` fragmentos más relevantes
   - se construye un prompt con ese contexto
   - se llama al modelo servido por `llama.cpp`
5. La respuesta vuelve a la interfaz web

---

## Cómo editar la base de conocimiento

Edita este fichero:

```text
docs/Documento_base.txt
```

Regla simple de este ejemplo:
- cada bloque separado por una línea en blanco se considera un fragmento distinto

Ejemplo:

```text
Lostsys ofrece servicios y productos para informática corporativa.

Lostsys desarrolla aplicaciones y tiendas online.

Lostsys imparte formación en IA, Data y DevOps.
```

Después de modificarlo, recarga la base de conocimiento con:

```bash
curl -X POST http://localhost:8000/reload
```

En PowerShell:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/reload" -Method Post
```

---

## Comprobaciones útiles

### Ver si el modelo responde

#### Linux
```bash
./scripts/test-model-linux.sh
```

#### Windows PowerShell
```powershell
./scripts/test-model-windows.ps1
```

### Ver contenedores activos

```bash
docker ps
```

### Ver logs

```bash
docker compose logs -f
```

### Parar el sistema

```bash
docker compose down
```

---

## Personalización

### Variables importantes

- `MODEL_FILE`: nombre del modelo `.gguf`
- `CTX_SIZE`: contexto del servidor `llama.cpp`
- `TOP_K`: número de fragmentos recuperados por Chroma
- `TEMPERATURE`: creatividad del modelo

### Cambiar el prompt del sistema

Puedes cambiarlo desde la variable `SYSTEM_PROMPT` en `docker-compose.yml` o directamente dentro de `app/main.py`.

---

## Ejecución sin Docker para la app

Si quieres usar Docker solo para `llama.cpp` y arrancar la app Python localmente:

### 1. Crear entorno virtual

#### Linux
```bash
python -m venv .venv
source .venv/bin/activate
```

#### Windows PowerShell
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Lanzar la app

```bash
python -m app.main
```

En este caso el modelo debe seguir disponible en:

```text
http://127.0.0.1:8080/v1
```

---

## Problemas frecuentes

### 1. El modelo no carga
Revisa:
- que el fichero `.gguf` exista en `models/`
- que `MODEL_FILE` coincida exactamente con el nombre real
- que el contenedor `llama-server` esté activo

### 2. La app arranca pero no responde
Revisa:
- que `docker ps` muestre `llama-server` y `rag-app`
- que `http://localhost:8080/v1/models` responda
- que `http://localhost:8000/health` devuelva `status: ok`

### 3. Respuestas pobres o poco precisas
Prueba a:
- mejorar `docs/Documento_base.txt`
- aumentar `TOP_K`
- dividir mejor los fragmentos
- ajustar el prompt del sistema

### 4. Windows PowerShell da errores con `curl`
Usa `Invoke-RestMethod` en lugar de `curl` si el alias de PowerShell te da problemas.

---

## Flujo recomendado para clase

1. Levantar el sistema con Docker Compose
2. Probar que el modelo responde
3. Editar `Documento_base.txt`
4. Recargar la base de conocimiento
5. Hacer preguntas en la web
6. Explicar que el RAG:
   - busca contexto
   - construye un prompt mejor
   - llama al LLM

---

## Siguientes mejoras posibles

- carga de PDFs
- chunking más avanzado
- reranking
- historial de conversación persistente
- streaming de tokens
- autenticación
- despliegue en servidor remoto

---

## Licencia y modelos

El código del repositorio puede publicarse sin incluir los pesos del modelo.
Asegúrate de respetar la licencia del modelo GGUF que utilices.
