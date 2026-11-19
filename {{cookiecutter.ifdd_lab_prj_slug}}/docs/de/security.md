(ifdd-lab-security)=
# Sicherheit
{%- set dind = cookiecutter.ifdd_lab_docker_mode == "dind" %}
{%- set internet = cookiecutter.ifdd_lab_internet == "y" %}

## Wer was darf

| Wer | Darf |
|---|---|
| Mitglieder von `{{ cookiecutter.ifdd_keycloak_lab_users_group }}` | sich anmelden, den eigenen Server starten, darin beliebigen Code ausführen |
| Mitglieder von `{{ cookiecutter.ifdd_keycloak_lab_admins_group }}` | zusätzlich die Server aller Benutzer sehen und beenden |
| alle anderen | nichts: Der Hub antwortet nach der Anmeldung mit 403 |

Ein Notebook handelt in ifdd-be mit den Rollen und Kontextmustern der
angemeldeten Person, nicht mehr: Der Client
`{{ cookiecutter.ifdd_keycloak_lab_client_id }}` gibt die Rollen des Benutzers
ins Token, und ifdd-be prüft sie. Es gibt kein gemeinsames Dienstkonto.

## Delegierte Tokens

- Das API-Token eines Benutzer-Servers darf den Auth-State des eigenen
  Benutzers lesen und sonst nichts (`admin:auth_state!user`). Der Auth-State
  enthält Access- und Refresh-Token der Anmeldung; Code im Server kann beide
  lesen. Das ist der Preis der Delegation: Wer im eigenen Server Code
  ausführt, kann für die Laufzeit des Refresh-Tokens als diese Person handeln.
- Ein Token nie ausgeben und nie in eine Ausgabe schreiben: Ausgaben werden
  in der Notebook-Datei gespeichert und wandern mit ihr.
- Die Tokens liegen verschlüsselt (`JUPYTERHUB_CRYPT_KEY` in `.env`).

## Netz

- Die Benutzer-Server liegen in keinem Netz mit den anderen Diensten; sie
  erreichen sie nur über den Proxy (Lab-Netz `{{ cookiecutter.ifdd_lab_network }}`, intern).
{%- if internet %}
- **Internetzugang ist an** (`ifdd_lab_internet=y`): Die Benutzer-Server
  erreichen jeden Host im Internet, und das Git-Panel von JupyterLab ist
  installiert. Daten können die Installation auf diesem Weg verlassen. Diese
  Einstellung nicht nutzen, wo Konfiguration und Laufzeitdaten das
  Unternehmen nicht verlassen dürfen.
{%- else %}
- **Kein Internetzugang** (`ifdd_lab_internet=n`): Die Benutzer-Server haben
  keine Route nach außen; es gibt kein Git-Panel. `git`, `curl` und Python
  bleiben im Image, erreichen ohne Route aber nichts außerhalb.
{%- endif %}
- Downloads im Browser bleiben: Ein Benutzer kann Dateien und PDF-Exporte
  aus JupyterLab auf den eigenen Arbeitsplatz laden. Das ist wie bei den
  anderen Weboberflächen hingenommen (der Arbeitsplatz gehört zum
  Unternehmen).
- JupyterLab holt keine Neuigkeiten und prüft keine Updates
  (Image-Konfiguration).

## Docker

{%- if dind %}
Der Hub steuert einen Docker-in-Docker-Daemon über einen Socket in einem
gemeinsamen Volume. Dieser Daemon läuft in einem privilegierten Container;
er hält den Docker-Daemon des Hosts vom Hub fern, nicht den Kernel.
{%- else %}
Der Hub bindet den Docker-Socket des Hosts ein: volle Kontrolle über den
Docker-Daemon des Hosts, also root auf dem Host.
{%- endif %}
Der Hub läuft in seinem Container als root; die Benutzer-Server laufen als
Benutzer `jovyan` (UID 1000) ohne veröffentlichte Ports.
