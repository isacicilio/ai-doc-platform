# backend/Dockerfile
FROM python:3.11-slim

# PYTHONUNBUFFERED faz os logs saírem na hora (bom pra ver no 'docker logs').
# PYTHONDONTWRITEBYTECODE evita gerar arquivos .pyc dentro do container.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# gcc e libpq-dev são necessários pra compilar o psycopg2 (driver do Postgres).
# Instalamos, e limpamos o cache do apt na mesma linha pra não inchar a imagem.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala o PyTorch na versão CPU-only ANTES do resto. Por quê? O torch padrão
# (que o sentence-transformers puxa) vem com bibliotecas de GPU/CUDA que pesam
# VÁRIOS GB e que você não usaria — sua máquina roda no CPU. A versão CPU é
# muito menor. Isso deixa a imagem bem mais leve.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copia só o requirements primeiro (truque de cache do Docker: se depois você
# mudar o código mas não as dependências, o Docker reaproveita esta camada e
# não reinstala tudo de novo).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Agora o código da aplicação.
COPY . .

EXPOSE 8000

# --host 0.0.0.0 é OBRIGATÓRIO dentro do container. Sem isso, o uvicorn só
# aceitaria conexões de dentro dele mesmo, e nem seu navegador chegaria nele.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]