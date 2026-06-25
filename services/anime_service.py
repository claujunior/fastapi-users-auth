import os

from dotenv import load_dotenv
import httpx
from rapidfuzz import fuzz

load_dotenv()

MAL_BASE_URL = "https://api.myanimelist.net/v2"
HEADERS = {"X-MAL-CLIENT-ID": os.getenv("MAL_CLIENT_ID")}

DETAIL_FIELDS = (
    "title,main_picture,alternative_titles,start_date,end_date,synopsis,mean,"
    "rank,popularity,num_list_users,num_scoring_users,nsfw,created_at,updated_at,"
    "media_type,status,genres,my_list_status,num_episodes,start_season,broadcast,"
    "source,average_episode_duration,rating,pictures,background,related_anime,"
    "related_manga,recommendations,studios,statistics"
)


def _nsfw(flag):
    return "true" if flag else "false"


_RATINGS_NSFW = {"r+", "rx"}
_GENEROS_NSFW = {"ecchi", "erotica", "hentai"}


def _is_safe(node):
    if (node.get("rating") or "") in _RATINGS_NSFW:
        return False
    generos = {g.get("name", "").lower() for g in node.get("genres") or []}
    return not (generos & _GENEROS_NSFW)


def _filtra_nsfw(itens, nsfw):
    if nsfw:
        return itens
    return [i for i in itens if _is_safe(i.get("node") or {})]


async def animes_recente(page, nsfw=True):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MAL_BASE_URL}/anime/season/2026/spring",
            headers=HEADERS,
            params={
                "limit": 7,
                "offset": (page - 1) * 7,
                "fields": "rating,genres",
                "nsfw": _nsfw(nsfw),
            },
        )
    data = response.json()
    data["data"] = _filtra_nsfw(data.get("data", []), nsfw)
    return data


def _norm(s):
    return " ".join(s.lower().split())


def _relevancia(query, node):
    q = _norm(query)
    alt = node.get("alternative_titles") or {}
    titulo = node.get("title", "")
    en = alt.get("en", "")

    if (titulo and _norm(titulo) == q) or (en and _norm(en) == q):
        return 130

    titulos = [titulo, en, alt.get("ja", ""), *(alt.get("synonyms") or [])]
    return max((fuzz.WRatio(q, _norm(t)) for t in titulos if t), default=0)


async def search_animes(search, nsfw=True):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MAL_BASE_URL}/anime",
            headers=HEADERS,
            params={
                "limit": 20,
                "q": search,
                "fields": "alternative_titles,num_list_users,mean,media_type,start_season,rating,genres",
                "nsfw": _nsfw(nsfw),
            },
        )

    data = response.json()
    resultados = _filtra_nsfw(data.get("data", []), nsfw)

    def score(item):
        node = item["node"]
        relevancia = _relevancia(search, node)
        popularidade = min(node.get("num_list_users", 0) / 50000, 1.0) * 10
        return relevancia + popularidade

    resultados.sort(key=score, reverse=True)
    data["data"] = resultados[:8]
    return data


async def search_id(id):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MAL_BASE_URL}/anime/{id}",
            headers=HEADERS,
            params={"fields": DETAIL_FIELDS},
        )
    return response.json()

async def topanimes(nsfw=True):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MAL_BASE_URL}/anime/ranking",
            headers=HEADERS,
            params={"ranking_type": "all", "limit": 14, "fields": "rating,genres", "nsfw": _nsfw(nsfw)},
        )
    data = response.json()
    data["data"] = _filtra_nsfw(data.get("data", []), nsfw)
    return data