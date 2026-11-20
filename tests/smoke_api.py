"""Hub API steps of tests/smoke.sh, run inside the hub container.

    python3 - start|stop USER < smoke_api.py     (token in SMOKE_TOKEN)

start: start the user's server and wait until it is ready.
stop: stop it and wait until it is gone.
Only the standard library: the hub image has no requests.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "http://127.0.0.1:8081/hub/api"
TOKEN = os.environ["SMOKE_TOKEN"]


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(API + path, data=data, method=method,
                                     headers={"Authorization": f"token {TOKEN}",
                                              "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()


def server(user):
    status, model = call("GET", f"/users/{user}")
    assert status == 200, (status, model)
    return model["servers"].get("")


def main(action, user):
    if action == "start":
        status, body = call("POST", f"/users/{user}/server", {})
        assert status in (201, 202), (status, body)
        for _ in range(120):
            current = server(user)
            if current and current.get("ready"):
                print(f"server of {user} ready")
                return
            time.sleep(2)
        raise SystemExit(f"server of {user} not ready after 240 s: {server(user)}")
    if action == "stop":
        status, body = call("DELETE", f"/users/{user}/server")
        assert status in (202, 204), (status, body)
        for _ in range(60):
            if not server(user):
                print(f"server of {user} stopped")
                return
            time.sleep(2)
        raise SystemExit(f"server of {user} still there after 120 s")
    raise SystemExit(f"unknown action {action}")


if __name__ == "__main__":
    main(*sys.argv[1:])
