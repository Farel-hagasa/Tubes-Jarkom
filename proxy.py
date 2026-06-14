import os
import time
import hashlib
import threading
from socket import *
from datetime import datetime

PROXY_PORT = 8080

WEB_SERVER_IP = "192.168.100.113"
WEB_SERVER_PORT = 8000

CACHE_DIR = "cache"

if not os.path.exists(CACHE_DIR):
    os.mkdir(CACHE_DIR)

cache_lock = threading.Lock()


def log(ip, path, status, elapsed):

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    print(
        f"[{now}] "
        f"CLIENT={ip} "
        f"URL={path} "
        f"CACHE={status} "
        f"TIME={elapsed:.2f}ms"
    )


def cache_name(url):

    return os.path.join(
        CACHE_DIR,
        hashlib.md5(
            url.encode()
        ).hexdigest()
    )


def build_error_response(code, message):

    body = f"""
    <html>
    <body>
    <h1>{code} {message}</h1>
    </body>
    </html>
    """

    header = (
        f"HTTP/1.1 {code} {message}\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Content-Type: text/html\r\n"
        f"Connection: close\r\n\r\n"
    )

    return header.encode() + body.encode()


def receive_all(sock):

    data = b""

    while True:

        try:

            chunk = sock.recv(4096)

            if not chunk:
                break

            data += chunk

        except:
            break

    return data


def handle_client(client_socket, addr):

    print(
        f"[THREAD-{threading.get_ident()}] "
        f"Handling {addr}"
    )

    start_time = time.time()

    try:

        request = client_socket.recv(
            8192
        )

        if not request:

            client_socket.close()
            return

        request_text = request.decode(
            errors="ignore"
        )

        first_line = request_text.split(
            "\r\n"
        )[0]

        parts = first_line.split()

        if len(parts) < 2:

            client_socket.close()
            return

        path = parts[1]

        cache_file = cache_name(path)

        with cache_lock:

            cache_exists = os.path.exists(
                cache_file
            )

        if cache_exists:

            with open(
                cache_file,
                "rb"
            ) as f:

                response = f.read()

            client_socket.sendall(
                response
            )

            elapsed = (
                time.time()
                - start_time
            ) * 1000

            log(
                addr[0],
                path,
                "HIT",
                elapsed
            )

            client_socket.close()
            return

        server_socket = socket(
            AF_INET,
            SOCK_STREAM
        )

        server_socket.settimeout(
            5
        )

        try:

            server_socket.connect(
                (
                    WEB_SERVER_IP,
                    WEB_SERVER_PORT
                )
            )

            server_socket.sendall(
                request
            )

            response = receive_all(
                server_socket
            )

            if not response:

                response = build_error_response(
                    502,
                    "Bad Gateway"
                )

            with cache_lock:

                with open(
                    cache_file,
                    "wb"
                ) as f:

                    f.write(
                        response
                    )

            client_socket.sendall(
                response
            )

            elapsed = (
                time.time()
                - start_time
            ) * 1000

            log(
                addr[0],
                path,
                "MISS",
                elapsed
            )

        except timeout:

            response = build_error_response(
                504,
                "Gateway Timeout"
            )

            client_socket.sendall(
                response
            )

        except Exception:

            response = build_error_response(
                502,
                "Bad Gateway"
            )

            client_socket.sendall(
                response
            )

        finally:

            server_socket.close()

    except Exception as e:

        print(
            "Proxy Error:",
            e
        )

    finally:

        client_socket.close()


def start_proxy():

    proxy = socket(
        AF_INET,
        SOCK_STREAM
    )

    proxy.setsockopt(
        SOL_SOCKET,
        SO_REUSEADDR,
        1
    )

    proxy.bind(
        ("192.168.100.5", PROXY_PORT)
    )

    proxy.listen(20)

    print(
        f"[PROXY] Listening on "
        f"{PROXY_PORT}"
    )

    while True:

        client_socket, addr = (
            proxy.accept()
        )

        threading.Thread(
            target=handle_client,
            args=(
                client_socket,
                addr
            ),
            daemon=True
        ).start()


if __name__ == "__main__":

    start_proxy()