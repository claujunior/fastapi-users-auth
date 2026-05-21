import os

from fastapi import HTTPException
import requests



MAL_CLIENT_ID = os.getenv("MAL_CLIENT_ID")
MAL_BASE_URL = "https://api.myanimelist.net/v2"
HEADERS = {"X-MAL-CLIENT-ID": "9d3de26134abfa6109b3e81d0cf3e3a7"}

async def animes_recente(page):
    response = requests.get(
        "https://api.myanimelist.net/v2/anime/season/2026/spring",
        headers=HEADERS,
        params={"limit": 7,
    "offset": (page - 1) * 7}
    )

    return response.json()
    

async def search_animes(search):
    response = requests.get(
        "https://api.myanimelist.net/v2/anime",
        headers=HEADERS,
        params={"limit": 5,
    "q": search}
    )

    return response.json()


async def search_id(id):
    response = requests.get(
         f"https://api.myanimelist.net/v2/anime/{id}?fields=title,main_picture,alternative_titles,start_date,end_date,synopsis,mean,rank,popularity,num_list_users,num_scoring_users,nsfw,created_at,updated_at,media_type,status,genres,my_list_status,num_episodes,start_season,broadcast,source,average_episode_duration,rating,pictures,background,related_anime,related_manga,recommendations,studios,statistics",
        headers=HEADERS,        
    )
    
    return response.json()