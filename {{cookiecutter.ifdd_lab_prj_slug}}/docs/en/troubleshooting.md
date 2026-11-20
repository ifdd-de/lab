(ifdd-lab-troubleshooting)=
# Troubleshooting
{%- set dind = cookiecutter.ifdd_lab_docker_mode == "dind" %}

| Symptom | Cause and remedy |
|---|---|
| `adm_02_run.sh`: network `{{ cookiecutter.ifdd_lab_network }}` missing or not internal | create it once with `docker network create --internal {{ cookiecutter.ifdd_lab_network }}` (see {ref}`ifdd-lab-setup`) |
| 404 or "Gateway Timeout" at `https://<IFDD_LAB_HOST>/` | the proxy is not in the lab network: add the network to `ifdd_proxy_extra_networks` of the proxy instance and restart it |
| "403: Forbidden" after the login | the user is not in `{{ cookiecutter.ifdd_keycloak_lab_users_group }}`; add the group in Keycloak, then log in again |
| login ends with "invalid redirect_uri" at Keycloak | the client `{{ cookiecutter.ifdd_keycloak_lab_client_id }}` lacks `https://<IFDD_LAB_HOST>/hub/oauth_callback` |
| hub log: certificate verify failed | the CA of the proxy is not in `certs/`; copy it there and rebuild (`./adm_01_build.sh`) |
| the server does not start: image not found | {% if dind %}`./adm_02_run.sh` loads the images into the Docker-in-Docker daemon; run it after every build{% else %}build the images with `./adm_01_build.sh`{% endif %} |
| `ifdd_lab.LoginRequired` in a notebook | the Keycloak session ended; reload the hub page and log in again |
| ifdd-be answers 401 to a notebook | the token lacks the audience of ifdd-be: the client needs the scope of the backend audience (keycloak template) |
| ifdd-be answers 403 to a notebook | the user lacks the role or the context pattern; `/whoami` of ifdd-be shows what the token carries |

Logs: `docker compose -f docker-compose-production.yml logs hub`{% if dind %};
the containers of the users: `docker compose -f docker-compose-production.yml exec dind docker ps`{% endif %}.
