"""Reject values that would render but not work.

A mistake shows up here and not later as a hub that does not start, a router
Traefik drops or a login that never succeeds.
"""

import re
import sys

values = {
    "ifdd_lab_prj_slug": "{{ cookiecutter.ifdd_lab_prj_slug }}",
    "ifdd_lab_host": "{{ cookiecutter.ifdd_lab_host }}",
    "ifdd_lab_entrypoint": "{{ cookiecutter.ifdd_lab_entrypoint }}",
    "ifdd_lab_internet": "{{ cookiecutter.ifdd_lab_internet }}",
    "ifdd_lab_docker_mode": "{{ cookiecutter.ifdd_lab_docker_mode }}",
    "ifdd_lab_network": "{{ cookiecutter.ifdd_lab_network }}",
    "ifdd_lab_hub_base_image": "{{ cookiecutter.ifdd_lab_hub_base_image }}",
    "ifdd_lab_kernel_base_image": "{{ cookiecutter.ifdd_lab_kernel_base_image }}",
    "ifdd_lab_postgres_image": "{{ cookiecutter.ifdd_lab_postgres_image }}",
    "ifdd_lab_dind_image": "{{ cookiecutter.ifdd_lab_dind_image }}",
    "ifdd_lab_images": "{{ cookiecutter.ifdd_lab_images }}",
    "ifdd_lab_mem_limit": "{{ cookiecutter.ifdd_lab_mem_limit }}",
    "ifdd_lab_cpu_limit": "{{ cookiecutter.ifdd_lab_cpu_limit }}",
    "ifdd_lab_idle_timeout": "{{ cookiecutter.ifdd_lab_idle_timeout }}",
    "ifdd_keycloak_lab_client_id": "{{ cookiecutter.ifdd_keycloak_lab_client_id }}",
    "ifdd_keycloak_lab_users_group": "{{ cookiecutter.ifdd_keycloak_lab_users_group }}",
    "ifdd_keycloak_lab_admins_group": "{{ cookiecutter.ifdd_keycloak_lab_admins_group }}",
    "ifdd_oidc_realm": "{{ cookiecutter.ifdd_oidc_realm }}",
    "ifdd_be_url": "{{ cookiecutter.ifdd_be_url }}",
}

NAME = r"[A-Za-z0-9][A-Za-z0-9_.-]*"
IMAGE = r"[^\s:@]+(:[^\s:@]+)?(@sha256:[0-9a-f]{64})?"
GROUP = (r"[A-Za-z0-9_.-]+", "a Keycloak group name (no spaces, no commas, no slashes)")
rules = {
    "ifdd_lab_prj_slug": (r"[a-z0-9][a-z0-9_-]*", "lowercase letters, digits, - and _ (compose project name)"),
    "ifdd_lab_host": (r"[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?", "a host name without scheme, port or path"),
    "ifdd_lab_entrypoint": (NAME, "a Traefik entry point name"),
    "ifdd_lab_internet": (r"[yn]", "y or n"),
    "ifdd_lab_docker_mode": (r"dind|socket", "dind or socket"),
    "ifdd_lab_network": (NAME, "a Docker network name"),
    "ifdd_lab_hub_base_image": (IMAGE, "an image reference"),
    "ifdd_lab_kernel_base_image": (IMAGE, "an image reference"),
    "ifdd_lab_postgres_image": (IMAGE, "an image reference"),
    "ifdd_lab_dind_image": (IMAGE, "an image reference"),
    # Each name is a directory images/<name>/ and part of an image tag.
    "ifdd_lab_images": (r"[a-z0-9][a-z0-9-]*(,[a-z0-9][a-z0-9-]*)*", "image names (a-z, 0-9, -) separated by commas, no spaces"),
    # DockerSpawner.mem_limit: a number of bytes with an optional K, M, G or T.
    "ifdd_lab_mem_limit": (r"[0-9]+[KMGT]?", "bytes with an optional suffix K, M, G or T, e.g. 2G"),
    "ifdd_lab_cpu_limit": (r"[0-9]+(\.[0-9]+)?", "a number of CPUs, e.g. 1 or 0.5"),
    "ifdd_lab_idle_timeout": (r"[0-9]+", "seconds"),
    "ifdd_keycloak_lab_client_id": (NAME, "a Keycloak client id"),
    "ifdd_keycloak_lab_users_group": GROUP,
    "ifdd_keycloak_lab_admins_group": GROUP,
    "ifdd_oidc_realm": (r"https?://[A-Za-z0-9.-]+(:[0-9]+)?(/[^\s/]+)*/realms/[^\s/]+", "a Keycloak realm URL without trailing slash"),
    "ifdd_be_url": (r"https?://[A-Za-z0-9.-]+(:[0-9]+)?(/[^\s]*[^/\s])?", "the URL of ifdd-be without trailing slash"),
}

errors = []
for key, (pattern, meaning) in rules.items():
    if not re.fullmatch(pattern, values[key]):
        errors.append(f"{key}={values[key]!r}: expected {meaning}")

images = values["ifdd_lab_images"].split(",")
if len(set(images)) != len(images):
    errors.append("ifdd_lab_images: an image is listed twice")
if values["ifdd_keycloak_lab_users_group"] == values["ifdd_keycloak_lab_admins_group"]:
    errors.append("ifdd_keycloak_lab_users_group and ifdd_keycloak_lab_admins_group must differ")
if values["ifdd_lab_idle_timeout"].isdigit() and int(values["ifdd_lab_idle_timeout"]) < 300:
    errors.append("ifdd_lab_idle_timeout: at least 300 seconds")

if errors:
    print("Invalid template values:", file=sys.stderr)
    for error in errors:
        print(f"  - {error}", file=sys.stderr)
    sys.exit(1)
