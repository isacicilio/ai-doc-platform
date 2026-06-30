# AI Document Intelligence Platform — Registro de Progresso

> Documento de acompanhamento do desenvolvimento. Atualizado conforme avançamos em blocos.

## Visão geral do projeto

Sistema que recebe documentos (PDFs), entende o conteúdo com IA e responde perguntas sobre eles usando **RAG (Retrieval-Augmented Generation)**. Projeto de portfólio para vagas de **AI Engineer**.

**Stack:**
- Backend: Python + FastAPI
- Banco: PostgreSQL + pgvector (banco vetorial)
- IA: providers trocáveis (OpenAI / Claude / Ollama) — alterna pelo `.env`, sem mexer no código
- DevOps: Docker

**Estratégia:** preencher os arquivos em blocos, na ordem de dependências (da fundação para cima).

## Plano em 8 blocos

1. **Fundação** — configs e dependências ✅
2. **Banco com pgvector** — código pronto, falta rodar ⏳
3. **Providers** — LLM e embeddings (próximo)
4. **Ingestão** — PDF vira chunks com vetores
5. **Core RAG** — busca semântica + geração
6. **API** — rotas e `main.py`
7. **Rodar tudo** — Docker + teste ponta a ponta
8. **Frontend e DevOps**

## Bloco 1 — Fundação (CONCLUÍDO E TESTADO)

Arquivos criados em `backend/`:

- **`requirements.txt`** — FastAPI, uvicorn, pydantic, pydantic-settings, SQLAlchemy, psycopg2, pgvector, pypdf, httpx, anthropic, openai, sentence-transformers (opcional/pesado).
- **`app/config.py`** — classe `Settings` (pydantic-settings) que centraliza configuração e lê do `.env`. Contém nome do app, URL do banco, escolha de providers, chaves de API, nomes dos modelos e parâmetros do RAG (`chunk_size=1000`, `chunk_overlap=200`, `top_k=4`, `embedding_dim=1536`).
- **`.env.example`** — modelo das variáveis de ambiente.

### Regra crítica: `embedding_dim`
O `embedding_dim` precisa bater com o modelo de embedding escolhido:
- `text-embedding-3-small` (OpenAI) = **1536**
- `all-MiniLM-L6-v2` (local) = **384**

Esse número precisa ser igual ao da coluna de vetor no banco, senão o insert falha.

### Problema resolvido
O primeiro `pip install` falhou porque o comando rodou na **raiz** do projeto, mas os arquivos estão em `backend/`.

**Regra do projeto:** todo comando Python/pip roda de dentro de `backend/`, com a venv ativa:
```powershell
.\.venv\Scripts\Activate.ps1
cd backend
```

**Teste que passou:**
```powershell
python -c "from app.config import settings; print(settings.app_name, '|', settings.llm_provider)"
# Saída: AI Document Intelligence Platform | openai
```

## Bloco 2 — Banco com pgvector (CÓDIGO PRONTO, FALTA RODAR)

Arquivos criados:

- **`app/db/session.py`** — conexão com o banco: `engine`, `SessionLocal`, `Base` e a função `get_db()` (dependency do FastAPI que abre uma sessão por request e fecha no fim).
- **`app/db/models.py`** — duas tabelas:
  - `Document`: o PDF inteiro (id, filename, status, created_at) com relação para os chunks (cascade: apagar documento apaga os chunks).
  - `Chunk`: pedaço do documento (content, chunk_index) + coluna `embedding` do tipo `Vector(settings.embedding_dim)`.
- **`app/init_db.py`** — script que liga a extensão pgvector (`CREATE EXTENSION IF NOT EXISTS vector`) e cria as tabelas (`Base.metadata.create_all`).
- **`docker-compose.yml`** (raiz) — serviço de banco com imagem `pgvector/pgvector:pg16`, usuário/senha `postgres`, banco `aidocs`, porta 5432, volume `pgdata` para persistir dados.

### Falta executar (onde paramos)
```powershell
# Na raiz (onde está o docker-compose.yml), com Docker Desktop aberto:
docker compose up -d
docker compose ps

# Depois, dentro de backend/ com venv ativa:
cd backend
python -m app.init_db
# Saída esperada: Banco inicializado: extensão pgvector + tabelas criadas.
```

## Nota: avisos amarelos do Pylance

Avisos `could not be resolved` (pydantic_settings, sqlalchemy, pgvector) são **avisos do editor, não erros de código** — o código roda (o teste do Bloco 1 passou). Causa: VS Code apontando para o Python global (`3.11.9 Microsoft Store`) em vez da `.venv`.

**Solução:** `Ctrl+Shift+P` → **Python: Select Interpreter** → escolher a opção com `.venv`.

## Status atual

- Você vai **instalar o Docker Desktop**.
- Ao voltar, confirmar: `docker --version` e `docker info` (no Windows o Docker Desktop precisa estar **aberto**, baleia estável na bandeja).
- Depois: subir o banco e rodar `init_db`.
- Plano B, se o Docker der trabalho: instalar Postgres direto no Windows.

## Próximo passo

Terminar de rodar o Bloco 2 (subir banco + `init_db`) e seguir para o **Bloco 3 — Providers**:
1. `providers/base.py` — interface abstrata que todos os providers implementam
2. `providers/openai_llm.py`
3. `providers/claude_llm.py`
4. `providers/ollama_llm.py`
5. `providers/local_embeddings.py`
