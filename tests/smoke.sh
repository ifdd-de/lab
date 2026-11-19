#!/usr/bin/env bash
# Smoke test of a rendered instance with the real images (CI, template-test.yml).
#
#   tests/smoke.sh INSTANCE_DIR
#
# Builds and starts the instance without Keycloak: a hub admin "smoke" from
# hub/config.d/ gets an API token from `jupyterhub token`, starts a server
# through the hub API, and the checks run inside the user container:
# packages and helper, Git panel only with internet access, PDF through
# LaTeX, internet access as configured, the hub API reachable with the
# server's token, the home kept across a restart, no root.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
cd "${1:?usage: smoke.sh INSTANCE_DIR}"
COMPOSE=(docker compose -f docker-compose-production.yml)
cfg() { python3 -c "import yaml,sys; d=yaml.safe_load(open('docker-compose-production.yml')); print(eval(sys.argv[1]))" "$1"; }
NET=$(cfg 'd["networks"]["lab"]["name"]')
SLUG=$(cfg 'd["services"]["hub"]["environment"]["IFDD_LAB_SLUG"]')
INTERNET=$(cfg '"y" if "egress" in d["networks"] else "n"')
DIND=$(cfg '"y" if "dind" in d["services"] else "n"')
USER_NAME=smoke
echo "instance $SLUG: network $NET, internet $INTERNET, dind $DIND"

docker network create --internal "$NET" >/dev/null
printf 'stand-in\n' > secrets/oidc_client_secret
cat > hub/config.d/smoke.py <<'EOF'
# Smoke test only: an admin without Keycloak.
c.Authenticator.admin_users = {"smoke"}
EOF

./adm_01_build.sh
./adm_02_run.sh

TOKEN=$("${COMPOSE[@]}" exec -T hub jupyterhub token -f /srv/jupyterhub/jupyterhub_config.py "$USER_NAME" | tail -1)
[ -n "$TOKEN" ]
api() { "${COMPOSE[@]}" exec -T -e SMOKE_TOKEN="$TOKEN" hub python3 - "$@" < "$HERE/smoke_api.py"; }
if [ "$DIND" = y ]; then
    in_user() { "${COMPOSE[@]}" exec -T dind docker exec -i "$SLUG-$USER_NAME" "$@"; }
else
    in_user() { docker exec -i "$SLUG-$USER_NAME" "$@"; }
fi

api start "$USER_NAME"

echo "--- runs as jovyan, not root"
test "$(in_user id -u)" = 1000

echo "--- packages and helper"
in_user python -c "import ifdd_lab, papermill, pandas, requests, sqlalchemy; print('ok')"

echo "--- Git panel only with internet access"
if in_user pip show -q jupyterlab-git >/dev/null 2>&1; then git_panel=y; else git_panel=n; fi
test "$git_panel" = "$INTERNET"

echo "--- no news feed, no update check"
in_user python - <<'EOF'
from traitlets.config.loader import PyFileConfigLoader
c = PyFileConfigLoader("jupyter_server_config.py", path="/etc/jupyter").load_config()
assert c.LabApp.news_url is None, c.LabApp.news_url
assert c.LabApp.check_for_updates_class == "jupyterlab.NeverCheckForUpdate"
print("ok")
EOF

echo "--- PDF through LaTeX"
in_user bash -c 'cd /tmp && python -c "
import nbformat
nb = nbformat.v4.new_notebook(cells=[nbformat.v4.new_markdown_cell(\"# Smoke \$x^2\$\"), nbformat.v4.new_code_cell(\"print(6 * 7)\")])
nbformat.write(nb, \"smoke.ipynb\")" && jupyter nbconvert --to pdf --execute smoke.ipynb >/dev/null 2>&1 && test -s smoke.pdf && head -c 5 smoke.pdf'
echo

echo "--- internet access as configured"
if in_user python -c "import urllib.request; urllib.request.urlopen('https://pypi.org/simple/', timeout=15)" 2>/dev/null; then
    reached=y
else
    reached=n
fi
test "$reached" = "$INTERNET"

echo "--- the hub API answers the server's token (auth state readable)"
in_user python - <<'EOF'
import ifdd_lab
try:
    ifdd_lab.access_token()
except ifdd_lab.LoginRequired as error:
    # The smoke user never logged in through Keycloak: no tokens. A refusal
    # (401/403) or an unreachable hub would be a different error.
    assert "no access token" in str(error), error
    print("ok:", error)
else:
    raise SystemExit("unexpected token for a user without login")
EOF

echo "--- the home survives a restart of the server"
in_user bash -c 'echo kept > /home/jovyan/smoke.txt'
api stop "$USER_NAME"
api start "$USER_NAME"
test "$(in_user cat /home/jovyan/smoke.txt)" = kept

api stop "$USER_NAME"
echo "smoke test passed"
