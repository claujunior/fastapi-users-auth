import time
import unicodedata

from rapidfuzz import fuzz

from anipy_api.provider.providers import AllAnimeProvider
from anipy_api.provider import LanguageTypeEnum
from anipy_api.provider.base import ProviderInfoResult

MAX_ATTEMPTS = 4
BASE_DELAY = 1.0
CACHE_TTL = 1800
MIN_RATIO = 70

SEQUEL_MARKERS = (
    "√a", ":re", "2nd", "3rd", "season", "movie", "film", "ova", "ona",
    "special", "part", "final", "kanketsu", "recap",
)


class _SafeAllAnimeProvider(AllAnimeProvider):
    # AllAnime às vezes devolve "show": null e o get_info estoura; devolvemos
    # info vazia nesse caso e deixamos erros de rede subirem pro with_retry.
    def get_info(self, identifier):
        try:
            return super().get_info(identifier)
        except (AttributeError, KeyError, TypeError):
            return ProviderInfoResult()


_provider = _SafeAllAnimeProvider(base_url_override=None)

_resolve_cache = {}
_eps_cache = {}
_cache = {}


def with_retry(fn, *args, attempts=MAX_ATTEMPTS, base_delay=BASE_DELAY):
    for attempt in range(1, attempts + 1):
        try:
            return fn(*args)
        except Exception:
            if attempt == attempts:
                raise
            time.sleep(base_delay * (2 ** (attempt - 1)))


def _stream_type(url):
    return "hls" if ".m3u8" in url.lower() else "mp4"


def _normalize(s):
    return " ".join(unicodedata.normalize("NFKC", s).lower().split())


def _raw_titles(detail):
    titles = {detail["title"]}
    alt = detail.get("alternative_titles") or {}
    for k in ("en", "ja"):
        if alt.get(k):
            titles.add(alt[k])
    titles |= set(alt.get("synonyms") or [])
    return {t for t in titles if t}


def _penalty(name, mal_joined):
    name_n = _normalize(name)
    return sum(25 for m in SEQUEL_MARKERS if m in name_n and m not in mal_joined)


def _candidate_ratio(result, mal_titles, penalty):
    name_n = _normalize(result.name)
    ratio = max((fuzz.token_sort_ratio(m, name_n) for m in mal_titles), default=0)

    # nome não bate: consulta os nomes alternativos do provider (resolve título
    # estilizado tipo Tokyo Ghoul e apelido tipo One Piece = "1P"). Pula isso se
    # o candidato já é um Special/etc (penalty>0), que não vai vencer mesmo.
    if ratio < 90 and penalty == 0:
        info = _provider.get_info(result.identifier)
        for alt in info.alternative_names or []:
            a = _normalize(alt)
            ratio = max(ratio, max((fuzz.token_sort_ratio(m, a) for m in mal_titles), default=0))
            if ratio >= 100:
                break
    return ratio


def _match(detail):
    mal_titles = {_normalize(t) for t in _raw_titles(detail)}
    mal_joined = " ".join(mal_titles)

    candidates = {}
    for q in _raw_titles(detail):
        for r in with_retry(_provider.get_search, q) or []:
            candidates.setdefault(r.identifier, r)

    best, best_score, best_ratio = None, -1, -1
    for r in candidates.values():
        penalty = _penalty(r.name, mal_joined)
        ratio = _candidate_ratio(r, mal_titles, penalty)
        score = ratio - penalty
        if score > best_score:
            best, best_score, best_ratio = r, score, ratio

    if best is None or best_ratio < MIN_RATIO:
        return (None, None)
    return (best.identifier, best.name)


def _resolve_anime(detail):
    mal_id = detail.get("id")
    cached = _resolve_cache.get(mal_id)
    if cached and cached[1] > time.time():
        return cached[0]

    result = _match(detail)
    _resolve_cache[mal_id] = (result, time.time() + CACHE_TTL)
    return result


def list_episodes(detail, lang="sub"):
    key = (detail.get("id"), lang)
    cached = _eps_cache.get(key)
    if cached and cached[1] > time.time():
        return cached[0]

    lang_enum = LanguageTypeEnum.DUB if lang == "dub" else LanguageTypeEnum.SUB

    identifier, provider_title = _resolve_anime(detail)
    if not identifier:
        return None

    eps = with_retry(_provider.get_episodes, identifier, lang_enum)
    result = {
        "episodes": sorted(int(e) for e in eps),
        "provider_title": provider_title,
    }
    _eps_cache[key] = (result, time.time() + CACHE_TTL)
    return result


def resolve_stream(detail, episode, lang="sub"):
    key = (detail.get("id"), int(episode), lang)
    cached = _cache.get(key)
    if cached and cached[1] > time.time():
        return cached[0]

    lang_enum = LanguageTypeEnum.DUB if lang == "dub" else LanguageTypeEnum.SUB

    identifier, provider_title = _resolve_anime(detail)
    if not identifier:
        return None

    streams = with_retry(_provider.get_video, identifier, episode, lang_enum)
    if not streams:
        return None

    best = max(streams, key=lambda s: s.resolution)
    result = {
        "url": best.url,
        "resolution": best.resolution,
        "type": _stream_type(best.url),
        "referrer": best.referrer,
        "provider_title": provider_title,
    }
    _cache[key] = (result, time.time() + CACHE_TTL)
    return result


if __name__ == "__main__":
    import json
    detail = {"id": 20, "title": "Naruto", "media_type": "tv"}
    print(json.dumps(resolve_stream(detail, 1), indent=2))
