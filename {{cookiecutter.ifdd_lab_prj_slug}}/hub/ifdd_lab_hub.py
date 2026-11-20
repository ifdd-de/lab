"""Configuration of the IFDD lab hub (JupyterHub with DockerSpawner).

jupyterhub_config.py calls configure(c). Every value comes from the
environment, which the compose file fills from the template variables and
.env, so this file is the same in every instance and can be tested on its own
(tests/test_hub_config.py).

Login: OIDC with Keycloak (GenericOAuthenticator, code flow with PKCE). Only
members of IFDD_LAB_USERS_GROUP log in, members of IFDD_LAB_ADMINS_GROUP are
hub admins. The tokens of the login stay in the encrypted auth state of the
user; the hub renews them with the refresh token (refresh_user_hook).

Delegation: the server of a user gets an API token that may read the auth
state of that user only (admin:auth_state!user). The helper ifdd_lab in the
images reads the current access token with it, so a notebook calls ifdd-be
with the rights of the person who is logged in.
"""

import base64
import json
import os
import random
import sys
import time

from dockerspawner import DockerSpawner

# An access token with less time left than this is renewed before the hub
# hands it out; the helper in the notebook gets at least this much.
REFRESH_MARGIN = 300
# The hub checks the auth state of a user at most this often (seconds).
AUTH_REFRESH_AGE = 60
HOME = "/home/jovyan"


def env(name, default=None):
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"{name} is not set (docker-compose-production.yml, .env)")
    return value


def jwt_expiry(token):
    """The exp claim of a JWT access token, or None. Not verified: the hub
    only decides whether to renew; ifdd-be verifies the token."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return float(json.loads(base64.urlsafe_b64decode(payload))["exp"])
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        return None


async def refresh_user_hook(authenticator, user, auth_state):
    """Renew the access token shortly before it expires.

    OAuthenticator's own refresh_user renews only after the token has
    expired (oauthenticator 17.5.0), so a notebook could receive a token that
    is valid for a few seconds. Returns True while the token is fresh, the new
    auth model after a renewal, False when the user has to log in again (the
    Keycloak session ended), None to fall back to the default.
    """
    if not auth_state:
        return None
    expiry = jwt_expiry(auth_state.get("access_token"))
    if expiry is None:
        return None
    if expiry - time.time() > REFRESH_MARGIN:
        return True
    refresh_token = auth_state.get("refresh_token")
    if not refresh_token:
        return False
    params = authenticator.build_refresh_token_request_params(refresh_token)
    try:
        token_info = await authenticator.get_token_info(None, params)
    except Exception as error:  # noqa: BLE001 - any failure means: log in again
        authenticator.log.info(f"Refreshing the tokens of {user.name} failed ({error}); new login needed")
        return False
    token_info.setdefault("refresh_token", refresh_token)
    try:
        # Private in oauthenticator 17.5.0; pinned in hub/requirements.txt and
        # covered by tests/test_hub_config.py.
        return await authenticator._token_to_auth_model(token_info)
    except Exception as error:  # noqa: BLE001
        authenticator.log.error(f"Fresh tokens of {user.name} were not accepted ({error})")
        return False


# Ports of the user servers in the network namespace of the Docker-in-Docker
# daemon, which they share (dind mode).
PORTS = (30000, 59999)


class LabSpawner(DockerSpawner):
    """DockerSpawner with the two network set-ups of the template.

    dind: the user containers run in the Docker-in-Docker daemon with its
    network ("host" there), like the task containers of ifdd-de/wf: they
    resolve the names of the lab network through the daemon's resolver and
    reach the hub and the proxy. A user-defined network inside the daemon
    does not resolve those names (smoke test, docker:29.9.2-dind). Each
    server listens on a port of its own; the hub reaches it at
    IFDD_LAB_DIND_HOST:<port>.
    socket: the user containers run on the host's daemon in the lab network;
    with internet access they also join IFDD_LAB_EGRESS_NETWORK.
    """

    def _dind_host(self):
        return os.environ.get("IFDD_LAB_DIND_HOST", "")

    async def get_ip_and_port(self):
        if self._dind_host():
            return self._dind_host(), self.port
        return await super().get_ip_and_port()

    async def start(self):
        if self._dind_host():
            self.port = random.randint(*PORTS)
        result = await super().start()
        egress = os.environ.get("IFDD_LAB_EGRESS_NETWORK", "")
        if egress:
            await self.docker("connect_container_to_network", self.container_id, egress)
        return result


def images():
    """{name: tag} from IFDD_LAB_IMAGES, e.g. "default=ifdd-lab-default:local"."""
    result = {}
    for item in env("IFDD_LAB_IMAGES").split(","):
        name, _, tag = item.partition("=")
        if not name or not tag:
            raise RuntimeError(f"IFDD_LAB_IMAGES: expected name=tag, got {item!r}")
        result[name] = tag
    return result


def configure(c):
    realm = env("IFDD_OIDC_REALM").rstrip("/")
    endpoint = realm + "/protocol/openid-connect"
    host = env("IFDD_LAB_HOST")
    client_id = env("IFDD_LAB_CLIENT_ID")
    slug = env("IFDD_LAB_SLUG")
    dind_host = os.environ.get("IFDD_LAB_DIND_HOST", "")

    # Hub and its proxy (configurable-http-proxy in this container). Traefik
    # routes to port 8000; the servers of the users call the hub API on 8081.
    c.JupyterHub.bind_url = "http://:8000"
    c.JupyterHub.hub_bind_url = "http://0.0.0.0:8081"
    c.JupyterHub.hub_connect_url = f"http://{env('IFDD_LAB_HUB_HOST')}:8081"
    c.JupyterHub.db_url = f"postgresql+psycopg://jupyterhub:{env('IFDD_LAB_DB_PASSWORD')}@postgres:5432/jupyterhub"
    c.JupyterHub.allow_named_servers = False

    c.JupyterHub.authenticator_class = "generic-oauth"
    a = c.GenericOAuthenticator
    a.client_id = client_id
    with open(env("IFDD_LAB_CLIENT_SECRET_FILE")) as handle:
        a.client_secret = handle.read().strip()
    a.oauth_callback_url = f"https://{host}/hub/oauth_callback"
    a.authorize_url = endpoint + "/auth"
    a.token_url = endpoint + "/token"
    a.userdata_url = endpoint + "/userinfo"
    a.logout_redirect_url = (f"{endpoint}/logout?client_id={client_id}"
                             f"&post_logout_redirect_uri=https://{host}/hub/")
    a.scope = ["openid", "profile", "email"]
    a.username_claim = "preferred_username"
    a.enable_pkce = True
    a.manage_groups = True
    a.auth_state_groups_key = "oauth_user.groups"
    a.allowed_groups = {env("IFDD_LAB_USERS_GROUP")}
    a.admin_groups = {env("IFDD_LAB_ADMINS_GROUP")}
    a.enable_auth_state = True                    # key: JUPYTERHUB_CRYPT_KEY
    a.auth_refresh_age = AUTH_REFRESH_AGE
    a.refresh_user_hook = refresh_user_hook

    c.JupyterHub.load_roles = [
        # Every user may read the own auth state (the tokens of the login).
        {"name": "user", "scopes": ["self", "admin:auth_state!user"]},
        {"name": "idle-culler", "services": ["idle-culler"],
         "scopes": ["list:users", "read:users:activity", "read:servers", "delete:servers"]},
    ]
    # The API token of a server: what the default role "server" grants plus
    # reading the user (and its auth state) - always the own user only.
    c.Spawner.server_token_scopes = [
        "users:activity!user", "access:servers!server", "read:users!user", "admin:auth_state!user",
    ]
    c.JupyterHub.services = [{
        "name": "idle-culler",
        "command": [sys.executable, "-m", "jupyterhub_idle_culler",
                    f"--timeout={int(env('IFDD_LAB_IDLE_TIMEOUT'))}"],
    }]

    c.JupyterHub.spawner_class = LabSpawner
    s = c.DockerSpawner
    offered = images()
    s.allowed_images = offered
    # The first image is the default: DockerSpawner uses it when there is no
    # choice (one image, or a start through the API without options).
    s.image = next(iter(offered.values()))
    s.pull_policy = "never"                       # local images only (adm_01_build.sh)
    s.remove = True                               # the home volume stays
    s.prefix = slug
    s.volumes = {f"{slug}-home-{{username}}": HOME}
    s.notebook_dir = HOME
    s.network_name = env("IFDD_LAB_SPAWN_NETWORK")       # "host" in dind mode
    # No published ports: in dind mode get_ip_and_port names the daemon (and
    # port bindings are invalid with the network "host"), in socket mode the
    # hub reaches the container in the lab network.
    s.use_internal_ip = True
    # No raw sockets (no sniffing or spoofing in a shared network), no gain
    # of privileges.
    s.extra_host_config = {"cap_drop": ["NET_RAW"], "security_opt": ["no-new-privileges:true"]}
    s.mem_limit = env("IFDD_LAB_MEM_LIMIT")
    s.cpu_limit = float(env("IFDD_LAB_CPU_LIMIT"))
    s.environment = {
        "IFDD_BE_URL": env("IFDD_BE_URL"),
        "IFDD_OIDC_REALM": realm,
    }
    c.Spawner.default_url = "/lab"
