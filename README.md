# 🐍 GitFica

Este projeto é uma aplicação backend Django containerizada com Docker e orquestrada via Docker Compose.

## 🚀 Tecnologias

- Python 3.11
- Django
- Docker
- Docker Compose

## 📦 Pré-requisitos

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

## ⚙️ Como rodar o projeto

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/seu-repo.git
cd seu-repo
```

### 2. Construa a imagem e suba os containers
```bash
docker compose up 
```

### 3. Acesse a aplicação
```bash
http://localhost:8000
```

🧪 Comandos úteis
- Subir containers: docker-compose up
- Parar containers: docker-compose down
- cessar o shell: docker-compose exec web bash
- Rodar testes: docker-compose exec web python core/manage.py test
