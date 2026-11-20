(ifdd-lab-security)=
# Security
{%- set dind = cookiecutter.ifdd_lab_docker_mode == "dind" %}
{%- set internet = cookiecutter.ifdd_lab_internet == "y" %}

## Who may do what

| Who | May |
|---|---|
| members of `{{ cookiecutter.ifdd_keycloak_lab_users_group }}` | log in, start the own server, run any code in it |
| members of `{{ cookiecutter.ifdd_keycloak_lab_admins_group }}` | additionally see and stop the servers of all users |
| everybody else | nothing: the hub answers 403 after the login |

A notebook acts in ifdd-be with the roles and context patterns of the person
logged in, no more: the client `{{ cookiecutter.ifdd_keycloak_lab_client_id }}`
passes the roles of the user into the token, and ifdd-be checks them. There
is no shared service account.

## Delegated tokens

- The API token of a user server may read the auth state of its own user
  and nothing else (`admin:auth_state!user`). The auth state holds the
  access token and the refresh token of the login; code in the server can
  read both. That is the price of the delegation: whoever runs code in the
  own server can act as that person for the lifetime of the refresh token.
- Never print a token or write it into an output: outputs are saved in the
  notebook file and travel with it.
- The tokens are stored encrypted (`JUPYTERHUB_CRYPT_KEY` in `.env`).

## Network

- The user servers are in no network with the other services; they reach
  them only through the proxy (lab network `{{ cookiecutter.ifdd_lab_network }}`, internal).
{%- if internet %}
- **Internet access is on** (`ifdd_lab_internet=y`): the user servers can
  reach any host on the internet, and the Git panel of JupyterLab is
  installed. Data can leave the installation this way. Do not use this
  setting where configuration and run-time data must not leave the company.
{%- else %}
- **No internet access** (`ifdd_lab_internet=n`): the user servers have no
  route outside; there is no Git client panel. `git`, `curl` and Python stay
  in the image, but without a route they reach nothing outside.
{%- endif %}
- Browser downloads remain: a user can download files and PDF exports from
  JupyterLab to the own workstation. That is accepted as for the other web
  interfaces (the workstation belongs to the company).
- JupyterLab fetches no news and checks no updates (image configuration).

## Docker

{%- if dind %}
The hub controls a Docker-in-Docker daemon through a socket in a shared
volume. That daemon runs in a privileged container; it keeps the host's own
Docker daemon out of reach of the hub, not out of reach of the kernel.
{%- else %}
The hub mounts the host's Docker socket: full control of the host's Docker
daemon, which is root on the host.
{%- endif %}
The hub runs as root in its container; the user servers run as the user
`jovyan` (UID 1000) without published ports.

{% if dind -%}
The user servers run in the Docker-in-Docker daemon with its network, like
the task containers of `ifdd-de/wf`: they share one network namespace, each
listening on a port of its own, protected by the login of the hub. They have
no raw sockets (`NET_RAW` dropped) and cannot gain privileges, so one server
cannot read the traffic of another.
{%- else -%}
The user servers have no raw sockets (`NET_RAW` dropped) and cannot gain
privileges.
{%- endif %}
