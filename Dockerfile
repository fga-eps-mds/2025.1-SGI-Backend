# Dockerfile
FROM python:3.11-slim

# Diretório de trabalho dentro do container
WORKDIR /app

# Copiar e instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código
COPY . .

# Abrir a porta do Django
EXPOSE 8000

# Comando para rodar o servidor
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
