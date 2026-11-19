{%- set dind = cookiecutter.ifdd_lab_docker_mode == "dind" -%}
#!/usr/bin/env bash
# Pre-flight checks, then start the hub.{% if dind %} Loads the images of the user
# servers into the Docker-in-Docker daemon first (it pulls nothing itself).{% endif %}
# Usage: ./adm_02_run.sh
set -euo pipefail
cd "$(dirname "$0")"
[ $# -eq 0 ] || { echo "usage: $0" >&2; exit 2; }
COMPOSE=(docker compose -f docker-compose-production.yml)
NETWORK="{{ cookiecutter.ifdd_lab_network }}"
IMAGES=({% for name in cookiecutter.ifdd_lab_images.split(",") %}"{{ cookiecutter.ifdd_lab_prj_slug }}-{{ name }}:local" {% endfor %})
fail() { echo "ERROR: $*" >&2; exit 1; }

[ -f .env ] || fail ".env missing"
grep -v '^ *#' .env | grep -q '<<generate:' && fail "placeholders <<generate:...>> left in .env"
[ -s secrets/oidc_client_secret ] \
    || fail "secrets/oidc_client_secret is empty or missing - enter the secret of the Keycloak client {{ cookiecutter.ifdd_keycloak_lab_client_id }}"

internal=$(docker network inspect -f '{{ '{{' }}.Internal{{ '}}' }}' "$NETWORK" 2>/dev/null) \
    || fail "Docker network $NETWORK missing - create it once: docker network create --internal $NETWORK (the proxy joins it)"
[ "$internal" = true ] \
    || fail "Docker network $NETWORK is not internal; recreate it: docker network rm $NETWORK && docker network create --internal $NETWORK"

for image in "${IMAGES[@]}"; do
    docker image inspect "$image" >/dev/null 2>&1 || fail "image $image missing - run ./adm_01_build.sh"
done
{%- if dind %}

"${COMPOSE[@]}" up -d --wait dind
for image in "${IMAGES[@]}"; do
    echo "Loading $image into the Docker-in-Docker daemon"
    docker save "$image" | "${COMPOSE[@]}" exec -T dind docker load
done
# The network of the user servers inside the daemon: a user-defined bridge,
# so that the daemon's resolver answers the names of the lab network.
"${COMPOSE[@]}" exec -T dind docker network inspect lab >/dev/null 2>&1 \
    || "${COMPOSE[@]}" exec -T dind docker network create lab >/dev/null
{%- endif %}

"${COMPOSE[@]}" up -d --wait --wait-timeout 300
set -a; . ./.env; set +a
echo "Hub: https://${IFDD_LAB_HOST}/"
