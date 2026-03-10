"""Twitch stream -ilmoitukset: pollaa API ja lähettää viestin kun streameri aloittaa striimin."""
import os
import time
import requests

TWITCH_API = "https://api.twitch.tv/helix"
TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
_REQ_TIMEOUT = 15

_twitch_token = None
_twitch_token_expires = 0


def _get_twitch_token() -> str | None:
    """Hakee app access tokenin Twitch API:lle."""
    global _twitch_token, _twitch_token_expires
    client_id = os.getenv("TWITCH_CLIENT_ID", "").strip()
    client_secret = os.getenv("TWITCH_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        return None
    if _twitch_token and time.time() < _twitch_token_expires - 60:
        return _twitch_token
    r = requests.post(
        TWITCH_TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        },
        timeout=_REQ_TIMEOUT,
    )
    if r.status_code != 200:
        return None
    data = r.json()
    _twitch_token = data.get("access_token")
    _twitch_token_expires = time.time() + data.get("expires_in", 0)
    return _twitch_token


def fetch_live_streams(user_logins: list[str]) -> list[dict]:
    """Hakee Twitch API:sta mitkä user_logins ovat juuri nyt livessä. Palauttaa lista stream-objekteista."""
    if not user_logins:
        return []
    token = _get_twitch_token()
    if not token:
        return []
    client_id = os.getenv("TWITCH_CLIENT_ID", "").strip()
    headers = {
        "Authorization": f"Bearer {token}",
        "Client-Id": client_id,
    }
    logins = ",".join(user_logins[:100])
    r = requests.get(
        f"{TWITCH_API}/streams",
        params={"user_login": logins},
        headers=headers,
        timeout=_REQ_TIMEOUT,
    )
    if r.status_code != 200:
        return []
    data = r.json()
    return data.get("data") or []


def is_twitch_configured() -> bool:
    return bool(
        os.getenv("TWITCH_CLIENT_ID", "").strip()
        and os.getenv("TWITCH_CLIENT_SECRET", "").strip()
    )

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
