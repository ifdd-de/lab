(ifdd-lab-operations)=
# Betrieb
{%- set dind = cookiecutter.ifdd_lab_docker_mode == "dind" %}

## Starten, Stoppen, Status

```bash
./adm_02_run.sh                                         # starten oder neu starten
docker compose -f docker-compose-production.yml ps
docker compose -f docker-compose-production.yml logs -f hub
docker compose -f docker-compose-production.yml down    # Volumes bleiben
```

Der Hub beendet beim Stoppen die Server der Benutzer; ihre Homes bleiben.

## Server der Benutzer

| Regel | Wert |
|---|---|
| ein Server je Benutzer | benannte Server sind aus |
| Image | beim Start gewählt, wenn es mehr als eines gibt (`{{ cookiecutter.ifdd_lab_images }}`) |
| Speicher, CPUs | `{{ cookiecutter.ifdd_lab_mem_limit }}`, `{{ cookiecutter.ifdd_lab_cpu_limit }}` |
| Leerlauf | nach {{ cookiecutter.ifdd_lab_idle_timeout }} s ohne Aktivität beendet (jupyterhub-idle-culler) |
| Home | Volume `{{ cookiecutter.ifdd_lab_prj_slug }}-home-<benutzer>` unter `/home/jovyan`{% if dind %}, im Docker-in-Docker-Daemon (Volume `dind-data`){% endif %}; der Container wird beim Beenden entfernt, das Home bleibt |

Mitglieder von `{{ cookiecutter.ifdd_keycloak_lab_admins_group }}` sehen die
Server aller Benutzer auf der Admin-Seite des Hubs (`/hub/admin`) und können
sie beenden.

## Anmeldung und Tokens

Der Hub hält die Tokens einer Anmeldung in seiner Datenbank, verschlüsselt
mit `JUPYTERHUB_CRYPT_KEY`. Er erneuert das Access-Token mit dem
Refresh-Token, wenn weniger als fünf Minuten übrig sind. Die Keycloak-Sitzung
des Clients `{{ cookiecutter.ifdd_keycloak_lab_client_id }}` endet nach langem
Leerlauf oder bei ihrer Höchstdauer (Einstellungen des Realms und des
Clients); dann schickt der Hub den Benutzer erneut zur Anmeldung, und
`ifdd_lab` meldet in einem laufenden Notebook `LoginRequired`.

## Sicherung

```{note}
Nicht getestet: Für die Hub-Datenbank und die Homes gibt es noch keine
Sicherung. Die Homes liegen {% if dind %}im Volume `dind-data`{% else %}in den Volumes `{{ cookiecutter.ifdd_lab_prj_slug }}-home-*`{% endif %}; wer {% if dind %}es{% else %}sie{% endif %} löscht, löscht jedes Notebook jedes Benutzers.
```

## Entfernen

`./adm_99_destroy.sh` fragt nach einer Bestätigung und löscht dann
Container, Volumes (mit den Homes aller Benutzer), lokale Images und das
Instanz-Verzeichnis.
