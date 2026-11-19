"""Static checks of the generated configuration (pytest tests).

They read only files of this instance and need neither Docker nor a hub.
"""

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent


def compose():
    return yaml.safe_load((ROOT / "docker-compose-production.yml").read_text())


def env_of(service):
    return compose()["services"][service]["environment"]


def labels(service):
    return dict(item.split("=", 1) for item in compose()["services"][service].get("labels", []))


def dind_mode():
    return "dind" in compose()["services"]


def internet():
    return "egress" in compose()["networks"]


def test_no_service_publishes_a_port():
    for name, service in compose()["services"].items():
        assert not service.get("ports"), f"{name} publishes ports"


def test_postgres_only_on_internal_network():
    data = compose()
    assert data["services"]["postgres"]["networks"] == ["db"]
    assert data["networks"]["db"]["internal"] is True


def test_lab_network_is_external_and_named():
    lab = compose()["networks"]["lab"]
    assert lab["external"] is True
    assert re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", lab["name"])


def test_hub_is_not_on_the_proxy_network():
    # The proxy joins the lab network; the hub needs no other.
    networks = set(compose()["services"]["hub"]["networks"])
    assert networks <= {"db", "lab", "egress"}


def test_router_uses_the_lab_network_and_no_tls():
    lab = compose()["networks"]["lab"]["name"]
    hub = labels("hub")
    assert hub["traefik.docker.network"] == lab
    assert not [k for k in hub if ".tls" in k], "router labels must not carry tls (see README)"
    assert hub[next(k for k in hub if k.endswith(".rule"))] == "Host(`${IFDD_LAB_HOST}`)"


def test_docker_access():
    services = compose()["services"]
    hub = services["hub"]
    if dind_mode():
        dind = services["dind"]
        assert dind["command"] == ["dockerd", "--host=unix:///dind/docker.sock"], "DinD must not listen on TCP"
        assert "dind-socket:/dind" in hub["volumes"]
        assert not any("docker.sock:" in v for v in hub["volumes"]), "DinD mode must not mount the host socket"
        assert hub["environment"]["IFDD_LAB_SPAWN_NETWORK"] == "lab"
        assert hub["environment"]["IFDD_LAB_DIND_HOST"] in dind["networks"]["lab"]["aliases"]
        assert (ROOT / "dind" / "Dockerfile").exists()
    else:
        assert "/var/run/docker.sock:/var/run/docker.sock" in hub["volumes"]
        assert hub["environment"]["IFDD_LAB_SPAWN_NETWORK"] == compose()["networks"]["lab"]["name"]
        assert not (ROOT / "dind").exists()


def test_internet_switch():
    services = compose()["services"]
    holder = services["dind"] if dind_mode() else services["hub"]
    git = {s["build"]["args"]["IFDD_LAB_GIT"] for n, s in services.items() if n.startswith("image-")}
    if internet():
        assert "egress" in holder["networks"]
        assert git == {"y"}
        assert compose()["networks"]["egress"].get("internal") is not True
    else:
        for name, service in services.items():
            assert "egress" not in (service.get("networks") or {}), name
        assert git == {"n"}
        assert "IFDD_LAB_EGRESS_NETWORK" not in env_of("hub")


def test_every_image_is_built_and_offered():
    services = compose()["services"]
    offered = dict(item.split("=", 1) for item in env_of("hub")["IFDD_LAB_IMAGES"].split(","))
    built = {n.removeprefix("image-"): s for n, s in services.items() if n.startswith("image-")}
    assert set(offered) == set(built)
    for name, service in built.items():
        assert service["profiles"] == ["images"]
        assert service["image"] == offered[name]
        assert service["build"]["dockerfile"] == f"images/{name}/Dockerfile"
        assert service["build"]["args"]["IMAGE_DIR"] == f"images/{name}"
        assert (ROOT / "images" / name / "Dockerfile").exists()


def test_secrets_reach_the_hub_only_from_env_and_files():
    hub = env_of("hub")
    for key in ("IFDD_LAB_DB_PASSWORD", "JUPYTERHUB_CRYPT_KEY", "JPY_COOKIE_SECRET"):
        assert hub[key] == "${" + key + ":?set in .env}"
    assert "./secrets/oidc_client_secret:/run/ifdd/oidc_client_secret:ro" in compose()["services"]["hub"]["volumes"]
    assert hub["IFDD_LAB_CLIENT_SECRET_FILE"] == "/run/ifdd/oidc_client_secret"


@pytest.mark.parametrize("name", ["IFDD_LAB_DB_PASSWORD", "JUPYTERHUB_CRYPT_KEY", "JPY_COOKIE_SECRET"])
def test_generated_values_are_placeholders(name):
    dist = (ROOT / "dotenv.dist").read_text()
    assert re.search(rf"^{name}=<<generate:", dist, re.M)


def test_crypt_and_cookie_keys_are_32_bytes_hex():
    dist = (ROOT / "dotenv.dist").read_text()
    for name in ("JUPYTERHUB_CRYPT_KEY", "JPY_COOKIE_SECRET"):
        assert re.search(rf"^{name}=<<generate:hex:32>>$", dist, re.M), name


def test_instance_owned_paths_are_git_ignored():
    ignored = (ROOT / ".gitignore").read_text().splitlines()
    for line in (".env", "secrets/*", "certs/*", "hub/config.d/*"):
        assert line in ignored


def test_images_turn_off_news_and_update_checks():
    for directory in (ROOT / "images").iterdir():
        config = (directory / "jupyter_server_config.py").read_text()
        assert "c.LabApp.news_url = None" in config
        assert 'c.LabApp.check_for_updates_class = "jupyterlab.NeverCheckForUpdate"' in config
        assert '"checkForUpdates": false' in (directory / "overrides.json").read_text()


def test_scripts_are_executable():
    for script in ROOT.glob("adm_*.sh"):
        assert script.stat().st_mode & 0o111, script
