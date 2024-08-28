ARG ERIC_ENM_SLES_BASE_IMAGE_NAME=eric-enm-sles-base
ARG ERIC_ENM_SLES_BASE_IMAGE_REPO=armdocker.rnd.ericsson.se/proj-enm
ARG ERIC_ENM_SLES_BASE_IMAGE_TAG=1.64.0-17

FROM ${ERIC_ENM_SLES_BASE_IMAGE_REPO}/${ERIC_ENM_SLES_BASE_IMAGE_NAME}:${ERIC_ENM_SLES_BASE_IMAGE_TAG}

ARG BUILD_DATE=unspecified
ARG IMAGE_BUILD_VERSION=unspecified
ARG GIT_COMMIT=unspecified
ARG ISO_VERSION=unspecified
ARG RSTATE=unspecified

COPY image_content/service/metrics_client.py /metrics_client.py

# RPMS INSTALLATION
RUN zypper --non-interactive install python3-six python3-pip sysstat && \
    zypper --non-interactive --no-gpg-checks install ERICdbpyu_CXP9039964 && \
    zypper --non-interactive --no-gpg-checks install ERICneo4jutilities_CXP9034750 && \
    zypper --non-interactive --no-gpg-checks install python3-prometheus_client && \
    pip3 uninstall -y PyYAML lxml paramiko netaddr pexpect pytz Jinja2 decorator && \
    zypper --non-interactive install python3-PyYAML python3-lxml python3-paramiko python3-netaddr \
    python3-pexpect python3-pytz python3-Jinja2 python3-decorator

CMD ["python3", "/metrics_client.py"]

