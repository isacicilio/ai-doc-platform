# AI Document Intelligence Platform — Plano e Arquitetura

> Sistema RAG (Retrieval-Augmented Generation) para fazer perguntas sobre documentos.
> Versão local, gratuita e fácil de testar — preparada para escalar depois.

---

## 1. Visão geral

O sistema faz duas coisas:

1. **Ingestão** — você envia um documento (PDF, DOCX...). Ele é lido, quebrado em pedaços (*chunks*), transformado em vetores (*embeddings*) e guardado num banco vetorial.
2. **Pergunta e resposta** — você faz uma pergunta. O sistema busca os trechos mais relevantes do documento (busca semântica), monta um contexto e pede pro LLM gerar a resposta baseada **só** naquele contexto.

Isso é o padrão RAG: o LLM não "decora" o documento, ele consulta na hora. Resultado: respostas baseadas no documento real, com menos alucinação.

---

## 2. Stack escolhida (grátis + local)

| Camada | Tecnologia | Por quê |
|---|---|---|
| **LLM** | Ollama + Llama 3.1 8B (ou Qwen2.5 7B) | Grátis, local, sem API key. 1 comando pra instalar. |
| **Embeddings** | sentence-transformers (`all-MiniLM-L6-v2`) | Grátis, local, rápido, leve (384 dimensões). |
| **Banco vetorial** | PostgreSQL + pgvector | Igual ao diagrama. Guarda vetores + metadados juntos. |
| **Backend / API** | FastAPI (Python) | Rápido, moderno, ótimo pra IA. |
| **Frontend** | React (fase posterior) | Interface de chat. |
| **Extração de texto** | PyMuPDF (PDF), python-docx (DOCX) | Leitura confiável de documentos. |
| **Infra (depois)** | Docker, GitHub Actions, AWS | Containerização e deploy. |

### Princípio-chave: abstração de provedor

O código nunca chama o Ollama diretamente. Ele chama uma interface (`LLMProvider`, `EmbeddingProvider`). Trocar pra **Claude** ou **OpenAI** vira só mudar o `.env`:

```
LLM_PROVIDER=ollama        # ollama | claude | openai
EMBEDDING_PROVIDER=local   # local | openai
```

Assim você desenvolve de graça agora e pluga um modelo pago depois sem reescrever a lógica.

> **Máquina fraca?** Alternativa sem rodar modelo local: usar o *free tier* da API do Google Gemini ou da Groq pro LLM. Continua sem custo, só não é 100% offline.

---

## 3. Arquitetura — mapeada ao diagrama

```
┌─────────┐   ┌──────────┐   ┌─────────────┐
│ USUÁRIO │──▶│ FRONTEND │──▶│ API GATEWAY │
└─────────┘   │  (React) │   │  (FastAPI)  │
     ▲        └──────────┘   └──────┬──────┘
     │                              │
     │                   ┌──────────┴──────────┐
     │                   ▼                     ▼
     │         ┌───────────────────┐  ┌──────────────────┐
     │         │ PIPELINE INGESTÃO │  │ PIPELINE RAG (Q&A)│
     │         │ 1. Upload         │  │ 6. Recuperação    │
     │         │ 2. Extração       │  │ 7. Contexto       │
     │         │ 3. Chunking       │  │ 8. LLM            │
     │         │ 4. Embeddings     │  └────────┬─────────┘
     │         │ 5. Armazenamento  │           │
     │         └─────────┬─────────┘           │
     │                   ▼                     ▼
     │            ┌──────────────────────────────┐
     │            │  PostgreSQL + pgvector        │
     │            │  (documentos, chunks, vetores)│
     └────────────┴──────────────────────────────┘
              resposta da IA
```

---

## 4. Os dois fluxos em detalhe

### Fluxo A — Ingestão (quando você envia um documento)

1. **Upload** — arquivo recebido pela API, salvo em disco (depois: S3).
2. **Extração** — texto extraído (PyMuPDF / python-docx).
3. **Chunking** — texto dividido em pedaços de ~500 tokens com sobreposição de ~50 (mantém contexto entre os pedaços).
4. **Embeddings** — cada chunk vira um vetor numérico.
5. **Armazenamento** — chunks + vetores + metadados salvos no pgvector.

### Fluxo B — Pergunta (quando você pergunta)

6. **Recuperação** — a pergunta vira vetor; o banco retorna os *Top K* chunks mais parecidos (busca por similaridade de cosseno).
7. **Contexto** — os chunks recuperados são montados num *prompt* junto da pergunta.
8. **LLM** — o modelo gera a resposta baseada **só** nesse contexto, citando o documento.

---

## 5. Estrutura de pastas do projeto

```
ai-doc-platform/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entrypoint
│   │   ├── config.py               # lê .env (provedores, chaves)
│   │   ├── api/
│   │   │   ├── documents.py        # POST /documents (upload)
│   │   │   └── chat.py             # POST /chat (pergunta)
│   │   ├── core/
│   │   │   ├── extraction.py       # extrair texto (PDF/DOCX)
│   │   │   ├── chunking.py         # dividir em chunks
│   │   │   ├── retrieval.py        # busca Top K
│   │   │   └── rag.py              # orquestra contexto + LLM
│   │   ├── providers/
│   │   │   ├── base.py             # interfaces (LLM, Embedding)
│   │   │   ├── ollama_llm.py
│   │   │   ├── local_embeddings.py
│   │   │   ├── claude_llm.py        # plugar depois
│   │   │   └── openai_llm.py        # plugar depois
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   └── models.py           # tabelas documents, chunks
│   │   └── services/
│   │       └── ingestion.py        # orquestra fluxo A
│   ├── requirements.txt
│   └── .env.example
├── frontend/                       # React (fase 4)
├── docker-compose.yml              # Postgres+pgvector (fase 1)
└── README.md
```

---

## 6. Esquema do banco de dados

```sql
-- Documentos enviados
CREATE TABLE documents (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename    TEXT NOT NULL,
    status      TEXT DEFAULT 'processing',  -- processing | ready | error
    created_at  TIMESTAMP DEFAULT now()
);

-- Chunks com seus vetores (pgvector)
CREATE TABLE chunks (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id  UUID REFERENCES documents(id) ON DELETE CASCADE,
    content      TEXT NOT NULL,
    chunk_index  INT NOT NULL,
    embedding    VECTOR(384)                 -- dimensão do all-MiniLM-L6-v2
);

-- Índice pra busca rápida por similaridade
CREATE INDEX ON chunks USING ivfflat (embedding vector_cosine_ops);
```

---

## 7. Endpoints da API (MVP)

| Método | Rota | O que faz |
|---|---|---|
| `POST` | `/documents` | Envia documento → dispara ingestão (fluxo A). |
| `GET` | `/documents` | Lista documentos e status. |
| `POST` | `/chat` | Recebe pergunta → roda RAG (fluxo B) → retorna resposta + fontes. |
| `GET` | `/health` | Checa se API e banco estão de pé. |

Exemplo de resposta do `/chat`:
```json
{
  "answer": "O contrato vence em 12/2026.",
  "sources": [
    { "document": "contrato.pdf", "chunk": "...cláusula 8, vigência até dezembro de 2026..." }
  ]
}
```

---

## 8. Roadmap de construção (por fases)

Construímos incremental: cada fase entrega algo que **funciona** e testa de ponta a ponta.

- **Fase 0 — Setup**
  Instalar Ollama, subir Postgres+pgvector via Docker, criar ambiente Python. Validar com um "hello world" do LLM e do banco.

- **Fase 1 — Núcleo RAG (sem API ainda)**
  Scripts que: leem um PDF, fazem chunk, geram embeddings, salvam no banco, e respondem uma pergunta no terminal. *É aqui que o sistema "ganha vida".*

- **Fase 2 — Backend / API**
  Envelopar o núcleo no FastAPI: endpoints de upload e chat. Testar com `curl` ou Swagger.

- **Fase 3 — Robustez**
  Autenticação simples, validação, logs, tratamento de erro, status de processamento.

- **Fase 4 — Frontend**
  Interface React: tela de upload + chat com as fontes citadas.

- **Fase 5 — Infra & Deploy**
  Dockerizar tudo, CI com GitHub Actions, e (opcional) deploy na AWS.

> **Sugestão:** começar pela **Fase 0 + Fase 1**. Em poucos passos você já vê o sistema respondendo perguntas sobre um documento real, de graça e local.

---

## 9. Pré-requisitos para começar

- Python 3.11+
- Docker (pra subir o Postgres+pgvector)
- Ollama instalado (`ollama pull llama3.1`)
- ~6–8 GB de RAM livre pro modelo local (Llama 3.1 8B). Menos que isso → usar Phi-3 ou Gemma 2 2B, ou o free tier de uma API.

---

## 10. Decisões em aberto (pra confirmar antes de codar)

1. **Tipos de documento** no MVP: só PDF, ou já incluir DOCX/TXT?
2. **Idioma dos documentos**: PT, EN, ambos? (afeta a escolha do modelo de embedding).
3. **Multiusuário** desde já, ou single-user pra simplificar o MVP?
4. **Confirmar capacidade da máquina** (RAM/GPU) pra decidir o tamanho do modelo local.
