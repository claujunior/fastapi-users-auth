# 🚀 Como subir o projeto do zero (para testar)

Guia rápido para subir tudo do zero nesta máquina (WSL Ubuntu).
Ordem importa: **primeiro o banco, depois o backend.**

Caminhos desta máquina:
- Projeto: `/home/kafka/materias/web/fastapi-users-auth`
- MongoDB portable: `/home/kafka/mongodb-portable/...`
- Dados do banco: `/home/kafka/mongodb-portable/data`

---

## 1. Subir o MongoDB

```bash
/home/kafka/mongodb-portable/mongodb-linux-x86_64-ubuntu2404-8.0.4/bin/mongod \
  --dbpath /home/kafka/mongodb-portable/data \
  --port 27017 --bind_ip 127.0.0.1 \
  --logpath /home/kafka/mongodb-portable/log/mongod.log --fork
```

> O `--fork` faz o Mongo rodar em segundo plano. Os dados **persistem** em
> `--dbpath` entre reinícios (não apaga nada).

**Conferir se subiu:**
```bash
ss -ltnp | grep 27017
```
Tem que aparecer uma linha com `mongod` escutando em `127.0.0.1:27017`.

---

## 2. Subir o backend (FastAPI / uvicorn)

```bash
cd /home/kafka/materias/web/fastapi-users-auth
source .venv/bin/activate
uvicorn main:app --reload
```

**Conferir se subiu:**
- Terminal mostra `Uvicorn running on http://127.0.0.1:8000`
- API: http://localhost:8000
- Docs (Swagger): http://localhost:8000/docs

> Deixe esse terminal **aberto**. É nele que aparecem os logs/erros
> (ex.: ao testar o "conectar ao MAL", erros como
> `"Falha ao autenticar com o MAL"` ou `"State inválido"` aparecem aqui).

---

## 3. Frontend

O frontend é **estático** (HTML/CSS/JS, sem `package.json`) e fica em outra pasta,
**fora** do projeto do backend:

```
/home/kafka/materias/web/web
```

> É um repositório git **separado** do backend.

Ele precisa ser servido na **porta 5500** (é o que está em `FRONTEND_URL` no `.env`).
Duas formas:

**a) VS Code — Live Server** (mais comum): abrir a pasta `web/web` no VS Code e
clicar em **"Go Live"** (sobe em `http://localhost:5500`).

**b) Pelo terminal** (sem VS Code):
```bash
cd /home/kafka/materias/web/web
python3 -m http.server 5500
```
Acessar em http://localhost:5500

---

## ✅ Checklist antes de testar o MAL

1. [ ] MongoDB rodando (porta 27017 escutando)
2. [ ] Backend rodando (porta 8000)
3. [ ] Arquivo `.env` preenchido com os valores **reais** (não os placeholders do `.env.example`):
   - `MAL_CLIENT_ID`
   - `MAL_CLIENT_SECRET`
   - `MAL_REDIRECT_URI=http://localhost:8000/auth/mal/callback`
   - `MONGO_URL=mongodb://localhost:27017`
   - `JWT_SECRET=<sua chave>`

> Lembrete: o `.env` **não** vem do GitHub (está no `.gitignore`).
> Cada máquina precisa ter o seu, preenchido à mão.

---

## 🛑 Como parar tudo

**Parar o backend:** no terminal do uvicorn, aperte `Ctrl + C`.

**Parar o MongoDB (shutdown limpo):**
```bash
pkill -TERM mongod
```

**Conferir que parou tudo:**
```bash
ps aux | grep -iE "mongod|uvicorn" | grep -v grep
ss -ltnp | grep -E ":8000|:27017"
```
Se não aparecer nada, está tudo parado.

---

## ⚠️ Zerar o banco (apaga TODOS os usuários!)

Só faça isso se quiser começar com o banco **realmente vazio**.
Pare o Mongo antes (passo acima), depois:

```bash
rm -rf /home/kafka/mongodb-portable/data/*
```

E suba o Mongo de novo (passo 1). Isso apaga todos os usuários e
conexões do MAL salvas.
