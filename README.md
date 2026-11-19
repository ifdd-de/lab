# ifdd-de/lab

cookiecutter/cruft template for a notebook service: [JupyterHub](https://jupyterhub.readthedocs.io)
behind the IFDD proxy (`ifdd-de/proxy`) that starts one container per user
with [DockerSpawner](https://github.com/jupyterhub/dockerspawner), in an own
Docker-in-Docker daemon or on the host socket. Users log in at Keycloak
(`ifdd-de/keycloak`); a notebook calls the IFDD services with the rights of
the person logged in: the hub keeps the tokens of the login, renews them and
hands the current access token to the helper `ifdd_lab` in the image.

## Generate an instance

```bash
cruft create --no-input --checkout <tag> \
  --config-file cookiecutter_all.yaml \
  --skip .env --skip secrets --skip certs --skip hub/config.d \
  --output-dir ../instances https://github.com/ifdd-de/lab
```

Then copy the internal CA certificates into `certs/`, the client secret into
`secrets/oidc_client_secret`, create the internal network once
(`docker network create --internal <ifdd_lab_network>`) and follow the
instance documentation (`docs/`). The skip list keeps the generated secrets,
the certificates and the local hub configuration out of every later
`cruft update`.

## Variables

| Variable | Default | Meaning |
|---|---|---|
| `ifdd_lab_prj_name`, `ifdd_lab_prj_slug` | `IFDD Lab`, derived | name and directory of the instance; the slug also prefixes images, containers and home volumes |
| `ifdd_lab_host` | `lab` | host name Traefik routes (default for `IFDD_LAB_HOST`); **shared** with `ifdd-de/keycloak` (redirect URI of the client) |
| `ifdd_lab_entrypoint` | `websecure` | Traefik entry point of the router |
| `ifdd_lab_internet` | `n` | `n`: the user servers have no route outside and no Git panel (no bridge out of the installation); `y`: internet access and the Git panel of JupyterLab |
| `ifdd_lab_docker_mode` | `dind` | `dind`: own privileged Docker daemon, socket shared by volume, no TCP; `socket`: host's `/var/run/docker.sock` |
| `ifdd_lab_network` | `lab-net` | internal network of the hub, created once by hand, which the proxy joins (`ifdd_proxy_extra_networks` of `ifdd-de/proxy`) |
| `ifdd_lab_hub_base_image` | `node:26-slim` | base of the hub image (configurable-http-proxy needs Node.js 22 or later; Python from Debian) |
| `ifdd_lab_kernel_base_image` | `quay.io/jupyter/minimal-notebook:2026-11-16` | base of the images of the user servers (JupyterLab 4.6.6, JupyterHub 6.2.0, Python 3.13, XeLaTeX) |
| `ifdd_lab_postgres_image` | `postgres:18` | hub database |
| `ifdd_lab_dind_image` | `docker:29.9.2-dind` | DinD image |
| `ifdd_lab_images` | `default` | images offered at start, comma-separated; each is a directory `images/<name>/` (the hook copies `default` for new names) |
| `ifdd_lab_mem_limit`, `ifdd_lab_cpu_limit` | `2G`, `1` | limits per user server |
| `ifdd_lab_idle_timeout` | `3600` | seconds without activity before the idle culler stops a server (at least 300) |
| `ifdd_keycloak_lab_client_id` | `ifdd-lab` | **shared** with `ifdd-de/keycloak`: confidential client of the hub |
| `ifdd_keycloak_lab_users_group`, `ifdd_keycloak_lab_admins_group` | `ifdd_lab_users`, `ifdd_lab_admins` | **shared** with `ifdd-de/keycloak`: Keycloak groups that may log in and that administer the hub |
| `ifdd_oidc_realm` | `https://keycloak.example.org/realms/ifdd` | realm URL |
| `ifdd_be_url` | `https://be.example.org` | ifdd-be for notebooks (`IFDD_BE_URL` in the user servers) |

`hooks/pre_gen_project.py` rejects values that would render but not work.
`hooks/post_gen_project.py` creates `.env` from `dotenv.dist` and fills every
`<<generate:...>>` placeholder with a random value of the stated quality;
existing files are never overwritten.

## Delegation of rights

The hub (`hub/ifdd_lab_hub.py`) logs users in with `GenericOAuthenticator`
(code flow with PKCE) and keeps the tokens in the encrypted auth state.

- The API token of a user server has the scope `admin:auth_state!user`, so it
  can read the auth state of its own user and of nobody else; the role
  `user` grants that scope to every user.
- `ifdd_lab.access_token()` in the image asks the hub API
  (`/hub/api/users/<user>`) for the current access token;
  `ifdd_lab.session()` sends it with every request.
- OAuthenticator 17.5.0 renews a token only after it has expired; the
  hook `refresh_user_hook` renews it when less than 300 s are left, so a
  notebook never gets a token that is about to expire.
- The client in Keycloak passes the roles of the user into the token
  (`full_scope_allowed`) and carries the audience of ifdd-be; ifdd-be checks
  the roles and context patterns as for every other client.

## Requirements on the other templates

- `ifdd-de/keycloak`: the client `ifdd_keycloak_lab_client_id` and the two
  groups (added together with this template).
- `ifdd-de/proxy`: joins the network `ifdd_lab_network` with its host aliases
  (`ifdd_proxy_extra_networks`, added together with this template).

## Documentation of the instance (`docs/`)

Every instance carries its operating documentation as Sphinx sources in
MyST Markdown, in English (`docs/en`) and German (`docs/de`), with the same
files, labels and headings in both: `index`, `setup`, `build-release`,
`operations`, `security`, `troubleshooting`, `reference`, plus `kernels`
(images of the user servers, `ifdd_lab`). Labels start with `ifdd-lab-`;
references to `ifdd-instances-lab` resolve only in the full documentation.
`tests/check_docs.py` checks a rendered instance and builds both languages
with `-W`; it needs Java and Graphviz for PlantUML:

```bash
export IFDD_PLANTUML_JAR="$(tests/docs/get_plantuml.sh)"
python tests/check_docs.py <instance> --prefix ifdd-lab-
```

## CI

- `template-test.yml`, job `render`: renders every fixture in
  `tests/fixtures/` (`defaults`: DinD without internet; `internet`: DinD with
  internet and two images; `socket`: host socket with internet), checks for
  leftover placeholders, runs the instance tests (static checks, the helper
  against a stand-in hub API, the hub configuration and the refresh hook with
  the pinned packages against a stand-in OIDC provider), checks and builds
  the documentation, parses the scripts, validates the compose file and
  checks that the pre-generation hook rejects bad values.
- `template-test.yml`, job `smoke`: builds all images and starts each
  fixture with the real images, without Keycloak (`tests/smoke.sh`): a server
  started through the hub API runs as `jovyan`, has the packages and the
  helper, the Git panel only with internet access, no news feed and update
  check, exports a PDF through LaTeX, reaches the internet only as
  configured, reads the hub API with its token, and keeps its home across a
  restart.
- `template-update-test.yml`: generates from the most recent tag and applies
  the current state with `cruft update` (no tag yet: nothing to do).

Not in the CI of the template: the login through Keycloak and the
delegation to ifdd-be; they need the whole installation (`ifdd-de/meta`).

## Security notes

- Docker access is root-equivalent: on the host with `socket`, inside the
  privileged DinD container with `dind`. The hub runs as root; the user
  servers run as `jovyan` without published ports.
- Code in a user server can read the tokens of its own user (that is the
  delegation). It cannot read those of other users.
- With `dind` the user servers share the network namespace of the
  Docker-in-Docker daemon, like the task containers of `ifdd-de/wf`: a
  user-defined network inside the daemon did not resolve the names of the
  lab network (smoke test with `docker:29.9.2-dind`). Each server listens on
  its own port behind the hub's login; `NET_RAW` is dropped and
  `no-new-privileges` set for every user server, so no server can read the
  traffic of another.
- With `ifdd_lab_internet=n` the user servers reach only the services behind
  the proxy. Downloads through the browser remain possible.

## AI assistance

Some parts of this repository, in particular the tests, the test data and the
documentation, were developed or improved with the help of large language
models (LLMs). All changes were reviewed and released by the maintainer.
