(ifdd-lab-setup)=
# Setup
{%- set dind = cookiecutter.ifdd_lab_docker_mode == "dind" %}
{%- set internet = cookiecutter.ifdd_lab_internet == "y" %}

## Prerequisites

| What | Why |
|---|---|
| Docker with Compose | hub, PostgreSQL{% if dind %}, the Docker-in-Docker daemon{% endif %} and the user servers run as containers; the images are built locally |
| a few GB of free disk space per image | the images of the user servers are based on `{{ cookiecutter.ifdd_lab_kernel_base_image }}`, which contains LaTeX{% if dind %}; with Docker-in-Docker every image is stored twice (on the host and in the daemon){% endif %} |
| a running proxy instance that joins the network `{{ cookiecutter.ifdd_lab_network }}` with its host aliases | Traefik routes `IFDD_LAB_HOST` to the hub; the hub and the user servers reach Keycloak and ifdd-be through it |
| the Keycloak client `{{ cookiecutter.ifdd_keycloak_lab_client_id }}` with the redirect URI `https://<IFDD_LAB_HOST>/hub/oauth_callback` and the groups `{{ cookiecutter.ifdd_keycloak_lab_users_group }}` and `{{ cookiecutter.ifdd_keycloak_lab_admins_group }}` | login; `ifdd-de/keycloak` creates them in a new realm |
| the CA certificate of the proxy, if it uses a CA of its own | it is built into every image |

## Create the instance

Usually `ifdd-meta create` creates every instance of an installation: it
runs `cruft create` with the variable file of the installation, copies the
local CA of the proxy into `certs/` and the client secret into
`secrets/oidc_client_secret`. By hand, from the directory that holds the
instances, with the skip list this template recommends:

```bash
cruft create --no-input --config-file cookiecutter_all.yaml \
  --skip .env --skip secrets --skip certs --skip hub/config.d \
  https://github.com/ifdd-de/lab
cp proxy/certs/ca.crt {{ cookiecutter.ifdd_lab_prj_slug }}/certs/
```

## Configuration and secrets

The hook of the template writes `.env` (mode 0600) with a database password,
the key of the encrypted auth state and the cookie secret. The client secret
comes from the `.env` of the keycloak instance
(`IFDD_KEYCLOAK_LAB_CLIENT_SECRET`):

```bash
cd {{ cookiecutter.ifdd_lab_prj_slug }}
umask 077
grep '^IFDD_KEYCLOAK_LAB_CLIENT_SECRET=' ../keycloak/.env | cut -d= -f2- > secrets/oidc_client_secret
```

## The lab network

The hub{% if dind %} and the Docker-in-Docker daemon{% endif %} sit in the
network `{{ cookiecutter.ifdd_lab_network }}`. It is internal, so nothing in
it has a route outside, and it is shared with the proxy, so no compose
project owns it. Create it once:

```bash
docker network create --internal {{ cookiecutter.ifdd_lab_network }}
```

The proxy instance must join it with the same host aliases as the shared
proxy network (variable `ifdd_proxy_extra_networks` of `ifdd-de/proxy`);
otherwise Traefik cannot route to the hub and the user servers cannot reach
`ifdd-be` and Keycloak. `adm_02_run.sh` refuses to start when the network is
missing or not internal.
{%- if internet %}

With internet access the {% if dind %}Docker-in-Docker daemon{% else %}user servers and the hub{% endif %} also join
the network `{{ cookiecutter.ifdd_lab_prj_slug }}-egress`, which compose
creates.
{%- endif %}

## First start

```bash
./adm_01_build.sh
./adm_02_run.sh
```

Then open `https://<IFDD_LAB_HOST>/` and log in at Keycloak. A member of
`{{ cookiecutter.ifdd_keycloak_lab_users_group }}` gets JupyterLab; anybody
else gets a page "403: Forbidden" from the hub.

## Several servers

When Keycloak or ifdd-be run on another server, their host names must
resolve to that server's proxy and its CA must be in `certs/`. The redirect
URI of the client names the host of this hub. The values come from the
variable file of the installation (`ifdd_oidc_realm`, `ifdd_be_url`).
