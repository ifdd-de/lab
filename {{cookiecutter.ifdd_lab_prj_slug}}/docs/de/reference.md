(ifdd-lab-reference)=
# Referenz
{%- set dind = cookiecutter.ifdd_lab_docker_mode == "dind" %}

Die Variablen des Templates und ihre Werte in dieser Instanz stehen in
{ref}`ifdd-instances-lab`. Diese Seite nennt, was keine Template-Variable
ist.

## Aufbau

| Pfad | Inhalt |
|---|---|
| `docker-compose-production.yml` | PostgreSQL, {% if dind %}Docker-in-Docker, {% endif %}Hub und die Image-Builds (Profil `images`) |
| `hub/` | Hub-Image; `jupyterhub_config.py` lädt `ifdd_lab_hub.py` (Einstellungen aus der Umgebung) und `config.d/*.py` |
| `hub/config.d/` | lokale Ergänzungen der Hub-Konfiguration (git-ignoriert, Skip-Liste) |
{%- if dind %}
| `dind/` | Docker-in-Docker-Image |
{%- endif %}
| `images/<name>/` | Images der Benutzer-Server; `default` kommt aus dem Template |
| `lib/ifdd_lab.py` | Helfer in jedem Image: das Token des Benutzers für IFDD-Dienste |
| `build/install-certs.sh` | nimmt `certs/*` in den Trust-Store jedes Images auf |
| `certs/` | interne CA-Zertifikate (git-ignoriert) |
| `secrets/oidc_client_secret` | Client-Secret (git-ignoriert) |
| `.env` | Host, erzeugte Passwörter und Schlüssel (git-ignoriert) |
| `examples/notebooks/` | Beispiel-Notebook |
| `adm_01_build.sh`, `adm_02_run.sh`, `adm_99_destroy.sh` | bauen; prüfen und starten; alles löschen |

## Umgebung (`.env`)

| Variable | Vorgabe hier | Bedeutung |
|---|---|---|
| `IFDD_LAB_HOST` | `{{ cookiecutter.ifdd_lab_host }}` | Host, den der Proxy zum Hub routet |
| `IFDD_LAB_DB_PASSWORD` | erzeugt | einmal gesetzt |
| `JUPYTERHUB_CRYPT_KEY` | erzeugt | Schlüssel der gespeicherten Tokens; ein neuer Schlüssel zwingt jeden Benutzer zur neuen Anmeldung |
| `JPY_COOKIE_SECRET` | erzeugt | Secret der Anmelde-Cookies |

## Umgebung der Benutzer-Server

| Variable | Wert |
|---|---|
| `IFDD_BE_URL` | `{{ cookiecutter.ifdd_be_url }}` (Basis-URL von `ifdd_lab.session()`) |
| `IFDD_OIDC_REALM` | `{{ cookiecutter.ifdd_oidc_realm }}` |
| `JUPYTERHUB_API_URL`, `JUPYTERHUB_API_TOKEN`, `JUPYTERHUB_USER` | vom Hub gesetzt; `ifdd_lab` liest damit das Token |

## Einstellungen des Hubs

| Einstellung | Wert |
|---|---|
| Erneuerung des Access-Tokens | wenn weniger als 300 s übrig sind (`ifdd_lab_hub.REFRESH_MARGIN`) |
| Prüfung des Auth-States | höchstens alle 60 s je Benutzer |
| Scopes des API-Tokens eines Servers | `users:activity!user`, `access:servers!server`, `read:users!user`, `admin:auth_state!user` |
| URL nach der Anmeldung | `/lab` |
