# Additional CA certificates

Place the PEM files of internal CAs here (`*.crt` or `*.pem`), for example
the CA of the IFDD proxy and the CAs of a TLS-inspecting proxy. They are
git-ignored; `ifdd-meta create` copies the local CA of the proxy in.

At build time they are added to the system trust store of

- the hub image (login at Keycloak; `npm` and `pip` during the build),
{%- if cookiecutter.ifdd_lab_docker_mode == "dind" %}
- the Docker-in-Docker image,
{%- endif %}
- every image of the user servers (`images/<name>/`): Python's `ssl`,
  `requests` and `pip` use the system bundle there (`SSL_CERT_FILE`,
  `REQUESTS_CA_BUNDLE`, `PIP_CERT`).

Without files here the images keep their default trust store. Rebuild after
a change: `./adm_01_build.sh`, then `./adm_02_run.sh`.
