# Docker-in-Docker daemon for the user servers. The upstream image plus the
# instance's CA certificates. The daemon pulls nothing: adm_02_run.sh loads
# the locally built images into it.
#
# The daemon listens only on the unix socket in the volume shared with the
# hub (see docker-compose-production.yml); there is no TCP port.
ARG DIND_IMAGE
FROM ${DIND_IMAGE}

COPY build/install-certs.sh /usr/local/sbin/ifdd-install-certs
COPY certs/ /tmp/ifdd-certs/
RUN sh /usr/local/sbin/ifdd-install-certs /tmp/ifdd-certs
