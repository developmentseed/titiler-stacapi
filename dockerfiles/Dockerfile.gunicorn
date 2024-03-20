ARG PYTHON_VERSION=3.12

FROM ghcr.io/vincentsarago/uvicorn-gunicorn:${PYTHON_VERSION}


ENV CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

WORKDIR /tmp

COPY titiler/ titiler/
COPY pyproject.toml pyproject.toml
COPY README.md README.md
COPY LICENSE LICENSE

RUN python -m pip install --no-cache-dir --upgrade .
RUN rm -rf titiler/ pyproject.toml README.md LICENSE

ENV MODULE_NAME titiler.stacapi.main
ENV VARIABLE_NAME app
