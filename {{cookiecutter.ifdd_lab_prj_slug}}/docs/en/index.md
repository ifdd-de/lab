(ifdd-lab-index)=
# {{ cookiecutter.ifdd_lab_prj_name }} (lab)
{%- set dind = cookiecutter.ifdd_lab_docker_mode == "dind" %}
{%- set internet = cookiecutter.ifdd_lab_internet == "y" %}

The notebook service of an IFDD node: JupyterHub starts one container per
user from a local image, after a login at Keycloak. Notebooks call the IFDD
services with the rights of the person who is logged in: the hub keeps the
tokens of the login and hands the current access token to the notebook
(`import ifdd_lab`). This chapter describes the instance
`{{ cookiecutter.ifdd_lab_prj_slug }}`, generated from the template
`ifdd-de/lab`, from the point of view of the people who set it up, build,
run and secure it.

| | |
|---|---|
| URL | `https://{{ cookiecutter.ifdd_lab_host }}/` (default of `IFDD_LAB_HOST`; routed by the proxy) |
| Login | Keycloak client `{{ cookiecutter.ifdd_keycloak_lab_client_id }}`; group `{{ cookiecutter.ifdd_keycloak_lab_users_group }}` may log in, group `{{ cookiecutter.ifdd_keycloak_lab_admins_group }}` administers the hub |
| User servers | {% if dind %}in an own Docker-in-Docker daemon (`{{ cookiecutter.ifdd_lab_dind_image }}`){% else %}on the host's Docker daemon (socket mounted){% endif %}, images `{{ cookiecutter.ifdd_lab_images }}` based on `{{ cookiecutter.ifdd_lab_kernel_base_image }}` |
| Internet access of the user servers | {% if internet %}yes, with the Git panel of JupyterLab{% else %}none: they reach only the services behind the proxy{% endif %} |
| Limits per user | memory `{{ cookiecutter.ifdd_lab_mem_limit }}`, CPUs `{{ cookiecutter.ifdd_lab_cpu_limit }}`; idle servers stop after {{ cookiecutter.ifdd_lab_idle_timeout }} s |
| Backend for notebooks | `{{ cookiecutter.ifdd_be_url }}` with the user's own token |

## What the instance contains

One compose file; the hub image (`hub/`: `Dockerfile`, `requirements.txt`,
`jupyterhub_config.py`, `ifdd_lab_hub.py`){% if dind %}, the
Docker-in-Docker image (`dind/`){% endif %} and the images of the user
servers (`images/<name>/`), all built locally with the CA certificates of
`certs/` in their trust store; the helper `lib/ifdd_lab.py` that every image
contains; `.env` with generated values; `secrets/` for the client secret;
`hub/config.d/` for local additions; an example notebook; the scripts
`adm_01_build.sh`, `adm_02_run.sh` and `adm_99_destroy.sh`.

## Architecture

```{uml}
@startuml
left to right direction
rectangle "Browser" as Browser
rectangle "proxy: Traefik" as Proxy
rectangle "Keycloak" as KC
rectangle "hub: JupyterHub" as Hub
database "PostgreSQL" as PG
Browser --> Proxy : HTTPS
Proxy --> Hub : lab network
Hub --> PG : db network
Hub --> KC : via proxy: login, refresh
{%- if dind %}
rectangle "dind: Docker daemon" as Docker
Hub --> Docker : socket volume
{%- else %}
rectangle "host Docker" as Docker
Hub --> Docker : host socket
{%- endif %}
rectangle "user servers" as Servers
Docker --> Servers
Servers --> Hub : hub API: current token
rectangle "ifdd-be" as BE
Servers --> Proxy : user token
Proxy --> BE
{%- if internet %}
rectangle "Internet" as Net
Servers --> Net : egress network
{%- endif %}
@enduml
```

| Who | Uses lab for |
|---|---|
| people in the group `{{ cookiecutter.ifdd_keycloak_lab_users_group }}` | notebooks in JupyterLab, with their own rights in ifdd-be |
| people in the group `{{ cookiecutter.ifdd_keycloak_lab_admins_group }}` | the admin page of the hub (servers of other users) |

## Chapters

```{toctree}
:maxdepth: 2

setup
build-release
operations
security
troubleshooting
reference
kernels
```

The values of the variables of this instance and how they relate to the
other services are listed in the chapter on the service instances
({ref}`ifdd-instances-lab`).
