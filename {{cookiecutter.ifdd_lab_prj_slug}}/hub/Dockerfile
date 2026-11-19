# Hub image of this instance: JupyterHub with configurable-http-proxy,
# OAuthenticator, DockerSpawner and the idle culler, plus the instance's CA
# certificates (certs/) in the system trust store (login at Keycloak, also
# through a TLS-inspecting proxy during the build).
#
# The base is the Node.js image (configurable-http-proxy needs Node.js 22 or
# later); Python comes from its Debian packages. Build context is the
# instance root (see .dockerignore); built by adm_01_build.sh, never published.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

COPY build/install-certs.sh /usr/local/sbin/ifdd-install-certs
COPY certs/ /tmp/ifdd-certs/
RUN sh /usr/local/sbin/ifdd-install-certs /tmp/ifdd-certs

ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    PIP_CERT=/etc/ssl/certs/ca-certificates.crt \
    NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-venv ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY hub/requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/hub \
 && /opt/hub/bin/pip install --no-cache-dir -r /tmp/requirements.txt \
 && rm /tmp/requirements.txt \
 && npm install -g --no-fund --no-audit configurable-http-proxy@5.4.0 \
 && npm cache clean --force

ENV PATH=/opt/hub/bin:$PATH
WORKDIR /srv/jupyterhub
COPY hub/jupyterhub_config.py hub/ifdd_lab_hub.py /srv/jupyterhub/
RUN jupyterhub --version && configurable-http-proxy --version

# Root: needed for the Docker socket (both modes), see README.
CMD ["jupyterhub", "-f", "/srv/jupyterhub/jupyterhub_config.py"]
