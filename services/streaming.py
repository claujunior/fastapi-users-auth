import time

from rapidfuzz import fuzz

from anipy_api.provider.providers import AllAnimeProvider
from anipy_api.provider import LanguageTypeEnum

MAX_ATTEMPTS = 4          # tentativas por chamada (1 + 3 retries)
BASE_DELAY = 1.0          # backoff: 1s, 2s, 4s...
CACHE_TTL = 1800          # segundos: reusa o link resolvido (o token dura ~dias)

# O AllAnimeProvider é síncrono (usa requests). Reusamos uma instância;
# o resolver deve rodar em threadpool a partir do endpoint async.
_provider = AllAnimeProvider(base_url_override=None)

# cache em memória: (title, episode, lang) -> (resultado, expira_em)
_cache = {}


def with_retry(fn, *args, attempts=MAX_ATTEMPTS, base_delay=BASE_DELAY):
    """Roda fn(*args) com retry e backoff exponencial.

    O provedor (AllAnime) é instável: devolve 520 e respostas vazias
    (data["episode"] vira None -> TypeError). Retry recupera a maioria
    dessas falhas transitórias. Levanta a última exceção se esgotar.
    """
    for attempt in range(1, attempts + 1):
        try:
            return fn(*args)
        except Exception:
            if attempt == attempts:
                raise
            time.sleep(base_delay * (2 ** (attempt - 1)))


def _best_match(title, results):
    """Escolhe o resultado do provedor cujo nome mais parece com o título
    do MAL — evita pegar cegamente results[0] (ex.: 'Tokyo Ghoul' x ':re')."""
    best, best_score = None, -1
    for r in results:
        score = fuzz.WRatio(title.lower(), r.name.lower())
        if score > best_score:
            best, best_score = r, score
    return best


def _stream_type(url):
    return "hls" if ".m3u8" in url.lower() else "mp4"


def resolve_stream(title, episode, lang="sub"):
    """Resolve o link de vídeo de UM episódio, sob demanda.

    title: título vindo do MAL.
    episode: número do episódio escolhido pelo usuário.
    lang: "sub" ou "dub".
    Retorna dict com a URL do melhor stream, ou None se não houver.
    """
    key = (title, int(episode), lang)
    cached = _cache.get(key)
    if cached and cached[1] > time.time():
        return cached[0]

    lang_enum = LanguageTypeEnum.DUB if lang == "dub" else LanguageTypeEnum.SUB

    results = with_retry(_provider.get_search, title)
    if not results:
        return None

    anime = _best_match(title, results)

    streams = with_retry(
        _provider.get_video, anime.identifier, episode, lang_enum
    )
    if not streams:
        return None

    best = max(streams, key=lambda s: s.resolution)
    result = {
        "url": best.url,
        "resolution": best.resolution,
        "type": _stream_type(best.url),
        "referrer": best.referrer,
        "provider_title": anime.name,
    }
    _cache[key] = (result, time.time() + CACHE_TTL)
    return result


if __name__ == "__main__":
    # smoke test rápido: resolve só 1 episódio
    import json
    print(json.dumps(resolve_stream("Naruto", 1), indent=2))
