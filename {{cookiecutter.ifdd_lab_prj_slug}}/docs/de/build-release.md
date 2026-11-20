(ifdd-lab-build-release)=
# Bauen und Ausliefern
{%- set dind = cookiecutter.ifdd_lab_docker_mode == "dind" %}

## Images

Alle Images baut `./adm_01_build.sh` lokal; sie werden nie veröffentlicht,
denn sie enthalten die CA-Zertifikate aus `certs/`.

| Image | Gebaut aus | Inhalt |
|---|---|---|
| `{{ cookiecutter.ifdd_lab_prj_slug }}-hub:local` | `{{ cookiecutter.ifdd_lab_hub_base_image }}` (Node.js für configurable-http-proxy) | JupyterHub, OAuthenticator, DockerSpawner, Idle-Culler, PostgreSQL-Treiber (`hub/requirements.txt`), die Konfiguration aus `hub/` |
{%- if dind %}
| `{{ cookiecutter.ifdd_lab_prj_slug }}-dind:local` | `{{ cookiecutter.ifdd_lab_dind_image }}` | der Docker-Daemon der Benutzer-Server |
{%- endif %}
{%- for name in cookiecutter.ifdd_lab_images.split(",") %}
| `{{ cookiecutter.ifdd_lab_prj_slug }}-{{ name }}:local` | `{{ cookiecutter.ifdd_lab_kernel_base_image }}` | Benutzer-Server: `images/{{ name }}/`, siehe {ref}`ifdd-lab-kernels` |
{%- endfor %}

`adm_01_build.sh` übergibt `--pull`, damit ein wanderndes Basis-Tag neu
geholt wird. Nach einem Build {% if dind %}lädt `./adm_02_run.sh` die Images
in den Docker-in-Docker-Daemon und {% else %}startet `./adm_02_run.sh` {% endif %}den Hub neu. Laufende
Server behalten ihr altes Image, bis sie enden; ein Benutzer startet den
eigenen Server auf der Hub-Seite neu (File, Hub Control Panel, Stop My
Server).

## Hinter einem TLS-aufbrechenden Proxy

Die CA-Zertifikate aus `certs/` liegen im Trust-Store jedes Images, bevor
etwas heruntergeladen wird: `pip` und `npm` im Hub-Image, `pip` in den Images
der Benutzer-Server. Die CAs des aufbrechenden Proxys gehören vor dem ersten
Build dorthin.

## Template aktualisieren

```bash
cruft update
./adm_01_build.sh
./adm_02_run.sh
```

`cruft update` fasst `.env`, `secrets/`, `certs/` und `hub/config.d/` nie an
(Skip-Liste). Images unter `images/` außer `default` gehören der Instanz;
das Template kennt sie nicht, ein Update lässt sie also, wie sie sind.
