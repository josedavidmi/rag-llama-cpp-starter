import json
import os
from pathlib import Path
from typing import List

import chromadb
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_FILE = Path(os.getenv("DOCS_FILE", BASE_DIR / "docs" / "Documento_base.txt"))
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", BASE_DIR / "data" / "chroma"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "knowledge-base")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:8080/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Llama-3.2-3B-Instruct-Q4_K_M.gguf")
TOP_K = int(os.getenv("TOP_K", "2"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "Eres un asistente útil. Responde solo con información apoyada en el contexto recuperado. "
    "Si el contexto no contiene la respuesta, dilo claramente. Sé breve y claro.",
)

app = FastAPI(title="RAG con llama.cpp", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")

chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = chroma_client.get_or_create_collection(COLLECTION_NAME)
llm_client = AsyncOpenAI(base_url=LLM_BASE_URL, api_key="local")


class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []


class ChatResponse(BaseModel):
    answer: str
    context: List[str]


def read_Documento_base() -> List[str]:
    if not DOCS_FILE.exists():
        raise FileNotFoundError(f"No existe el fichero de conocimiento: {DOCS_FILE}")

    text = DOCS_FILE.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("La base de conocimiento está vacía")

    chunks = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]
    return chunks


def seed_collection(force: bool = False) -> int:
    chunks = read_Documento_base()

    if force:
        current = collection.get()
        if current and current.get("ids"):
            collection.delete(ids=current["ids"])

    current_count = collection.count()
    if current_count == len(chunks) and current_count > 0:
        return current_count

    if current_count > 0:
        current = collection.get()
        if current and current.get("ids"):
            collection.delete(ids=current["ids"])

    ids = [f"doc-{i+1}" for i in range(len(chunks))]
    collection.add(ids=ids, documents=chunks)
    return len(chunks)


@app.on_event("startup")
async def startup_event() -> None:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    seeded = seed_collection(force=False)
    print(f"Colección '{COLLECTION_NAME}' lista con {seeded} fragmentos")
    print(f"LLM endpoint: {LLM_BASE_URL}")
    print(f"Modelo: {MODEL_NAME}")


@app.get("/")
async def root():
    return RedirectResponse("/static/index.html")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "llm_base_url": LLM_BASE_URL,
        "collection": COLLECTION_NAME,
        "documents": collection.count(),
    }


@app.post("/reload")
async def reload_Documento_base():
    seeded = seed_collection(force=True)
    return {"status": "reloaded", "documents": seeded}


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")

    try:
        results = collection.query(query_texts=[message], n_results=TOP_K)
        context_docs = results["documents"][0] if results.get("documents") else []
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error consultando Chroma: {exc}") from exc

    system_message = {
        "role": "system",
        "content": (
            f"{SYSTEM_PROMPT}\n\n"
            f"Contexto recuperado:\n{json.dumps(context_docs, ensure_ascii=False, indent=2)}"
        ),
    }

    messages = [system_message] + payload.history + [{"role": "user", "content": message}]

    try:
        response = await llm_client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=TEMPERATURE,
            stream=False,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error llamando al LLM: {exc}") from exc

    answer = response.choices[0].message.content if response.choices else "Sin respuesta"
    return ChatResponse(answer=answer or "Sin respuesta", context=context_docs)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
