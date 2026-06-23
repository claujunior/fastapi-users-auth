# 🎬 Streaming de episódios (sob demanda)

Resolve o link de vídeo de **um** episódio só quando o usuário clica pra assistir.
Os metadados (título, nº de episódios) vêm do **MAL**; o link de vídeo vem do
provedor **AllAnime** (via `anipy-api`), que é instável — por isso resolvemos
on-demand, com retry e cache.

## Arquitetura

```
Front (web/)                         Backend (fastapi-users-auth/)
─────────────                        ─────────────────────────────
paginaAnime.js                       anime_router.py
  num_episodes (MAL) ──► grade       GET /anime/{id}/episodes/{ep}/stream  -> metadados
  clique no ep ──────────────────►   GET /anime/{id}/episodes/{ep}/video   -> proxy do mp4
  <video src = /video proxy>         services/streaming.py
                                       resolve_stream(title, ep, lang)
                                         AllAnime get_search -> get_video
```

- **`/stream`** → `{resolution, type, provider_title}`. O player usa pra saber mp4 vs hls.
- **`/video`** → proxy: busca no host com o `Referer` correto e repassa os bytes,
  encaminhando `Range` (permite seek na barra do player).

## Por que existe o proxy (`/video`)

O host de vídeo (`fast4speed.rsvp`) tem **hotlink protection**: só serve o vídeo
se a requisição vier com `Referer: https://allanime.day`. O navegador, tocando de
`localhost`, manda o próprio Referer e **não pode forçar outro** num `<video>`.
Resultado: apontar o `<video>` direto pra URL dá **404**.

O backend resolve isso: o `<video>` aponta pro `/video`, e o backend faz a
requisição ao host com o `Referer` certo. Custo: a banda do vídeo passa pelo
backend (ok pra projeto pequeno).

## Pontos em aberto / decisões

1. **HLS (`.m3u8`) não suportado ainda.** Alguns animes servem HLS em vez de mp4.
   Hoje o player detecta (`type == "hls"`) e só avisa. Pra suportar: **hls.js** no
   front + reescrever as URLs dos segmentos no proxy. (Naruto é mp4, funciona.)

2. **Match de título é best-effort.** `_best_match` usa similaridade (`rapidfuzz`)
   entre o título do MAL e os resultados do provedor — evita pegar cegamente o
   primeiro, mas pode errar em casos como "Tokyo Ghoul" vs "Tokyo Ghoul:re".

3. **Cache de 30 min** (`CACHE_TTL` em `services/streaming.py`). O link resolvido
   é reusado por (título, episódio, idioma) pra não bater no provedor instável a
   cada seek/replay. O token na URL dura ~dias, então 30 min é seguro.

4. **Retry + backoff** (`with_retry`, 4 tentativas: 1s/2s/4s). O provedor devolve
   520 e respostas vazias com frequência; o retry recupera a maioria.

5. **`anipy-api` é síncrono** (usa `requests`). Os endpoints async chamam o
   resolver via `run_in_threadpool` pra não travar o event loop.

## Dependências

`anipy-api` (e suas deps: rapidfuzz, beautifulsoup4, m3u8, pycryptodomex, etc.)
estão pinadas no `requirements.txt` (gerado por `pip freeze`).
