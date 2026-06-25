import os

from dotenv import load_dotenv
import httpx

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


async def animes_recente(page):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MAL_BASE_URL}/anime/season/2026/spring",
            headers=HEADERS,
            params={"limit": 7, "offset": (page - 1) * 7, "nsfw": "true"},
        )
    return response.json()


async def search_animes(search):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MAL_BASE_URL}/anime",
            headers=HEADERS,
            params={
                "limit": 20,
                "q": search,
                "fields": "num_list_users,mean,media_type,start_season",
                "nsfw": "true",
            },
        )

    data = response.json()
    resultados = data.get("data", [])
    resultados.sort(
        key=lambda n: n["node"].get("num_list_users", 0),
        reverse=True,
    )
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

async def topanimes():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MAL_BASE_URL}/anime/ranking",
            headers=HEADERS,
            params={"ranking_type": "all", "limit": 14, "nsfw": "true"},
        )
    return response.json()