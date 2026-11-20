"""Call IFDD services from a notebook with the rights of the logged-in user.

    import ifdd_lab
    be = ifdd_lab.session()                 # requests.Session for ifdd-be
    r = be.get("/nodes/", params={"start": 0, "end": 10})

The hub keeps the tokens of the login. Each request asks the hub API for the
current access token of the user (the server's own JUPYTERHUB_API_TOKEN may
read the user's auth state and nothing else), so a notebook acts exactly with
the roles and context patterns of the person who logged in, and a long
running notebook keeps working while the hub renews the token.

Never print the token or write it into a notebook output: outputs are saved
with the notebook.
"""

import base64
import json
import os
import time
from urllib.parse import quote

import requests

__all__ = ["LoginRequired", "access_token", "session"]

# Ask the hub again when the cached token has less time left than this. The
# hub renews tokens with less than 300 s left (hub/ifdd_lab_hub.py).
MARGIN = 120
TIMEOUT = 30

_cache = {"token": None, "expiry": 0.0}


class LoginRequired(RuntimeError):
    """The hub has no valid tokens for the user: log in to the hub again."""


def _expiry(token):
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return float(json.loads(base64.urlsafe_b64decode(payload))["exp"])
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        return 0.0


def _fetch():
    api = os.environ.get("JUPYTERHUB_API_URL", "").rstrip("/")
    user = os.environ.get("JUPYTERHUB_USER", "")
    api_token = os.environ.get("JUPYTERHUB_API_TOKEN", "")
    if not (api and user and api_token):
        raise LoginRequired("not running in a server started by the IFDD lab hub "
                            "(JUPYTERHUB_API_URL, JUPYTERHUB_USER, JUPYTERHUB_API_TOKEN)")
    response = requests.get(f"{api}/users/{quote(user, safe='')}",
                            headers={"Authorization": f"token {api_token}"}, timeout=TIMEOUT)
    if response.status_code in (401, 403):
        raise LoginRequired(f"the hub refused the request ({response.status_code}); "
                            "log in to the hub again")
    response.raise_for_status()
    state = response.json().get("auth_state") or {}
    token = state.get("access_token")
    if not token:
        raise LoginRequired("the hub has no access token for this user; log in to the hub again")
    return token


def access_token():
    """The current OIDC access token of the logged-in user."""
    if _cache["token"] and _cache["expiry"] - time.time() > MARGIN:
        return _cache["token"]
    token = _fetch()
    _cache["token"], _cache["expiry"] = token, _expiry(token)
    return token


class _Session(requests.Session):
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url.rstrip("/")

    def request(self, method, url, *args, **kwargs):
        if not url.startswith(("http://", "https://")):
            url = self.base_url + "/" + url.lstrip("/")
        headers = dict(kwargs.pop("headers", None) or {})
        headers["Authorization"] = f"Bearer {access_token()}"
        kwargs.setdefault("timeout", TIMEOUT)
        return super().request(method, url, *args, headers=headers, **kwargs)


def session(base_url=None):
    """A requests.Session that sends the user's token with every request.

    Relative URLs are resolved against base_url, by default IFDD_BE_URL.
    """
    base = base_url or os.environ.get("IFDD_BE_URL", "")
    if not base:
        raise ValueError("no base URL: pass base_url or set IFDD_BE_URL")
    return _Session(base)
