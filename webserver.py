import os
import mimetypes
import threading
from socket import *
from datetime import datetime

HTTP_PORT = 8000
UDP_PORT = 9000

ROOT_DIR = "HTML"


def log_request(ip, path, status):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {ip} {path} {status}")


def build_response(status_code, body, content_type):

    status_text = {
        200: "OK",
        404: "Not Found",
        500: "Internal Server Error"
    }

    header = (
        f"HTTP/1.1 {status_code} {status_text[status_code]}\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Content-Type: {content_type}\r\n"
        "Connection: close\r\n\r\n"
    )

    return header.encode() + body


def load_error_page(code):

    filename = os.path.join(
        ROOT_DIR,
        "status",
        f"{code}.html"
    )

    if os.path.exists(filename):
        with open(filename, "rb") as f:
            return f.read()

    return f"<h1>{code}</h1>".encode()


def handle_http(conn, addr):

    try:

        request = conn.recv(8192).decode(errors="ignore")

        if not request:
            conn.close()
            return

        first_line = request.split("\r\n")[0]

        parts = first_line.split()

        if len(parts) < 2:
            conn.close()
            return

        method = parts[0]
        path = parts[1]

        if method != "GET":

            body = load_error_page(500)

            response = build_response(
                500,
                body,
                "text/html"
            )

            conn.sendall(response)
            conn.close()
            return

        if path == "/":
            path = "/index.html"

        filepath = os.path.join(
            ROOT_DIR,
            path.lstrip("/")
        )

        if not os.path.exists(filepath):

            body = load_error_page(404)

            response = build_response(
                404,
                body,
                "text/html"
            )

            conn.sendall(response)

            log_request(addr[0], path, 404)

            conn.close()
            return

        with open(filepath, "rb") as f:
            body = f.read()

        content_type, _ = mimetypes.guess_type(filepath)

        if content_type is None:
            content_type = "application/octet-stream"

        response = build_response(
            200,
            body,
            content_type
        )

        conn.sendall(response)

        log_request(addr[0], path, 200)

    except Exception as e:

        print("HTTP ERROR:", e)

        try:
            body = load_error_page(500)

            response = build_response(
                500,
                body,
                "text/html"
            )

            conn.sendall(response)

        except:
            pass

    finally:
        conn.close()


def http_server():

    server = socket(AF_INET, SOCK_STREAM)

    server.setsockopt(
        SOL_SOCKET,
        SO_REUSEADDR,
        1
    )

    server.bind(("", HTTP_PORT))
    server.listen(20)

    print(f"[HTTP] Listening on {HTTP_PORT}")

    while True:

        conn, addr = server.accept()

        threading.Thread(
            target=handle_http,
            args=(conn, addr),
            daemon=True
        ).start()


def udp_server():

    server = socket(AF_INET, SOCK_DGRAM)

    server.bind(("", UDP_PORT))

    print(f"[UDP] Listening on {UDP_PORT}")

    while True:

        data, addr = server.recvfrom(4096)

        server.sendto(data, addr)


if __name__ == "__main__":

    threading.Thread(
        target=http_server,
        daemon=True
    ).start()

    threading.Thread(
        target=udp_server,
        daemon=True
    ).start()

    while True:
        pass