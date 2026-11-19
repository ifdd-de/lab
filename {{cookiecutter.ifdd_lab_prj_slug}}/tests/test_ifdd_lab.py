"""The helper lib/ifdd_lab.py against a stand-in of the hub API and ifdd-be."""

import base64
import importlib.util
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
API_TOKEN = "server-token"


def load_helper():
    spec = importlib.util.spec_from_file_location("ifdd_lab", ROOT / "lib" / "ifdd_lab.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def jwt(exp):
    def part(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")
    return f"{part({'alg': 'none'})}.{part({'exp': exp})}.sig"


class Stand(BaseHTTPRequestHandler):
    tokens = []          # the hub hands these out in order
    hub_calls = 0
    hub_status = 200
    seen = []            # (path, Authorization) of requests to the backend

    def log_message(self, *args):
        pass

    def reply(self, status, body, headers=None):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/hub/api/users/"):
            type(self).hub_calls += 1
            if self.headers.get("Authorization") != f"token {API_TOKEN}":
                return self.reply(403, {"message": "forbidden"})
            if self.path != "/hub/api/users/alice%40example.org":
                return self.reply(404, {"message": "no such user"})
            if type(self).hub_status != 200:
                return self.reply(type(self).hub_status, {"message": "refused"})
            token = type(self).tokens.pop(0) if len(type(self).tokens) > 1 else type(self).tokens[0]
            return self.reply(200, {"name": "alice@example.org", "auth_state": {"access_token": token}})
        type(self).seen.append((self.path, self.headers.get("Authorization")))
        return self.reply(200, [{"@id": "x"}], {"X-Total-Count": "1"})


@pytest.fixture
def stand(monkeypatch):
    Stand.tokens, Stand.hub_calls, Stand.hub_status, Stand.seen = [jwt(time.time() + 1800)], 0, 200, []
    server = ThreadingHTTPServer(("127.0.0.1", 0), Stand)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    monkeypatch.setenv("JUPYTERHUB_API_URL", base + "/hub/api")
    monkeypatch.setenv("JUPYTERHUB_USER", "alice@example.org")
    monkeypatch.setenv("JUPYTERHUB_API_TOKEN", API_TOKEN)
    monkeypatch.setenv("IFDD_BE_URL", base + "/be")
    yield base
    server.shutdown()


def test_session_sends_the_users_token_to_relative_urls(stand):
    lab = load_helper()
    response = lab.session().get("/nodes/", params={"start": 0, "end": 5})
    assert response.headers["X-Total-Count"] == "1"
    assert Stand.seen == [("/be/nodes/?start=0&end=5", f"Bearer {Stand.tokens[0]}")]


def test_absolute_urls_are_kept(stand):
    lab = load_helper()
    lab.session().get(stand + "/other/path")
    assert Stand.seen[0][0] == "/other/path"


def test_a_fresh_token_is_reused(stand):
    lab = load_helper()
    s = lab.session()
    s.get("/a")
    s.get("/b")
    assert Stand.hub_calls == 1


def test_a_token_about_to_expire_is_fetched_again(stand):
    soon, later = jwt(time.time() + 30), jwt(time.time() + 1800)
    Stand.tokens = [soon, later]
    lab = load_helper()
    assert lab.access_token() == soon
    assert lab.access_token() == later
    assert Stand.hub_calls == 2


@pytest.mark.parametrize("status", [401, 403])
def test_refusal_of_the_hub_asks_for_a_new_login(stand, status):
    Stand.hub_status = status
    lab = load_helper()
    with pytest.raises(lab.LoginRequired, match="log in to the hub again"):
        lab.access_token()


def test_outside_a_hub_server(monkeypatch):
    for name in ("JUPYTERHUB_API_URL", "JUPYTERHUB_USER", "JUPYTERHUB_API_TOKEN"):
        monkeypatch.delenv(name, raising=False)
    lab = load_helper()
    with pytest.raises(lab.LoginRequired, match="not running in a server"):
        lab.access_token()


def test_session_needs_a_base_url(monkeypatch):
    monkeypatch.delenv("IFDD_BE_URL", raising=False)
    lab = load_helper()
    with pytest.raises(ValueError):
        lab.session()
