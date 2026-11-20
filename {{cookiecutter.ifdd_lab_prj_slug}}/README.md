{%- set dind = cookiecutter.ifdd_lab_docker_mode == "dind" -%}
# {{ cookiecutter.ifdd_lab_prj_name }}

JupyterHub with one container per user ({% if dind %}in an own Docker-in-Docker daemon{% else %}on the host's Docker daemon{% endif %}),
login through Keycloak, generated from `ifdd-de/lab`. Production URL:
`https://<IFDD_LAB_HOST>/`. Notebooks call IFDD services with the rights
of the person logged in (`import ifdd_lab`).
Internet access of the user servers: **{% if cookiecutter.ifdd_lab_internet == "y" %}yes, with the Git panel{% else %}none{% endif %}**.

## Quick start

```bash
cp <proxy instance>/certs/ca.crt certs/      # with the local CA of the proxy
# client secret of {{ cookiecutter.ifdd_keycloak_lab_client_id }} from the keycloak instance:
install -m 600 /dev/null secrets/oidc_client_secret && editor secrets/oidc_client_secret
docker network create --internal {{ cookiecutter.ifdd_lab_network }}    # once; the proxy joins it
./adm_01_build.sh
./adm_02_run.sh
```

Then log in at Keycloak; members of `{{ cookiecutter.ifdd_keycloak_lab_users_group }}` get a server.

## Documentation

Setup, build and release, operations, security, troubleshooting, reference
and the images of the user servers:

- English: [docs/en/index.md](docs/en/index.md)
- Deutsch: [docs/de/index.md](docs/de/index.md)

The pages are Sphinx sources in MyST Markdown, meant to be copied into a
documentation project that covers all services; GitHub shows them as plain
Markdown.

## AI assistance

Some parts of the template `ifdd-de/lab` this instance was generated
from, in particular the tests, the test data and the documentation, were
developed or improved with the help of large language models (LLMs). All
changes were reviewed and released by the maintainer.

## License

BSD-3-Clause, see `LICENSE`.
