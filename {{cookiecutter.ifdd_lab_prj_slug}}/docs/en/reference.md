(ifdd-lab-reference)=
# Reference
{%- set dind = cookiecutter.ifdd_lab_docker_mode == "dind" %}

The variables of the template and their values in this instance are listed
in {ref}`ifdd-instances-lab`. This page lists what is not a template
variable.

## Layout

| Path | Content |
|---|---|
| `docker-compose-production.yml` | PostgreSQL, {% if dind %}Docker-in-Docker, {% endif %}hub, and the image builds (profile `images`) |
| `hub/` | hub image; `jupyterhub_config.py` loads `ifdd_lab_hub.py` (settings from the environment) and `config.d/*.py` |
| `hub/config.d/` | local additions to the hub configuration (git-ignored, skip list) |
{%- if dind %}
| `dind/` | Docker-in-Docker image |
{%- endif %}
| `images/<name>/` | images of the user servers; `default` comes from the template |
| `lib/ifdd_lab.py` | helper in every image: the user's token for IFDD services |
| `build/install-certs.sh` | adds `certs/*` to the trust store of every image |
| `certs/` | internal CA certificates (git-ignored) |
| `secrets/oidc_client_secret` | client secret (git-ignored) |
| `.env` | host, generated passwords and keys (git-ignored) |
| `examples/notebooks/` | example notebook |
| `adm_01_build.sh`, `adm_02_run.sh`, `adm_99_destroy.sh` | build; check and start; delete everything |

## Environment (`.env`)

| Variable | Default here | Meaning |
|---|---|---|
| `IFDD_LAB_HOST` | `{{ cookiecutter.ifdd_lab_host }}` | host the proxy routes to the hub |
| `IFDD_LAB_DB_PASSWORD` | generated | set once |
| `JUPYTERHUB_CRYPT_KEY` | generated | key of the stored tokens; a new key forces every user to log in again |
| `JPY_COOKIE_SECRET` | generated | secret of the login cookies |

## Environment of the user servers

| Variable | Value |
|---|---|
| `IFDD_BE_URL` | `{{ cookiecutter.ifdd_be_url }}` (base URL of `ifdd_lab.session()`) |
| `IFDD_OIDC_REALM` | `{{ cookiecutter.ifdd_oidc_realm }}` |
| `JUPYTERHUB_API_URL`, `JUPYTERHUB_API_TOKEN`, `JUPYTERHUB_USER` | set by the hub; `ifdd_lab` reads the token with them |

## Hub settings

| Setting | Value |
|---|---|
| renewal of the access token | when less than 300 s are left (`ifdd_lab_hub.REFRESH_MARGIN`) |
| check of the auth state | at most every 60 s per user |
| scopes of the API token of a server | `users:activity!user`, `access:servers!server`, `read:users!user`, `admin:auth_state!user` |
| URL after login | `/lab` |
