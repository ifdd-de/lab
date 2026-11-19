# Image of the user servers ("default"): a Jupyter Docker Stacks image with
#   - the instance's CA certificates (certs/) in the system trust store, used
#     by Python's ssl module, requests and pip (SSL_CERT_FILE and friends);
#   - the packages of requirements.txt (those of the papermill runner of
#     ifdd-de/wf, so notebooks see the same libraries there);
#   - with internet access (ifdd_lab_internet=y) the Git extension of
#     JupyterLab (requirements-git.txt);
#   - the helper ifdd_lab (lib/ifdd_lab.py) for calls with the user's token;
#   - JupyterLab without news feed and update check (no requests outside).
#
# The base (minimal-notebook) brings git, pandoc and XeLaTeX, so "Save and
# Export Notebook As - PDF" works through LaTeX.
#
# LOCAL ONLY: built by adm_01_build.sh and never pushed; it carries the CA
# certificates. Another image: a directory images/<name>/ (start with a copy
# of this one) and its name in IFDD_LAB_IMAGES; IMAGE_DIR selects the
# directory. Build context is the instance root (see .dockerignore).
ARG BASE_IMAGE
FROM ${BASE_IMAGE}
ARG IMAGE_DIR=images/default
ARG IFDD_LAB_GIT=n

USER root

COPY build/install-certs.sh /usr/local/sbin/ifdd-install-certs
COPY certs/ /tmp/ifdd-certs/
RUN sh /usr/local/sbin/ifdd-install-certs /tmp/ifdd-certs

ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    PIP_CERT=/etc/ssl/certs/ca-certificates.crt

COPY ${IMAGE_DIR}/requirements.txt ${IMAGE_DIR}/requirements-git.txt /tmp/ifdd/
COPY ${IMAGE_DIR}/jupyter_server_config.py ${IMAGE_DIR}/overrides.json /tmp/ifdd/
COPY lib/ifdd_lab.py /tmp/ifdd/
RUN set -eu; \
    pip install --no-cache-dir -r /tmp/ifdd/requirements.txt; \
    if [ "$IFDD_LAB_GIT" = y ]; then pip install --no-cache-dir -r /tmp/ifdd/requirements-git.txt; fi; \
    cp /tmp/ifdd/ifdd_lab.py "$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')/"; \
    cat /tmp/ifdd/jupyter_server_config.py >> /etc/jupyter/jupyter_server_config.py; \
    mkdir -p "${CONDA_DIR}/share/jupyter/lab/settings"; \
    cp /tmp/ifdd/overrides.json "${CONDA_DIR}/share/jupyter/lab/settings/overrides.json"; \
    rm -rf /tmp/ifdd; \
    fix-permissions "${CONDA_DIR}"; \
    python -c "import ifdd_lab, papermill, pandas, requests, sqlalchemy; print('packages ok')"

USER ${NB_UID}
