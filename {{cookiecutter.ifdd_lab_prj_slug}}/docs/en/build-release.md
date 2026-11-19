(ifdd-lab-build-release)=
# Build and release
{%- set dind = cookiecutter.ifdd_lab_docker_mode == "dind" %}

## Images

All images are built locally by `./adm_01_build.sh` and never pushed: they
carry the CA certificates of `certs/`.

| Image | Built from | Content |
|---|---|---|
| `{{ cookiecutter.ifdd_lab_prj_slug }}-hub:local` | `{{ cookiecutter.ifdd_lab_hub_base_image }}` (Node.js for configurable-http-proxy) | JupyterHub, OAuthenticator, DockerSpawner, idle culler, PostgreSQL driver (`hub/requirements.txt`), the configuration of `hub/` |
{%- if dind %}
| `{{ cookiecutter.ifdd_lab_prj_slug }}-dind:local` | `{{ cookiecutter.ifdd_lab_dind_image }}` | the Docker daemon of the user servers |
{%- endif %}
{%- for name in cookiecutter.ifdd_lab_images.split(",") %}
| `{{ cookiecutter.ifdd_lab_prj_slug }}-{{ name }}:local` | `{{ cookiecutter.ifdd_lab_kernel_base_image }}` | user server: `images/{{ name }}/`, see {ref}`ifdd-lab-kernels` |
{%- endfor %}

`adm_01_build.sh` passes `--pull`, so a moving base tag is fetched again.
After a build, `./adm_02_run.sh` {% if dind %}loads the images into the
Docker-in-Docker daemon and {% endif %}restarts the hub. Running servers keep
their old image until they are stopped; a user restarts the own server from
the hub page (File, Hub Control Panel, Stop My Server).

## Behind a TLS-inspecting proxy

The CA certificates in `certs/` are in the trust store of every image before
anything is downloaded: `pip` and `npm` in the hub image, `pip` in the images
of the user servers. Put the CAs of the inspecting proxy there before the
first build.

## Updating the template

```bash
cruft update
./adm_01_build.sh
./adm_02_run.sh
```

`cruft update` never touches `.env`, `secrets/`, `certs/` and `hub/config.d/`
(skip list). Images under `images/` other than `default` belong to the
instance; the template does not know them, so an update leaves them as they
are.
