(ifdd-lab-troubleshooting)=
# Fehlersuche
{%- set dind = cookiecutter.ifdd_lab_docker_mode == "dind" %}

| Symptom | Ursache und Abhilfe |
|---|---|
| `adm_02_run.sh`: Netz `{{ cookiecutter.ifdd_lab_network }}` fehlt oder ist nicht intern | einmal mit `docker network create --internal {{ cookiecutter.ifdd_lab_network }}` anlegen (siehe {ref}`ifdd-lab-setup`) |
| 404 oder „Gateway Timeout“ unter `https://<IFDD_LAB_HOST>/` | der Proxy ist nicht im Lab-Netz: das Netz in `ifdd_proxy_extra_networks` der Proxy-Instanz aufnehmen und ihn neu starten |
| „403: Forbidden“ nach der Anmeldung | der Benutzer ist nicht in `{{ cookiecutter.ifdd_keycloak_lab_users_group }}`; Gruppe in Keycloak zuordnen, dann neu anmelden |
| Anmeldung endet bei Keycloak mit „invalid redirect_uri“ | dem Client `{{ cookiecutter.ifdd_keycloak_lab_client_id }}` fehlt `https://<IFDD_LAB_HOST>/hub/oauth_callback` |
| Hub-Log: certificate verify failed | die CA des Proxys liegt nicht in `certs/`; dorthin kopieren und neu bauen (`./adm_01_build.sh`) |
| der Server startet nicht: Image nicht gefunden | {% if dind %}`./adm_02_run.sh` lädt die Images in den Docker-in-Docker-Daemon; nach jedem Build ausführen{% else %}die Images mit `./adm_01_build.sh` bauen{% endif %} |
| `ifdd_lab.LoginRequired` in einem Notebook | die Keycloak-Sitzung ist zu Ende; Hub-Seite neu laden und neu anmelden |
| ifdd-be antwortet einem Notebook mit 401 | dem Token fehlt die Audience von ifdd-be: der Client braucht den Scope der Backend-Audience (Keycloak-Template) |
| ifdd-be antwortet einem Notebook mit 403 | dem Benutzer fehlt die Rolle oder das Kontextmuster; `/whoami` von ifdd-be zeigt, was das Token enthält |

Logs: `docker compose -f docker-compose-production.yml logs hub`{% if dind %};
die Container der Benutzer: `docker compose -f docker-compose-production.yml exec dind docker ps`{% endif %}.
