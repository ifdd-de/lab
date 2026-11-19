"""hub/ifdd_lab_hub.py with the pinned packages of hub/requirements.txt.

Needs jupyterhub, oauthenticator and dockerspawner (pip install -r
hub/requirements.txt); skipped without them. No Docker, no Keycloak: a
stand-in serves the token and userinfo endpoints.
"""

import asyncio
import base64
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

import pytest

pytest.importorskip("jupyterhub")
pytest.importorskip("oauthenticator")
pytest.importorskip("dockerspawner")

from traitlets.config import Config  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "hub"))
import ifdd_lab_hub  # noqa: E402
from oauthenticator.generic import GenericOAuthenticator  # noqa: E402


def jwt(exp, **claims):
    def part(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")
    return f"{part({'alg': 'none'})}.{part({'exp': exp, **claims})}.sig"


ENV = {
    "IFDD_OIDC_REALM": "https://id.example.org/realms/ifdd",
    "IFDD_LAB_HOST": "lab.example.org",
    "IFDD_LAB_HUB_HOST": "ifdd-lab-hub",
    "IFDD_LAB_SLUG": "ifdd-lab",
    "IFDD_LAB_DB_PASSWORD": "Secret123",
    "IFDD_LAB_CLIENT_ID": "ifdd-lab",
    "IFDD_LAB_USERS_GROUP": "ifdd_lab_users",
    "IFDD_LAB_ADMINS_GROUP": "ifdd_lab_admins",
    "IFDD_LAB_IMAGES": "default=ifdd-lab-default:local,gis=ifdd-lab-gis:local",
    "IFDD_LAB_MEM_LIMIT": "2G",
    "IFDD_LAB_CPU_LIMIT": "1.5",
    "IFDD_LAB_IDLE_TIMEOUT": "3600",
    "IFDD_BE_URL": "https://rest.example.org",
    "IFDD_LAB_SPAWN_NETWORK": "host",
    "IFDD_LAB_DIND_HOST": "ifdd-lab-dind",
}


@pytest.fixture
def config(monkeypatch, tmp_path):
    secret = tmp_path / "oidc_client_secret"
    secret.write_text("client-secret\n")
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("IFDD_LAB_CLIENT_SECRET_FILE", str(secret))
    c = Config()
    ifdd_lab_hub.configure(c)
    return c


def test_login(config):
    a = GenericOAuthenticator(config=config)
    assert a.client_secret == "client-secret"
    assert a.token_url == "https://id.example.org/realms/ifdd/protocol/openid-connect/token"
    assert a.oauth_callback_url == "https://lab.example.org/hub/oauth_callback"
    assert a.enable_pkce is True
    assert a.manage_groups is True
    assert a.allowed_groups == {"ifdd_lab_users"} and a.admin_groups == {"ifdd_lab_admins"}
    assert a.enable_auth_state is True
    assert a.refresh_user_hook is ifdd_lab_hub.refresh_user_hook


def test_server_token_reads_only_the_own_auth_state(config):
    scopes = config.Spawner.server_token_scopes
    assert "admin:auth_state!user" in scopes
    assert not [s for s in scopes if "!" not in s], "every scope of the server token is limited"
    user_role = next(r for r in config.JupyterHub.load_roles if r["name"] == "user")
    assert user_role["scopes"] == ["self", "admin:auth_state!user"]


def test_spawner(config):
    s = config.DockerSpawner
    assert s.allowed_images == {"default": "ifdd-lab-default:local", "gis": "ifdd-lab-gis:local"}
    assert s.image == "ifdd-lab-default:local"      # not the upstream default singleuser image
    assert s.pull_policy == "never"
    assert s.remove is True
    assert s.volumes == {"ifdd-lab-home-{username}": "/home/jovyan"}
    assert s.network_name == "host" and s.use_internal_ip is True   # no port bindings
    assert s.extra_host_config == {"cap_drop": ["NET_RAW"], "security_opt": ["no-new-privileges:true"]}
    assert s.environment == {"IFDD_BE_URL": "https://rest.example.org",
                             "IFDD_OIDC_REALM": "https://id.example.org/realms/ifdd"}
    assert config.JupyterHub.spawner_class is ifdd_lab_hub.LabSpawner
    assert config.JupyterHub.allow_named_servers is False


def test_socket_mode_uses_the_internal_ip(monkeypatch, tmp_path):
    secret = tmp_path / "s"
    secret.write_text("x")
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("IFDD_LAB_DIND_HOST")
    monkeypatch.setenv("IFDD_LAB_SPAWN_NETWORK", "lab-net")
    monkeypatch.setenv("IFDD_LAB_CLIENT_SECRET_FILE", str(secret))
    c = Config()
    ifdd_lab_hub.configure(c)
    assert c.DockerSpawner.use_internal_ip is True
    assert c.DockerSpawner.network_name == "lab-net"


def test_dind_servers_are_reached_through_the_daemon(config):
    """dind: the servers share the daemon's network; the hub reaches each at
    IFDD_LAB_DIND_HOST and its own port, without asking Docker."""
    spawner = ifdd_lab_hub.LabSpawner.__new__(ifdd_lab_hub.LabSpawner)
    spawner.port = 31234
    assert run(spawner.get_ip_and_port()) == ("ifdd-lab-dind", 31234)
    low, high = ifdd_lab_hub.PORTS
    assert 1024 < low < high <= 65535


def test_idle_culler(config):
    service = config.JupyterHub.services[0]
    assert service["name"] == "idle-culler"
    assert "--timeout=3600" in service["command"]


def test_missing_value_is_named(monkeypatch):
    monkeypatch.delenv("IFDD_OIDC_REALM", raising=False)
    with pytest.raises(RuntimeError, match="IFDD_OIDC_REALM"):
        ifdd_lab_hub.configure(Config())


class Provider(BaseHTTPRequestHandler):
    """Token and userinfo endpoints of a stand-in OIDC provider."""
    refreshed = []

    def log_message(self, *args):
        pass

    def reply(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        form = parse_qs(self.rfile.read(int(self.headers["Content-Length"])).decode())
        if form.get("grant_type") == ["refresh_token"] and form.get("refresh_token") == ["rt-1"]:
            type(self).refreshed.append(form["refresh_token"][0])
            return self.reply(200, {"access_token": jwt(time.time() + 1800), "refresh_token": "rt-2",
                                    "token_type": "Bearer", "expires_in": 1800})
        return self.reply(400, {"error": "invalid_grant"})

    def do_GET(self):
        return self.reply(200, {"preferred_username": "alice", "groups": ["ifdd_lab_users"]})


@pytest.fixture
def provider():
    Provider.refreshed = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def authenticator(config, provider):
    a = GenericOAuthenticator(config=config)
    a.token_url = provider + "/token"
    a.userdata_url = provider + "/userinfo"
    return a


class User:
    name = "alice"


def run(coro):
    return asyncio.run(coro)


def test_a_fresh_token_is_kept(config, provider):
    state = {"access_token": jwt(time.time() + 1800), "refresh_token": "rt-1"}
    assert run(ifdd_lab_hub.refresh_user_hook(authenticator(config, provider), User(), state)) is True
    assert Provider.refreshed == []


def test_a_token_about_to_expire_is_renewed(config, provider):
    old = jwt(time.time() + 60)
    state = {"access_token": old, "refresh_token": "rt-1"}
    model = run(ifdd_lab_hub.refresh_user_hook(authenticator(config, provider), User(), state))
    assert Provider.refreshed == ["rt-1"]
    assert model["name"] == "alice"
    assert model["auth_state"]["access_token"] != old
    assert model["auth_state"]["refresh_token"] == "rt-2"
    assert model["groups"] == ["ifdd_lab_users"]


def test_a_refused_refresh_asks_for_a_new_login(config, provider):
    state = {"access_token": jwt(time.time() + 10), "refresh_token": "used-already"}
    assert run(ifdd_lab_hub.refresh_user_hook(authenticator(config, provider), User(), state)) is False


def test_without_refresh_token_a_new_login_is_needed(config, provider):
    state = {"access_token": jwt(time.time() + 10)}
    assert run(ifdd_lab_hub.refresh_user_hook(authenticator(config, provider), User(), state)) is False


def test_without_auth_state_the_default_applies(config, provider):
    a = authenticator(config, provider)
    assert run(ifdd_lab_hub.refresh_user_hook(a, User(), None)) is None
    assert run(ifdd_lab_hub.refresh_user_hook(a, User(), {"access_token": "opaque"})) is None
