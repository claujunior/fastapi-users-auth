import os
import time
import secrets
from urllib.parse import urlencode

from fastapi import HTTPException
from dotenv import load_dotenv
import httpx

from repositories.user_repository import (
    find_user_by_username,
    find_user_by_oauth_state,
    update_user,
)

load_dotenv()

CLIENT_ID = os.getenv("MAL_CLIENT_ID")
CLIENT_SECRET = os.getenv("MAL_CLIENT_SECRET")
REDIRECT_URI = os.getenv("MAL_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5500")

OAUTH_BASE = "https://myanimelist.net/v1/oauth2"
API_BASE = "https://api.myanimelist.net/v2"


async def build_authorize_url(username):
    verifier = secrets.token_urlsafe(64)
    state = secrets.token_urlsafe(16)

    await update_user(username, {
        "mal_oauth_verifier": verifier,
        "mal_oauth_state": state,
    })

    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "code_challenge": verifier,
        "code_challenge_method": "plain",
        "state": state,
        "redirect_uri": REDIRECT_URI,
    }
    return f"{OAUTH_BASE}/authorize?{urlencode(params)}"


async def handle_callback(code, state):
    user = await find_user_by_oauth_state(state)
    if not user:
        raise HTTPException(status_code=400, detail="State inválido")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{OAUTH_BASE}/token",
            data={
                "grant_type": "authorization_code",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
                "code_verifier": user["mal_oauth_verifier"],
                "redirect_uri": REDIRECT_URI,
            },
        )

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Falha ao autenticar com o MAL")

    await _save_tokens(user["username"], response.json())
    return FRONTEND_URL


async def connection_status(username):
    user = await find_user_by_username(username)
    if not user.get("mal_access_token"):
        return {"connected": False}

    result = {
        "connected": True,
        "mal_username": user.get("mal_username"),
        "mal_picture": user.get("mal_picture"),
        "mal_statistics": None,
    }

    try:
        token = await _valid_token(username)
        profile = await _fetch_mal_profile(token)
        if profile:
            result["mal_username"] = profile.get("name") or result["mal_username"]
            result["mal_picture"] = profile.get("picture") or result["mal_picture"]
            result["mal_statistics"] = profile.get("anime_statistics")
    except Exception:
        pass

    return result


async def disconnect(username):
    await update_user(username, {
        "mal_access_token": None,
        "mal_refresh_token": None,
        "mal_token_expires_at": None,
        "mal_username": None,
        "mal_picture": None,
    })
    return {"connected": False}


async def get_animelist(username, status=None):
    token = await _valid_token(username)

    params = {
        "fields": "list_status,num_episodes,main_picture,mean",
        "limit": 1000,
        "nsfw": "true",
        "sort": "list_updated_at",
    }
    if status:
        params["status"] = status

    todos = []
    url = f"{API_BASE}/users/@me/animelist"
    async with httpx.AsyncClient() as client:
        while url:
            response = await client.get(url, headers=_bearer(token), params=params)
            data = response.json()
            todos.extend(data.get("data", []))
            url = data.get("paging", {}).get("next")
            params = None

    return {"data": todos}


async def update_list(username, anime_id, body):
    token = await _valid_token(username)
    payload = {k: v for k, v in body.items() if v is not None}

    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{API_BASE}/anime/{anime_id}/my_list_status",
            headers=_bearer(token),
            data=payload,
        )

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Falha ao atualizar a lista")
    return response.json()


async def remove_from_list(username, anime_id):
    token = await _valid_token(username)

    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{API_BASE}/anime/{anime_id}/my_list_status",
            headers=_bearer(token),
        )

    if response.status_code not in (200, 404):
        raise HTTPException(status_code=response.status_code, detail="Falha ao remover da lista")
    return {"removed": True}


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


async def _valid_token(username):
    user = await find_user_by_username(username)

    if not user.get("mal_access_token"):
        raise HTTPException(status_code=400, detail="Conta MAL não conectada")

    if user.get("mal_token_expires_at", 0) > time.time() + 60:
        return user["mal_access_token"]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{OAUTH_BASE}/token",
            data={
                "grant_type": "refresh_token",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": user["mal_refresh_token"],
            },
        )

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Sessão do MAL expirada, reconecte")

    tokens = response.json()
    await _save_tokens(username, tokens)
    return tokens["access_token"]


async def _save_tokens(username, tokens):
    fields = {
        "mal_access_token": tokens["access_token"],
        "mal_refresh_token": tokens["refresh_token"],
        "mal_token_expires_at": time.time() + tokens["expires_in"],
        "mal_oauth_verifier": None,
        "mal_oauth_state": None,
    }

    profile = await _fetch_mal_profile(tokens["access_token"])
    if profile:
        fields["mal_username"] = profile.get("name")
        fields["mal_picture"] = profile.get("picture")

    await update_user(username, fields)


async def _fetch_mal_profile(token):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE}/users/@me",
            headers=_bearer(token),
            params={"fields": "name,picture,anime_statistics"},
        )
    if response.status_code == 200:
        return response.json()
    return None

