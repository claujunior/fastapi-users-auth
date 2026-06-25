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
  /episodes ──► grade                GET /anime/{id}/episodes/{ep}/stream  -> metadados
  clique no ep ──────────────────►   GET /anime/{id}/episodes/{ep}/video   -> proxy do mp4
  <video src = /video proxy>         services/streaming.py
                                       resolve_stream(detail, ep, lang)
                                         _resolve_anime -> get_video
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

1. **HLS (`.m3u8`):** na prática **não apareceu** — testando ~15 títulos populares,
   todos vieram em **mp4** (host `fast4speed`). O player ainda detecta `type == "hls"`
   e avisa, por garantia, mas até agora esse provedor serve mp4 pra tudo. Se um dia
   aparecer HLS, suportar exige **hls.js** no front + reescrever segmentos no proxy.

2. **Match de título (MAL → AllAnime).** Matcher próprio (`_match`/`_resolve_anime`),
   que pega as boas ideias do `MyAnimeListAdapter` do `anipy` sem os pontos fracos
   dele (que casava Specials/Recaps por usar Levenshtein puro num `set`). Recebe o
   **detalhe completo do MAL** (não só o título) e:
   - **busca** o provedor com título principal **+ en/ja/sinônimos**;
   - **pontua** cada candidato por `token_sort_ratio` contra o nome dele; se o nome
     não bate (e ele não é um Special), consulta os **nomes alternativos** via
     `get_info` — é isso que casa nome estilizado (Tokyo Ghoul = `🆃🅾🅺🆈🅾...`)
     e apelido (One Piece = **"1P"**, 1168 eps) **sem precisar de override**;
   - **penaliza** marcadores de derivado no nome do candidato (`SEQUEL_MARKERS`:
     special, recap, ova, movie, season, part, √a, :re...) que não estejam no título
     do MAL — é o que evita cair em "X Specials"/"Recaps";
   - só aceita acima de `MIN_RATIO` (70), senão devolve `None`.

3. **`_SafeAllAnimeProvider`** (em `services/streaming.py`). O matcher chama
   `get_info` em candidatos; o AllAnime às vezes devolve `"show": null`, o que
   estoura. A subclasse devolve info vazia nesse caso (mantendo erros de rede
   subindo pro `with_retry`), pra um candidato ruim não derrubar o match inteiro.

4. **Cache de 30 min** (`CACHE_TTL` em `services/streaming.py`). O link resolvido
   é reusado por (título, episódio, idioma) pra não bater no provedor instável a
   cada seek/replay. O token na URL dura ~dias, então 30 min é seguro.

5. **Retry + backoff** (`with_retry`, 4 tentativas: 1s/2s/4s). O provedor devolve
   520 e respostas vazias com frequência; o retry recupera a maioria.

6. **`anipy-api` é síncrono** (usa `requests`). Os endpoints async chamam o
   resolver via `run_in_threadpool` pra não travar o event loop.

## Dependências

`anipy-api` (e suas deps: rapidfuzz, beautifulsoup4, m3u8, pycryptodomex, etc.)
estão pinadas no `requirements.txt` (gerado por `pip freeze`).
