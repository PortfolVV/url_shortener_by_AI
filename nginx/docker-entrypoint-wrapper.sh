#!/bin/sh
# Resolve which DNS server Nginx should use for dynamic upstream resolution.
#
# Docker's embedded DNS is 127.0.0.11, while Podman (aardvark-dns) advertises
# the network gateway in /etc/resolv.conf. Reading resolv.conf keeps the same
# image working on both runtimes without hardcoding an address.
set -e

if [ -z "${NGINX_RESOLVER:-}" ]; then
    NGINX_RESOLVER="$(awk '$1 == "nameserver" { print $2; exit }' /etc/resolv.conf 2>/dev/null || true)"
fi

if [ -z "$NGINX_RESOLVER" ]; then
    NGINX_RESOLVER="127.0.0.11"
fi

export NGINX_RESOLVER
echo "nginx-entrypoint: using DNS resolver ${NGINX_RESOLVER}"

exec /docker-entrypoint.sh "$@"
