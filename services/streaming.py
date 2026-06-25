import time
import unicodedata

from rapidfuzz import fuzz

from anipy_api.provider.providers import AllAnimeProvider
from anipy_api.provider import LanguageTypeEnum

# Letras unicode estilizadas -> ASCII (alguns títulos do AllAnime usam).
_FANCY_RANGES = [
    (0x1F170, 0x1F189, ord("A")),  # negative squared latin A-Z
    (0x1F130, 0x1F149, ord("A")),  # squared latin A-Z
    (0x24B6, 0x24CF, ord("A")),    # circled capital A-Z
    (0x24D0, 0x24E9, ord("a")),    # circled small a-z
    (0xFF21, 0xFF3A, ord("A")),    # fullwidth A-Z
    (0xFF41, 0xFF5A, ord("a")),    # fullwidth a-z
]

_SEQUEL_MARKERS = (
    "√a", ":re", "2nd", "3rd", "season", "movie", "film",
    "ova", "ona", "special", "part", "final", "kanketsu",
)


def _defancy_char(ch):
    cp = ord(ch)
    for start, end, base in _FANCY_RANGES:
        if start <= cp <= end:
            return chr(base + (cp - start))
    return ch


def _normalize(s):
    s = "".join(_defancy_char(c) for c in s)
    s = unicodedata.normalize("NFKC", s)
    return " ".join(s.lower().split())


MAX_ATTEMPTS = 4
BASE_DELAY = 1.0
CACHE_TTL = 1800

_provider = AllAnimeProvider(base_url_override=None)

_cache = {}
_eps_cache = {}

# Override MAL id -> identifier do AllAnime, quando o search não casa por nome.
MAL_TO_ALLANIME = {
    21: "ReooPAxPMsHM4KPMY",   # One Piece ("1P")
}


def with_retry(fn, *args, attempts=MAX_ATTEMPTS, base_delay=BASE_DELAY):
    for attempt in range(1, attempts + 1):
        try:
            return fn(*args)
        except Exception:
            if attempt == attempts:
                raise
            time.sleep(base_delay * (2 ** (attempt - 1)))


def _best_match(title, results):
    alvo = _normalize(title)

    exatos = [r for r in results if _normalize(r.name) == alvo]
    if exatos:
        return exatos[0]

    best, best_score = None, -1.0
    for r in results:
        nome = _normalize(r.name)
        score = fuzz.token_sort_ratio(alvo, nome)
        penalidade = sum(
            25 for m in _SEQUEL_MARKERS if m in nome and m not in alvo
        )
        score -= penalidade
        if score > best_score:
            best, best_score = r, score
    return best


def _stream_type(url):
    return "hls" if ".m3u8" in url.lower() else "mp4"


def _resolve_identifier(title, mal_id):
    override = MAL_TO_ALLANIME.get(mal_id)
    if override:
        return override, title

    results = with_retry(_provider.get_search, title)
    if not results:
        return None, None
    anime = _best_match(title, results)
    return anime.identifier, anime.name


def list_episodes(title, lang="sub", mal_id=None):
    key = (mal_id, title, lang)
    cached = _eps_cache.get(key)
    if cached and cached[1] > time.time():
        return cached[0]

    lang_enum = LanguageTypeEnum.DUB if lang == "dub" else LanguageTypeEnum.SUB

    identifier, provider_title = _resolve_identifier(title, mal_id)
    if not identifier:
        return None

    eps = with_retry(_provider.get_episodes, identifier, lang_enum)
    result = {
        "episodes": sorted(int(e) for e in eps),
        "provider_title": provider_title,
    }
    _eps_cache[key] = (result, time.time() + CACHE_TTL)
    return result


def resolve_stream(title, episode, lang="sub", mal_id=None):
    key = (mal_id, title, int(episode), lang)
    cached = _cache.get(key)
    if cached and cached[1] > time.time():
        return cached[0]

    lang_enum = LanguageTypeEnum.DUB if lang == "dub" else LanguageTypeEnum.SUB

    identifier, provider_title = _resolve_identifier(title, mal_id)
    if not identifier:
        return None

    streams = with_retry(
        _provider.get_video, identifier, episode, lang_enum
    )
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
    print(json.dumps(resolve_stream("Naruto", 1), indent=2))
