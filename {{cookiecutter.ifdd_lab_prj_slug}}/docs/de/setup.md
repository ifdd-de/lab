(ifdd-lab-setup)=
# Einrichtung
{%- set dind = cookiecutter.ifdd_lab_docker_mode == "dind" %}
{%- set internet = cookiecutter.ifdd_lab_internet == "y" %}

## Voraussetzungen

| Was | Wozu |
|---|---|
| Docker mit Compose | Hub, PostgreSQL{% if dind %}, der Docker-in-Docker-Daemon{% endif %} und die Benutzer-Server laufen als Container; die Images werden lokal gebaut |
| einige GB freier Plattenplatz je Image | die Images der Benutzer-Server bauen auf `{{ cookiecutter.ifdd_lab_kernel_base_image }}` auf, das LaTeX enthält{% if dind %}; mit Docker-in-Docker liegt jedes Image zweimal vor (auf dem Host und im Daemon){% endif %} |
| eine laufende Proxy-Instanz, die dem Netz `{{ cookiecutter.ifdd_lab_network }}` mit ihren Host-Aliasen beitritt | Traefik routet `IFDD_LAB_HOST` zum Hub; Hub und Benutzer-Server erreichen Keycloak und ifdd-be über ihn |
| der Keycloak-Client `{{ cookiecutter.ifdd_keycloak_lab_client_id }}` mit der Redirect-URI `https://<IFDD_LAB_HOST>/hub/oauth_callback` und die Gruppen `{{ cookiecutter.ifdd_keycloak_lab_users_group }}` und `{{ cookiecutter.ifdd_keycloak_lab_admins_group }}` | Anmeldung; `ifdd-de/keycloak` legt sie in einem neuen Realm an |
| das CA-Zertifikat des Proxys, falls er eine eigene CA nutzt | es wird in jedes Image eingebaut |

## Instanz anlegen

Üblicherweise legt `ifdd-meta create` alle Instanzen einer Installation an:
Es ruft `cruft create` mit der Variablendatei der Installation auf, kopiert
die lokale CA des Proxys nach `certs/` und das Client-Secret nach
`secrets/oidc_client_secret`. Von Hand, aus dem Verzeichnis mit den
Instanzen, mit der Skip-Liste, die dieses Template empfiehlt:

```bash
cruft create --no-input --config-file cookiecutter_all.yaml \
  --skip .env --skip secrets --skip certs --skip hub/config.d \
  https://github.com/ifdd-de/lab
cp proxy/certs/ca.crt {{ cookiecutter.ifdd_lab_prj_slug }}/certs/
```

## Konfiguration und Secrets

Der Hook des Templates schreibt `.env` (Modus 0600) mit einem
Datenbank-Passwort, dem Schlüssel des verschlüsselten Auth-States und dem
Cookie-Secret. Das Client-Secret kommt aus der `.env` der Keycloak-Instanz
(`IFDD_KEYCLOAK_LAB_CLIENT_SECRET`):

```bash
cd {{ cookiecutter.ifdd_lab_prj_slug }}
umask 077
grep '^IFDD_KEYCLOAK_LAB_CLIENT_SECRET=' ../keycloak/.env | cut -d= -f2- > secrets/oidc_client_secret
```

## Das Lab-Netz

Der Hub{% if dind %} und der Docker-in-Docker-Daemon{% endif %} liegen im
Netz `{{ cookiecutter.ifdd_lab_network }}`. Es ist intern, also hat nichts
darin eine Route nach außen, und es wird mit dem Proxy geteilt, also gehört
es keinem Compose-Projekt. Einmal anlegen:

```bash
docker network create --internal {{ cookiecutter.ifdd_lab_network }}
```

Die Proxy-Instanz muss ihm mit denselben Host-Aliasen beitreten wie dem
gemeinsamen Proxy-Netz (Variable `ifdd_proxy_extra_networks` von
`ifdd-de/proxy`); sonst routet Traefik nicht zum Hub, und die Benutzer-Server
erreichen weder `ifdd-be` noch Keycloak. `adm_02_run.sh` startet nicht, wenn
das Netz fehlt oder nicht intern ist.
{%- if internet %}

Mit Internetzugang treten {% if dind %}der Docker-in-Docker-Daemon{% else %}die Benutzer-Server und der Hub{% endif %} zusätzlich
dem Netz `{{ cookiecutter.ifdd_lab_prj_slug }}-egress` bei, das Compose
anlegt.
{%- endif %}

## Erster Start

```bash
./adm_01_build.sh
./adm_02_run.sh
```

Dann `https://<IFDD_LAB_HOST>/` öffnen und bei Keycloak anmelden. Mitglieder
von `{{ cookiecutter.ifdd_keycloak_lab_users_group }}` bekommen JupyterLab;
alle anderen bekommen vom Hub die Seite „403: Forbidden“.

## Mehrere Server

Laufen Keycloak oder ifdd-be auf einem anderen Server, müssen ihre
Hostnamen zum Proxy jenes Servers auflösen, und dessen CA muss in `certs/`
liegen. Die Redirect-URI des Clients nennt den Host dieses Hubs. Die Werte
kommen aus der Variablendatei der Installation (`ifdd_oidc_realm`,
`ifdd_be_url`).
