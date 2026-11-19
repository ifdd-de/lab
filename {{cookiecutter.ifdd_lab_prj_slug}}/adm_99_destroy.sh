{%- set dind = cookiecutter.ifdd_lab_docker_mode == "dind" -%}
#!/usr/bin/env bash
# Delete this instance completely: the containers{% if not dind %} (also the user servers){% endif %}, all volumes
# (database{% if dind %}, Docker-in-Docker data with the home volumes of all users{% endif %}),
# the locally built images and finally this directory with .env and secrets/.
{%- if not dind %}
# The home volumes of the users ({{ cookiecutter.ifdd_lab_prj_slug }}-home-*) are removed too.
{%- endif %}
#
# All notebooks in the homes of the users are lost.
# Usage: ./adm_99_destroy.sh   (asks for confirmation on a terminal)
set -euo pipefail
cd "$(dirname "$0")"
DIR=$(pwd -P)
SLUG="{{ cookiecutter.ifdd_lab_prj_slug }}"
fail() { echo "ERROR: $*" >&2; exit 1; }

[ $# -eq 0 ] || { echo "usage: $0" >&2; exit 2; }
[ -t 0 ] || fail "needs a terminal to confirm; nothing changed"
[ -f docker-compose-production.yml ] || fail "not an instance directory: $DIR"

echo "This deletes the lab instance in $DIR:"
echo "containers, volumes with the homes of all users, local images and the directory itself."
printf "Type 'destroy' to continue: "
answer=""
read -r answer || true
[ "$answer" = destroy ] || fail "not confirmed; nothing changed"

docker compose -f docker-compose-production.yml down --volumes --remove-orphans \
    || echo "WARNING: docker compose down failed" >&2
{%- if not dind %}
for c in $(docker ps -aq --filter "name=^${SLUG}-"); do docker rm -f "$c" >/dev/null || true; done
for v in $(docker volume ls -q --filter "name=^${SLUG}-home-"); do docker volume rm "$v" >/dev/null || true; done
{%- endif %}

for image in "$SLUG-hub:local"{% if dind %} "$SLUG-dind:local"{% endif %}{% for name in cookiecutter.ifdd_lab_images.split(",") %} "$SLUG-{{ name }}:local"{% endfor %}; do
    if docker image inspect "$image" >/dev/null 2>&1; then
        docker image rm "$image" >/dev/null || echo "WARNING: could not remove image $image" >&2
    fi
done

cd ..
rm -rf -- "$DIR"
echo "Deleted $DIR."
