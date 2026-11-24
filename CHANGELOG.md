# Changelog

The version scheme follows the other IFDD templates: `YY.MM.N`.

## [26.11.11] - 2026-11-24

- Version aligned across all ifdd-de repositories (26.11.11).
- Upstream images: `ifdd_lab_kernel_base_image` minimal-notebook
  2026-11-16 -> 2026-11-23 (still JupyterLab 4.6.6, JupyterHub 6.2.0,
  Python 3.13 according to the build manifests of docker-stacks),
  `ifdd_lab_dind_image` 29.9.2 -> 29.10.0 (`-dind`).
- The packages of the image "default" equal those of the papermill runner of
  ifdd-de/wf 26.11.11 again (comment in `images/default/requirements.txt`).

## [26.11.3] - 2026-11-21

- CI: GitHub Actions pinned to commit SHAs (version as comment),
  `persist-credentials: false` on every checkout; the same in the workflows of
  the instance.
- First version: JupyterHub 6.2.0 with DockerSpawner 14.0.0 and
  OAuthenticator 17.5.0 behind the IFDD proxy, one server per user in an own
  Docker-in-Docker daemon or on the host socket, PostgreSQL 18 as hub
  database, idle culler.
- Login through Keycloak (client `ifdd_keycloak_lab_client_id`, groups for
  users and admins); notebooks call IFDD services with the rights of the
  person logged in (helper `ifdd_lab`, scope `admin:auth_state!user`,
  renewal of the access token 300 s before it expires).
- Switch `ifdd_lab_internet`: without internet access (default) the user
  servers reach only the services behind the proxy and get no Git panel.
- Images of the user servers based on Jupyter Docker Stacks
  (`minimal-notebook`) with the packages of the papermill runner of
  `ifdd-de/wf`, PDF export through LaTeX, no news feed and update check.
