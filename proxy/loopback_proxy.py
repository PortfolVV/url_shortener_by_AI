#!/usr/bin/env python3
"""Small TCP proxy that clamps the TCP MSS on the browser-facing socket.

Why this exists
---------------
On the machine this project was developed on, the loopback interface has an
MTU of 65536 bytes.  Podman's rootless port forwarder (``rootlessport``) and
the container network inherit that value, so TCP negotiates segments of tens
of kilobytes.  On this kernel those large segments are never delivered: a
plain ``python3 -m http.server`` and a plain Nginx both hang for any response
larger than ~12 KiB, while the server logs a normal ``200`` response.  The
Vite bundle is ~167 KiB, so the browser waits forever and the UI never boots.

The forwarder cannot be configured to advertise a smaller MSS, but a socket
can: ``TCP_MAXSEG`` set on the *listening* socket is inherited by accepted
connections, and setting it on the upstream socket before ``connect()`` makes
the upstream advertise the same limit.  The result is a connection that is
usable on this host without changing system-wide networking (which would
require root).

This proxy is deliberately transparent: Nginx remains the static file server,
load balancer and edge rate limiter.  The proxy only forwards bytes between
the browser and Nginx.

It is harmless on a healthy host as well; it just adds one local TCP hop.
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
import threading

# Linux value of IPPROTO_TCP / TCP_MAXSEG is stable; the constant is exposed by
# Python on Linux.  Fall back to 2 for the unusual case where it is missing.
TCP_MAXSEG = getattr(socket, "TCP_MAXSEG", 2)
TCP_NODELAY = getattr(socket, "TCP_NODELAY", 1)


def _set_tcp_options(sock: socket.socket, mss: int) -> None:
    """Apply the options that keep this host's TCP stack out of trouble."""
    try:
        sock.setsockopt(socket.IPPROTO_TCP, TCP_MAXSEG, mss)
    except OSError:
        # Not fatal: the proxy still works on systems where the option is
        # unavailable, they just do not need the workaround.
        pass
    try:
        sock.setsockopt(socket.IPPROTO_TCP, TCP_NODELAY, 1)
    except OSError:
        pass


def _make_listener(family: int, address: str, port: int, mss: int) -> socket.socket:
    sock = socket.socket(family, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if family == socket.AF_INET6:
        # Listen on IPv6 only; a separate IPv4 listener is created below.  This
        # avoids platform differences in the IPV6_V6ONLY default.
        try:
            sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
        except OSError:
            pass
    # Must be set before bind()/listen(): accepted sockets inherit it.
    _set_tcp_options(sock, mss)
    sock.bind((address, port))
    sock.listen(128)
    return sock


def _connect_upstream(host: str, port: int, mss: int) -> socket.socket:
    last_error: OSError | None = None
    for family, socktype, proto, _canonname, sockaddr in socket.getaddrinfo(
        host, port, type=socket.SOCK_STREAM
    ):
        upstream = socket.socket(family, socktype, proto)
        try:
            # Before connect(): this value is advertised in the SYN, so the
            # server (Nginx through rootlessport) also uses small segments.
            _set_tcp_options(upstream, mss)
            upstream.connect(sockaddr)
            return upstream
        except OSError as exc:
            last_error = exc
            upstream.close()
    raise last_error or OSError(f"cannot connect to {host}:{port}")


def _proxy_protocol_header(client: socket.socket) -> bytes:
    """Build a PROXY protocol v1 header for the browser-facing connection.

    Nginx listens with ``proxy_protocol`` so it can still see the real client
    address even though every connection now arrives from this forwarder.
    Unknown address families fall back to ``PROXY UNKNOWN``, which Nginx
    accepts (the address is then the proxy's address).
    """
    try:
        peer = client.getpeername()
        local = client.getsockname()
        source_ip, source_port = str(peer[0]), int(peer[1])
        dest_ip, dest_port = str(local[0]), int(local[1])
    except (OSError, IndexError, TypeError, ValueError):
        return b"PROXY UNKNOWN\r\n"

    family = "TCP6" if ":" in source_ip else "TCP4"
    return (
        f"PROXY {family} {source_ip} {dest_ip} {source_port} {dest_port}\r\n"
    ).encode("ascii", "replace")


def _pipe(src: socket.socket, dst: socket.socket) -> None:
    try:
        while True:
            chunk = src.recv(65536)
            if not chunk:
                break
            dst.sendall(chunk)
    except OSError:
        # Normal on browser tab close, reload, proxy shutdown, etc.
        pass
    finally:
        try:
            dst.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def _handle_client(
    client: socket.socket,
    target_host: str,
    target_port: int,
    mss: int,
    proxy_protocol: bool,
) -> None:
    upstream: socket.socket | None = None
    try:
        _set_tcp_options(client, mss)
        upstream = _connect_upstream(target_host, target_port, mss)
        if proxy_protocol:
            upstream.sendall(_proxy_protocol_header(client))
        back = threading.Thread(
            target=_pipe, args=(upstream, client), daemon=True
        )
        back.start()
        # Keep forwarding the request direction on this thread.
        _pipe(client, upstream)
        back.join(timeout=5)
    except OSError as exc:
        print(f"proxy: connection failed: {exc}", file=sys.stderr, flush=True)
    finally:
        for sock in (upstream, client):
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass


def _accept_loop(
    listener: socket.socket,
    target_host: str,
    target_port: int,
    mss: int,
    proxy_protocol: bool,
) -> None:
    while True:
        try:
            client, _peer = listener.accept()
        except OSError:
            return
        threading.Thread(
            target=_handle_client,
            args=(client, target_host, target_port, mss, proxy_protocol),
            daemon=True,
        ).start()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--listen-port",
        type=int,
        default=int(os.getenv("PROXY_LISTEN_PORT", "8080")),
        help="host port the browser connects to (default: 8080)",
    )
    parser.add_argument(
        "--target-host",
        default=os.getenv("PROXY_TARGET_HOST", "127.0.0.1"),
        help="Nginx host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--target-port",
        type=int,
        default=int(os.getenv("PROXY_TARGET_PORT", "8081")),
        help="Nginx port (default: 8081)",
    )
    parser.add_argument(
        "--mss",
        type=int,
        default=int(os.getenv("PROXY_MSS", "1200")),
        help="TCP MSS to advertise (default: 1200)",
    )
    parser.add_argument(
        "--no-proxy-protocol",
        dest="proxy_protocol",
        action="store_false",
        help=(
            "do not prepend a PROXY v1 header; disable only if the target "
            "does not listen with proxy_protocol"
        ),
    )
    parser.set_defaults(proxy_protocol=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if not 536 <= args.mss <= 65535:
        print("proxy: --mss must be between 536 and 65535", file=sys.stderr)
        return 2

    listeners: list[socket.socket] = []
    # Bind IPv4 and IPv6 separately so ``localhost`` works regardless of which
    # address family the browser tries first.
    for family, address in ((socket.AF_INET, "0.0.0.0"), (socket.AF_INET6, "::")):
        try:
            listeners.append(
                _make_listener(family, address, args.listen_port, args.mss)
            )
        except OSError as exc:
            if family == socket.AF_INET:
                print(f"proxy: cannot listen on IPv4: {exc}", file=sys.stderr)
                return 1
            print(f"proxy: IPv6 listener disabled: {exc}", file=sys.stderr, flush=True)

    print(
        "proxy: listening on "
        + ", ".join(
            f"[{sock.family.name}]:{args.listen_port}" for sock in listeners
        )
        + f" -> {args.target_host}:{args.target_port} (MSS={args.mss}"
        + (", PROXY v1)" if args.proxy_protocol else ")"),
        flush=True,
    )

    threads = [
        threading.Thread(
            target=_accept_loop,
            args=(
                listener,
                args.target_host,
                args.target_port,
                args.mss,
                args.proxy_protocol,
            ),
            daemon=True,
        )
        for listener in listeners
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
