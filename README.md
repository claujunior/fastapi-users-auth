<div align="center">

# 🎌 AniLib API

Backend de streaming e gerenciamento de animes construído com FastAPI, MongoDB e integração nativa com MyAnimeList.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)]()
[![MongoDB](https://img.shields.io/badge/MongoDB-Database-brightgreen.svg)]()
[![JWT](https://img.shields.io/badge/Auth-JWT-orange.svg)]()


</div>

---

## 📖 Sobre o Projeto

AniLib API é uma plataforma backend desenvolvida para fornecer uma experiência completa de descoberta, gerenciamento e streaming de animes.

O projeto integra múltiplas fontes de dados, autenticação moderna baseada em JWT, sincronização com MyAnimeList e serviços de streaming de episódios através de uma API REST escalável.

### Principais objetivos

- Centralizar informações de animes
- Fornecer streaming através de API
- Sincronizar listas com MyAnimeList
- Oferecer autenticação segura
- Servir como backend para aplicações web e mobile

---

## ✨ Funcionalidades

### 🔐 Autenticação

- Cadastro de usuários
- Login com JWT
- Rotas protegidas
- Hash de senha com Argon2
- Controle de sessão seguro

### 🎌 Catálogo de Animes

- Busca por nome
- Animes recentes
- Top animes
- Informações detalhadas
- Episódios disponíveis

### 🎥 Streaming

- Resolução automática de fontes
- Proxy para vídeos
- Streaming otimizado
- Suporte a Range Requests
- Compatível com players HTML5

### 📚 MyAnimeList

- OAuth2 PKCE
- Vinculação de conta
- Consulta da lista pessoal
- Atualização de status
- Atualização de nota
- Remoção de animes

### 🚀 API REST

- Arquitetura modular
- Respostas JSON
- Documentação Swagger automática
- Fácil integração com frontend

---

## 🏗 Arquitetura

```text
Client
   │
   ▼
FastAPI Router
   │
   ▼
Services
   │
   ▼
Repositories
   │
   ▼
MongoDB
```

O projeto segue uma arquitetura em camadas para facilitar manutenção, testes e escalabilidade.

| Camada | Responsabilidade |
|----------|------------------|
| Router | Receber requisições HTTP |
| Service | Regras de negócio |
| Repository | Persistência de dados |
| Database | Conexão com MongoDB |
| Auth | Segurança e autenticação |

---

## 🛠 Tecnologias

### Backend

- FastAPI
- Python
- Pydantic
- Uvicorn

### Banco de Dados

- MongoDB
- Motor (Async Mongo Driver)

### Segurança

- JWT
- Argon2
- OAuth2 PKCE

### Integrações

- MyAnimeList API
- AniPy

### Infraestrutura

- Docker
- Docker Compose

---

## 📂 Estrutura

```text
.
├── auth/
├── database/
├── dto/
├── exceptions/
├── middleware/
├── model/
├── repositories/
├── routers/
├── services/
├── main.py
├── requirements.txt
└── docker-compose.yml
```

---

## ⚙️ Instalação

### Clonar repositório

```bash
git clone https://github.com/seuusuario/anilib-api.git
cd anilib-api
```

### Criar ambiente virtual

```bash
python -m venv .venv
```

Windows

```bash
.venv\Scripts\activate
```

Linux/macOS

```bash
source .venv/bin/activate
```

### Instalar dependências

```bash
pip install -r requirements.txt
```

---

## 🔧 Configuração

Crie um arquivo `.env`

```env
MONGO_URL=mongodb://localhost:27017
JWT_SECRET=xxxxxxxxxxxxxxxxxxxx
API_MAL=https://api.myanimelist.net/v2
MAL_CLIENT_ID=xxxxxxxxxxxxxxxxxxx
MAL_REDIRECT_URI=http://localhost:8000/auth/mal/callback
FRONTEND_URL=http://localhost:5500
MAL_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 🐳 Docker

Subir MongoDB

```bash
docker compose up -d
```

Verificar containers

```bash
docker ps
```

---

## ▶️ Executando

```bash
uvicorn main:app --reload
```

Servidor:

```text
http://localhost:8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

---

## 📡 Principais Endpoints

### Usuários

| Método | Endpoint |
|----------|----------|
| POST | /users |
| POST | /users/login |
| GET | /users |

### Animes

| Método | Endpoint |
|----------|----------|
| GET | /anime |
| GET | /anime/search |
| GET | /anime/topanimes |
| GET | /anime/{id} |
| GET | /anime/{id}/episodes |

### Streaming

| Método | Endpoint |
|----------|----------|
| GET | /anime/{id}/episodes/{ep}/stream |
| GET | /anime/{id}/episodes/{ep}/video |

### MyAnimeList

| Método | Endpoint |
|----------|----------|
| GET | /auth/mal/start |
| GET | /auth/mal/callback |
| GET | /me/mal |
| DELETE | /me/mal |
| GET | /me/animelist |
| PATCH | /me/animelist/{id} |
| DELETE | /me/animelist/{id} |

---

## 🔒 Segurança

O projeto implementa:

- JWT Authentication
- Password Hashing com Argon2
- OAuth2 PKCE
- Validação de entrada com Pydantic
- Middleware de autenticação
- Separação de responsabilidades

---
