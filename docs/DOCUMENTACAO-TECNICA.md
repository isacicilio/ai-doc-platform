# 📘 Documentação Técnica — AI Document Intelligence Platform

> Documento de referência do projeto: o que foi construído, como cada peça
> funciona, as decisões de engenharia por trás dela, e o que ainda falta.
> Serve tanto como guia de manutenção quanto como material de estudo para
> defender o projeto em uma entrevista técnica.

---

## Índice

1. [Visão geral](#1-visão-geral)
2. [Conceitos-chave (o vocabulário do projeto)](#2-conceitos-chave)
3. [Arquitetura em camadas](#3-arquitetura-em-camadas)
4. [O que foi construído — Bloco a bloco](#4-o-que-foi-construído--bloco-a-bloco)
5. [Os dois fluxos de dados](#5-os-dois-fluxos-de-dados)
6. [Decisões técnicas para defender numa entrevista](#6-decisões-técnicas-para-defender-numa-entrevista)
7. [Como rodar (referência rápida)](#7-como-rodar-referência-rápida)
8. [O que falta — Bloco 8](#8-o-que-falta--bloco-8)
9. [Sugestão de frontend](#9-sugestão-de-frontend)
10. [Glossário rápido](#10-glossário-rápido)

---

## 1. Visão geral

A **AI Document Intelligence Platform** recebe documentos em PDF, entende o
conteúdo com IA e responde perguntas sobre eles usando **RAG**
(*Retrieval-Augmented Generation*).

O diferencial em relação a uma busca comum (`Ctrl+F`) é que ela busca por
**significado**, não por palavra exata. Você pergunta em linguagem natural, o
sistema encontra os trechos mais relevantes do documento e um modelo de
linguagem gera uma resposta **fundamentada apenas naquele conteúdo** — com a
indicação de onde a resposta foi encontrada.

**Stack:** Python + FastAPI · PostgreSQL + pgvector · SQLAlchemy · Docker.
Ponto central da arquitetura: **providers trocáveis** — dá para alternar entre
OpenAI, Claude e Ollama (local) mudando apenas o arquivo `.env`, sem tocar no
código.

**Estado atual:** backend completo e funcional de ponta a ponta (Blocos 1 a 7).
Falta apenas o Bloco 8 (frontend + acabamento de DevOps).

---

## 2. Conceitos-chave

Antes da arquitetura, o vocabulário. Entender estes cinco conceitos é entender
o projeto inteiro.

| Conceito | O que é |
|:---|:---|
| **Embedding** | Um texto convertido em uma lista de números (um vetor) que captura seu *significado*. Textos parecidos geram vetores próximos no espaço. |
| **Chunk** | Um pedaço do documento. Como um PDF inteiro é grande demais para virar um único vetor útil, ele é quebrado em pedaços menores. |
| **Banco vetorial** | Um banco que armazena vetores e sabe buscar por *similaridade* — "me dê os vetores mais parecidos com este" — em milissegundos. Aqui, PostgreSQL + pgvector. |
| **Similaridade de cosseno** | A medida usada para comparar dois vetores. Olha o *ângulo* entre eles (a direção/significado), não o tamanho. Menor distância = mais parecido. |
| **RAG** | *Retrieval-Augmented Generation*. Em vez de o modelo responder "de cabeça", ele primeiro **recupera** trechos relevantes do documento e só então **gera** a resposta com base neles. É o que ancora o modelo na verdade e reduz alucinação. |

---

## 3. Arquitetura em camadas

O projeto é organizado em camadas com responsabilidades separadas. Cada camada
só conhece a de baixo — nunca o contrário. Isso é o que permite testar e trocar
peças sem quebrar o resto.

```
┌─────────────────────────────────────────────┐
│  API (FastAPI)            app/api/           │  ← rotas HTTP, validação
├─────────────────────────────────────────────┤
│  Core (RAG)               app/core/          │  ← retrieval + geração
├─────────────────────────────────────────────┤
│  Services                 app/services/      │  ← ingestão, chunking
├─────────────────────────────────────────────┤
│  Providers                app/providers/     │  ← LLM e embeddings trocáveis
├─────────────────────────────────────────────┤
│  Banco de dados           app/db/            │  ← models, sessão, pgvector
├─────────────────────────────────────────────┤
│  Configuração             app/config.py      │  ← lê tudo do .env
└─────────────────────────────────────────────┘
```

A peça mais característica é a camada de **providers**. O resto do código nunca
fala diretamente com a OpenAI ou o Ollama — fala com uma **interface abstrata**.
Um `factory` lê o `.env` e devolve o provider concreto certo. Trocar de LLM é
mudar uma linha de configuração, não o código.

---

## 4. O que foi construído — Bloco a bloco

O projeto foi construído em blocos, na ordem de dependências (da fundação para
cima). Cada bloco abaixo descreve **o que foi feito** e **por que**.

### ✅ Bloco 1 — Fundação

Criação da estrutura base em `backend/`:
- **`requirements.txt`** com as dependências (FastAPI, SQLAlchemy, pgvector,
  pypdf, os SDKs de LLM, sentence-transformers).
- **`config.py`** — uma classe `Settings` (pydantic-settings) que centraliza
  toda a configuração e lê do `.env`: nome do app, URL do banco, escolha de
  provider, chaves de API, nomes dos modelos e os parâmetros do RAG
  (`chunk_size=1000`, `chunk_overlap=200`, `top_k=4`). Expõe
  `settings = get_settings()` com `@lru_cache` para criar a config uma única vez.
- **`.env.example`** — o modelo das variáveis de ambiente.

**Regra crítica estabelecida aqui:** o `embedding_dim` precisa bater com o modelo
de embedding escolhido (`text-embedding-3-small` = 1536; `all-MiniLM-L6-v2` = 384)
e com a dimensão da coluna vetorial no banco. Se não bater, o insert falha.

**Regra de trabalho:** comandos Python/pip rodam de dentro de `backend/` com a
venv ativa; comandos Docker rodam na raiz (onde está o `docker-compose.yml`).

### ✅ Bloco 2 — Banco com pgvector

- **`db/session.py`** — a conexão: `engine`, `SessionLocal` (fábrica de sessões),
  `Base` (que os models herdam) e `get_db()`, uma *dependency* do FastAPI que
  abre uma sessão por requisição e fecha no fim.
- **`db/models.py`** — duas tabelas. `Document` (o PDF inteiro: id, filename,
  status, created_at) e `Chunk` (um pedaço: content, chunk_index e a coluna
  mágica `embedding` do tipo `Vector(embedding_dim)`). Relação em cascata:
  apagar o documento apaga seus chunks.
- **`init_db.py`** — liga a extensão pgvector (`CREATE EXTENSION IF NOT EXISTS
  vector`) e cria as tabelas.
- **`docker-compose.yml`** — o serviço de banco usando a imagem
  `pgvector/pgvector:pg16`, com volume `pgdata` para persistir os dados.

### ✅ Bloco 3 — Providers (a identidade do projeto)

O coração conceitual. Construção da arquitetura de providers trocáveis.
- **`providers/base.py`** — duas interfaces abstratas (`ABC` + `@abstractmethod`):
  `LLMProvider` (método `generate`) e `EmbeddingProvider` (`dim`,
  `embed_documents`, `embed_query`). O contrato obrigatório garante que qualquer
  provider concreto implemente todos os métodos.
- **`providers/openai_llm.py`**, **`claude_llm.py`**, **`ollama_llm.py`** — três
  implementações de LLM com o mesmo contrato e SDKs diferentes.
- **`providers/local_embeddings.py`** e **`openai_embeddings.py`** — as duas
  implementações de embeddings.
- **`providers/factory.py`** — `get_llm_provider()` e `get_embedding_provider()`
  leem o `.env` e devolvem o provider certo já instanciado. É o único lugar que
  conhece as classes concretas. Usa imports *lazy* (só carrega o SDK do provider
  escolhido) e `@lru_cache` (não recria o provider a cada chamada — crítico para
  o modelo local, que leva segundos para carregar).

### ✅ Bloco 4 — Ingestão (PDF vira dados pesquisáveis)

O fluxo: **PDF → texto → chunks → vetores → banco**.
- **`services/chunking.py`** — divide o texto em pedaços de ~1000 caracteres com
  overlap de 200, respeitando fronteiras naturais (parágrafos, frases) via
  separadores em cascata `["\n\n", "\n", ". ", " ", ""]` e recursão. Mesmo
  princípio do `RecursiveCharacterTextSplitter` do LangChain.
- **`services/ingestion.py`** — o orquestrador: extrai o texto com pypdf, chama
  o chunking, pede os vetores ao provider (em lote) e salva cada chunk com seu
  vetor. Implementa uma máquina de estados no status
  (`processing → completed | failed`) e trata PDF escaneado (sem texto) com
  mensagem clara.

Nesta fase o projeto migrou para configuração **100% local** (`LLM_PROVIDER=ollama`,
`EMBEDDING_PROVIDER=local`, `EMBEDDING_DIM=384`), ativando toda a arquitetura de
providers. Teste final: ingestão de um PDF real gerou 9 chunks com embeddings de
384 dimensões, confirmados no banco.

### ✅ Bloco 5 — Core RAG

O bloco que dá nome ao projeto: **pergunta → busca chunks similares → monta
prompt → LLM gera resposta**.
- **`core/retrieval.py`** — `retrieve_relevant_chunks(db, question, top_k)`.
  Vetoriza a pergunta com `embed_query` (o **mesmo** provider da ingestão, para
  pergunta e chunks viverem no mesmo espaço vetorial) e pede ao pgvector os
  `top_k` chunks mais próximos por distância de cosseno — a busca roda no banco,
  não em Python.
- **`core/rag.py`** — `answer_question(db, question)`. Recupera os chunks
  (Retrieval), monta o prompt com eles como contexto (Augmented) e pede a
  resposta ao LLM (Generation). Um `SYSTEM_PROMPT` ancora o modelo no contexto e
  o instrui a admitir quando não sabe (mitigação de alucinação). Retorna
  `{answer, sources}` para rastreabilidade.

**Validado com Ollama + `llama3.2` (3B):** o sistema respondeu corretamente a uma
pergunta sobre o documento **e** recusou-se a responder "qual a capital da
França?" (que não está no documento) — a prova de que o RAG está ancorado no
contexto.

### ✅ Bloco 6 — API (FastAPI)

As funções viraram **endpoints HTTP**.
- **`api/schemas.py`** — os contratos (Pydantic): `AskRequest`, `AskResponse`,
  `Source`, `DocumentOut`. O FastAPI valida entrada e saída automaticamente.
- **`api/routes.py`** — quatro rotas (ver seção 7). É aqui que o `get_db()` do
  Bloco 2 finalmente entra em ação, via `Depends(get_db)`.
- **`main.py`** — monta a aplicação FastAPI, registra as rotas e expõe a
  documentação interativa automática em `/docs`.

A rota de upload salva o PDF em um arquivo temporário antes de chamar a ingestão
(porque `ingest_document` lê de um caminho em disco), e limpa o temporário no fim.

### ✅ Bloco 7 — Docker ponta a ponta

Toda a aplicação (backend + banco) passa a subir com **um comando**.
- **`backend/Dockerfile`** — a receita da imagem: parte de `python:3.11-slim`,
  instala o PyTorch em versão **CPU-only** (muito mais leve), instala as
  dependências e liga o uvicorn com `--host 0.0.0.0` (obrigatório dentro do
  container).
- **`backend/.dockerignore`** — impede que `.venv`, cache e o `.env` (segredos)
  entrem na imagem.
- **`docker-compose.yml`** (atualizado) — adiciona o serviço `backend` ao lado do
  `db`, com healthcheck no banco (o backend só sobe quando o banco está pronto) e
  criação automática das tabelas no start.

**As duas "viradas de rede"** — resolvidas só por variáveis de ambiente, sem tocar
no código, graças à arquitetura desacoplada:
1. **Banco:** dentro do Docker, o backend acha o banco pelo nome do serviço
   (`db:5432`), não `localhost`.
2. **Ollama:** o Ollama roda nativo no host; o container o alcança por
   `host.docker.internal:11434`.

---

## 5. Os dois fluxos de dados

### Fluxo de ingestão (guardar o documento)

```
PDF → extract_text_from_pdf (pypdf) → chunk_text → embed_documents (lote)
    → salva Chunks com embedding no Postgres → Document.status = "completed"
```

### Fluxo de consulta / RAG (perguntar sobre o documento)

```
pergunta → embed_query → pgvector: top_k por distância de cosseno
        → _build_prompt (contexto + pergunta) → LLM.generate
        → { answer, sources }
```

O ponto sutil e importante: a ingestão usa `embed_documents` e a consulta usa
`embed_query`, mas **ambas passam pelo mesmo provider** (garantido pelo factory).
Se fossem providers diferentes, os vetores viveriam em espaços incompatíveis e a
busca não faria sentido.

---

## 6. Decisões técnicas para defender numa entrevista

Estas são as perguntas que um entrevistador faria — e as respostas prontas.

**"Por que similaridade de cosseno?"**
Porque ela mede o *ângulo* entre vetores (direção = significado), ignorando a
magnitude. É o padrão da indústria para busca semântica. Dois textos com o mesmo
sentido apontam para a mesma direção mesmo que tenham tamanhos diferentes.

**"Por que dividir em chunks com overlap?"**
Um PDF inteiro em um único vetor perderia nuance. Chunks menores geram vetores
mais precisos. O overlap de 200 caracteres evita cortar uma ideia no meio da
fronteira — se "o contrato vence em | 2026" for partido, nenhum dos lados
responderia bem. O corte respeita parágrafos e frases (não corta cego por
caractere).

**"Como você lida com alucinação?"**
Duas defesas. (1) O RAG em si: o modelo responde com base em trechos reais
recuperados, não "de cabeça". (2) O `SYSTEM_PROMPT` instrui explicitamente a usar
**apenas** o contexto e a admitir quando a informação não está no documento.
Testado: o sistema recusou responder algo fora do documento mesmo *sabendo* a
resposta.

**"Por que essa arquitetura de providers?"**
Para desacoplar. O código de negócio depende de uma **interface** (`LLMProvider`),
não de uma implementação. Trocar OpenAI → Claude → Ollama é mudar o `.env`. Isso
usa dois padrões clássicos: *Strategy/Provider* (interfaces intercambiáveis) e
*Factory* (um ponto único que instancia a implementação certa).

**"Por que validar no `__init__` em uns providers e na chamada em outros?"**
Princípio: valide no `__init__` o que é **estático** (uma chave de API existe ou
não — falha cedo e claro); valide na chamada o que é **volátil** (o servidor
Ollama pode cair a qualquer momento — validar na hora, com mensagem útil).

**"Por que imports lazy e `@lru_cache` no factory?"**
Lazy import: só carrega o SDK (ou o PyTorch pesado) do provider realmente
escolhido. `@lru_cache`: não recria o provider a cada chamada — crítico para o
modelo local de embeddings, que leva segundos para carregar na memória.

**"Como o sistema roda em qualquer máquina?"**
Docker Compose sobe API + banco juntos, cria as tabelas no start e conecta os
containers por rede interna. Um `git clone` + `docker compose up` reproduz o
ambiente inteiro, sem "funciona na minha máquina".

---

## 7. Como rodar (referência rápida)

### Endpoints da API

| Método | Rota | Descrição |
|:---|:---|:---|
| `POST` | `/documents` | Envia um PDF e dispara a ingestão |
| `POST` | `/ask` | Faz uma pergunta e recebe resposta + fontes |
| `GET` | `/documents` | Lista os documentos enviados |
| `GET` | `/documents/{id}` | Consulta o status de um documento |

Documentação interativa: **http://localhost:8000/docs**

### Subir tudo (Docker)

```bash
ollama pull llama3.2          # modo local: baixa o modelo no host
docker compose up --build     # sobe API + banco com um comando
```

### Desenvolvimento (hot-reload)

```bash
docker compose up -d db
cd backend && uvicorn app.main:app --reload
```

---

## 8. O que falta — Bloco 8

O backend está completo. O que resta é o **acabamento** que transforma o projeto
em uma peça de portfólio redonda.

### 8.1 Frontend (a interface visual)

Uma página onde o usuário sobe um PDF e faz perguntas clicando, vendo as
respostas e as fontes — sem terminal, sem `/docs`. É o que torna o projeto
demonstrável para qualquer pessoa. Detalhes e recomendação na seção 9.

### 8.2 DevOps e acabamento

- **README** — ✅ já atualizado (roadmap, API, Docker, diagrama).
- **CORS** — quando o frontend chamar a API pelo navegador, pode ser preciso
  liberar CORS no FastAPI (`CORSMiddleware`). Se o frontend for servido pelo
  próprio FastAPI (mesma origem), esse problema nem aparece.
- **Documentação** — ✅ este documento.
- **Revisão final do repositório** — garantir que sobe do zero em qualquer
  máquina, histórico de commits limpo, `.env` protegido.
- **(Opcional) Integrar o `extraction.py`** — hoje é um stub. Se o objetivo for
  suportar DOCX além de PDF, criar um módulo de extração real e refatorar,
  tirando a lógica de extração de dentro do `ingestion.py`.

---

## 9. Sugestão de frontend

O backend expõe uma API REST simples (JSON). Isso deixa o frontend livre — qualquer
tecnologia que faça requisições HTTP serve. Duas opções fazem sentido para este
projeto:

### Opção recomendada — Página única (HTML + CSS + JS puro), servida pelo FastAPI

Uma única página que usa `fetch()` para chamar `/documents` (upload) e `/ask`
(perguntas). Servida como arquivo estático **pelo próprio FastAPI**.

**Por que é a melhor escolha aqui:**
- **Sem build, sem `node_modules`** — ideal para uma máquina com 8GB de RAM e
  para "clonar e rodar" sem passos extras.
- **Sem problema de CORS** — servida pelo mesmo servidor da API (mesma origem).
- **Continua sendo "um comando"** — sobe junto no `docker compose up`, mantendo a
  história de deploy limpa.
- Com um CSS moderno, o resultado visual fica praticamente igual ao de um app
  React para este caso de uso.

**Como se encaixa:** monta-se `POST /` no FastAPI servindo o `index.html`, e a
pasta `frontend/` (que já existe) guarda `index.html`, `style.css` e `app.js`.

### Alternativa — React + Vite

Combina com o diagrama do projeto (que menciona React) e agrega a palavra "React"
ao portfólio. Em troca, pesa mais: exige Node, `npm install` (muitos arquivos),
um passo de build e configuração de CORS. Viável, mas mais trabalho para um ganho
pequeno neste projeto específico.

### Recomendação final

Comece pela **página única servida pelo FastAPI**. É o caminho mais rápido para
um sistema demonstrável de ponta a ponta, mantém a máquina leve e preserva a
elegância do "um comando sobe tudo". Se depois quiser exibir React no currículo,
a migração é tranquila — a API não muda.

---

## 10. Glossário rápido

- **RAG** — recuperar trechos relevantes e gerar a resposta com base neles.
- **Embedding** — texto convertido em vetor de significado.
- **Chunk** — pedaço de um documento.
- **pgvector** — extensão do PostgreSQL para armazenar e buscar vetores.
- **Similaridade de cosseno** — comparação de vetores por ângulo (significado).
- **Provider** — implementação intercambiável de LLM ou de embeddings.
- **Factory** — função que escolhe e instancia o provider certo conforme o `.env`.
- **Dependency injection** — a sessão do banco é recebida de fora, não criada
  internamente; quem chama controla o ciclo de vida.
- **top_k** — quantos chunks mais parecidos a busca retorna (aqui, 4).
- **host.docker.internal** — endereço pelo qual um container alcança a máquina
  hospedeira.

---

*Documento gerado para a AI Document Intelligence Platform — projeto de portfólio
para AI Engineering. Última atualização: fechamento do Bloco 7.*
