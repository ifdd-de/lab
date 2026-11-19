(ifdd-lab-index)=
# {{ cookiecutter.ifdd_lab_prj_name }} (lab)
{%- set dind = cookiecutter.ifdd_lab_docker_mode == "dind" %}
{%- set internet = cookiecutter.ifdd_lab_internet == "y" %}

Der Notebook-Dienst eines IFDD-Knotens: JupyterHub startet nach einer
Anmeldung bei Keycloak je Benutzer einen Container aus einem lokalen Image.
Notebooks rufen die IFDD-Dienste mit den Rechten der angemeldeten Person auf:
Der Hub hält die Tokens der Anmeldung und gibt dem Notebook das aktuelle
Access-Token (`import ifdd_lab`). Dieses Kapitel beschreibt die Instanz
`{{ cookiecutter.ifdd_lab_prj_slug }}`, erzeugt aus dem Template
`ifdd-de/lab`, aus Sicht derer, die sie einrichten, bauen, betreiben und
absichern.

| | |
|---|---|
| URL | `https://{{ cookiecutter.ifdd_lab_host }}/` (Vorgabe von `IFDD_LAB_HOST`; vom Proxy geroutet) |
| Anmeldung | Keycloak-Client `{{ cookiecutter.ifdd_keycloak_lab_client_id }}`; die Gruppe `{{ cookiecutter.ifdd_keycloak_lab_users_group }}` darf sich anmelden, die Gruppe `{{ cookiecutter.ifdd_keycloak_lab_admins_group }}` verwaltet den Hub |
| Server der Benutzer | {% if dind %}in einem eigenen Docker-in-Docker-Daemon (`{{ cookiecutter.ifdd_lab_dind_image }}`){% else %}im Docker-Daemon des Hosts (Socket eingebunden){% endif %}, Images `{{ cookiecutter.ifdd_lab_images }}` auf Basis von `{{ cookiecutter.ifdd_lab_kernel_base_image }}` |
| Internetzugang der Server | {% if internet %}ja, mit dem Git-Panel von JupyterLab{% else %}keiner: sie erreichen nur die Dienste hinter dem Proxy{% endif %} |
| Grenzen je Benutzer | Speicher `{{ cookiecutter.ifdd_lab_mem_limit }}`, CPUs `{{ cookiecutter.ifdd_lab_cpu_limit }}`; untätige Server enden nach {{ cookiecutter.ifdd_lab_idle_timeout }} s |
| Backend für Notebooks | `{{ cookiecutter.ifdd_be_url }}` mit dem eigenen Token des Benutzers |

## Was die Instanz enthält

Eine Compose-Datei; das Hub-Image (`hub/`: `Dockerfile`, `requirements.txt`,
`jupyterhub_config.py`, `ifdd_lab_hub.py`){% if dind %}, das
Docker-in-Docker-Image (`dind/`){% endif %} und die Images der
Benutzer-Server (`images/<name>/`), alle lokal gebaut und mit den
CA-Zertifikaten aus `certs/` im Trust-Store; den Helfer `lib/ifdd_lab.py`, den
jedes Image enthält; `.env` mit erzeugten Werten; `secrets/` für das
Client-Secret; `hub/config.d/` für lokale Ergänzungen; ein Beispiel-Notebook;
die Skripte `adm_01_build.sh`, `adm_02_run.sh` und `adm_99_destroy.sh`.

## Architektur

```{uml}
@startuml
left to right direction
rectangle "Browser" as Browser
rectangle "proxy: Traefik" as Proxy
rectangle "Keycloak" as KC
rectangle "hub: JupyterHub" as Hub
database "PostgreSQL" as PG
Browser --> Proxy : HTTPS
Proxy --> Hub : Lab-Netz
Hub --> PG : db-Netz
Hub --> KC : über den Proxy: Anmeldung, Erneuerung
{%- if dind %}
rectangle "dind: Docker-Daemon" as Docker
Hub --> Docker : Socket-Volume
{%- else %}
rectangle "Docker des Hosts" as Docker
Hub --> Docker : Socket des Hosts
{%- endif %}
rectangle "Benutzer-Server" as Servers
Docker --> Servers
Servers --> Hub : Hub-API: aktuelles Token
rectangle "ifdd-be" as BE
Servers --> Proxy : Token des Benutzers
Proxy --> BE
{%- if internet %}
rectangle "Internet" as Net
Servers --> Net : Egress-Netz
{%- endif %}
@enduml
```

| Wer | Nutzt lab für |
|---|---|
| Personen in der Gruppe `{{ cookiecutter.ifdd_keycloak_lab_users_group }}` | Notebooks in JupyterLab, mit den eigenen Rechten in ifdd-be |
| Personen in der Gruppe `{{ cookiecutter.ifdd_keycloak_lab_admins_group }}` | die Admin-Seite des Hubs (Server anderer Benutzer) |

## Kapitel

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

Die Werte der Variablen dieser Instanz und wie sie mit den anderen Diensten
zusammenhängen, stehen im Kapitel über die Dienst-Instanzen
({ref}`ifdd-instances-lab`).
