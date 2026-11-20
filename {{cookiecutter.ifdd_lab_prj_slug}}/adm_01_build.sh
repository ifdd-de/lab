#!/usr/bin/env bash
# Build the images of this instance: the hub{% if cookiecutter.ifdd_lab_docker_mode == "dind" %}, Docker-in-Docker{% endif %} and the images of
# the user servers (profile "images": {{ cookiecutter.ifdd_lab_images }}).
# Usage: ./adm_01_build.sh
#
# Run again after a change to certs/, hub/, images/, lib/ or the image
# versions, then ./adm_02_run.sh.
set -euo pipefail
cd "$(dirname "$0")"
[ $# -eq 0 ] || { echo "usage: $0" >&2; exit 2; }
COMPOSE=(docker compose -f docker-compose-production.yml)
[ -f .env ] || { echo ".env missing (created at generation from dotenv.dist)" >&2; exit 1; }
certs=$(find certs -maxdepth 1 -type f \( -name '*.crt' -o -name '*.pem' \) | wc -l)
echo "CA certificates in certs/: $certs"
# --pull: fetch the pinned base images again, so security fixes of a moving
# base are picked up.
"${COMPOSE[@]}" --profile images build --pull
