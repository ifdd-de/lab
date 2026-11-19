(ifdd-lab-operations)=
# Operations
{%- set dind = cookiecutter.ifdd_lab_docker_mode == "dind" %}

## Start, stop, status

```bash
./adm_02_run.sh                                         # start or restart
docker compose -f docker-compose-production.yml ps
docker compose -f docker-compose-production.yml logs -f hub
docker compose -f docker-compose-production.yml down    # keeps the volumes
```

The hub stops the servers of the users when it stops; their homes stay.

## Servers of the users

| Rule | Value |
|---|---|
| one server per user | named servers are off |
| image | chosen at start when there is more than one (`{{ cookiecutter.ifdd_lab_images }}`) |
| memory, CPUs | `{{ cookiecutter.ifdd_lab_mem_limit }}`, `{{ cookiecutter.ifdd_lab_cpu_limit }}` |
| idle | stopped after {{ cookiecutter.ifdd_lab_idle_timeout }} s without activity (jupyterhub-idle-culler) |
| home | volume `{{ cookiecutter.ifdd_lab_prj_slug }}-home-<user>` at `/home/jovyan`{% if dind %}, inside the Docker-in-Docker daemon (volume `dind-data`){% endif %}; the container is removed when the server stops, the home stays |

Members of `{{ cookiecutter.ifdd_keycloak_lab_admins_group }}` see the
servers of all users on the admin page of the hub (`/hub/admin`) and can stop
them.

## Login and tokens

The hub keeps the tokens of a login in its database, encrypted with
`JUPYTERHUB_CRYPT_KEY`. It renews the access token with the refresh token
when less than five minutes are left. The Keycloak session of the client
`{{ cookiecutter.ifdd_keycloak_lab_client_id }}` ends after a long idle time
or at its maximum lifespan (settings of the realm and of the client); then
the hub sends the user to the login again, and `ifdd_lab` in a running
notebook raises `LoginRequired`.

## Backups

```{note}
Not tested: there is no backup of the hub database and the homes yet. The
homes are {% if dind %}in the volume `dind-data`{% else %}the volumes `{{ cookiecutter.ifdd_lab_prj_slug }}-home-*`{% endif %}; deleting {% if dind %}it{% else %}them{% endif %} deletes every notebook of every user.
```

## Removal

`./adm_99_destroy.sh` asks for confirmation, then deletes containers,
volumes (with the homes of all users), local images and the instance
directory.
