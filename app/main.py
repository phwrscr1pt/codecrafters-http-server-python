import socket
import threading
import argparse
from pathlib import Path


def handle_client(conn, directory):
    with conn:
        data = b""
        # TCP can deliver headers and body across multiple reads.
        while b"\r\n\r\n" not in data:
            chunk = conn.recv(4096)
            if not chunk:
                return
            data += chunk

        header_data, body = data.split(b"\r\n\r\n", 1)
        lines = header_data.decode("iso-8859-1").split("\r\n")
        method, path, version = lines[0].split(" ")

        headers = {}
        for line in lines[1:]:
            name, value = line.split(":", 1)
            headers[name.lower()] = value.strip()

        content_length = int(headers.get("content-length", "0"))
        while len(body) < content_length:
            chunk = conn.recv(content_length - len(body))
            if not chunk:
                return
            body += chunk
        request_body = body[:content_length]

        if path == "/":
            conn.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
        elif path.startswith("/echo/"):
            body = path[len("/echo/"):].encode()
            encoding_header = ""
            if headers.get("accept-encoding", "") == "gzip":
                encoding_header = "Content-Encoding: gzip\r\n"

            response_headers = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n"
                f"{encoding_header}"
                f"Content-Length: {len(body)}\r\n"
                "\r\n"
            ).encode()

            conn.sendall(response_headers + body)
        elif path == "/user-agent":
            body = headers.get("user-agent", "").encode()

            response_headers = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n"
                f"Content-Length: {len(body)}\r\n"
                "\r\n"
            ).encode()
            
            conn.sendall(response_headers + body)
        elif path.startswith("/files/"):
            if directory is None:
                conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
                return

            filename = path[len("/files/"):]
            root = Path(directory).resolve()
            file_path = (root / filename).resolve()

            if not file_path.is_relative_to(root):
                conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
                return

            if method == "POST":
                try:
                    file_path.write_bytes(request_body)
                except OSError:
                    conn.sendall(
                        b"HTTP/1.1 500 Internal Server Error\r\n"
                        b"Content-Length: 0\r\n\r\n"
                    )
                    return
                conn.sendall(
                    b"HTTP/1.1 201 Created\r\nContent-Length: 0\r\n\r\n"
                )
                return

            try:
                body = file_path.read_bytes()
            except (FileNotFoundError, IsADirectoryError, PermissionError):
                conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
                return

            response_headers = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/octet-stream\r\n"
                f"Content-Length: {len(body)}\r\n"
                "\r\n"
            ).encode()

            conn.sendall(response_headers + body)
        else:
            conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", default=None)
    args = parser.parse_args()

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    while True:
        conn, addr = server_socket.accept()
        threading.Thread(
            target=handle_client,
            args=(conn, args.directory),
            daemon=True,
        ).start()


if __name__ == "__main__":
    main()
