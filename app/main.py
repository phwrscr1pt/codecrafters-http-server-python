import socket
import threading
import argparse
import gzip
from pathlib import Path


def make_response(method, path, headers, request_body, directory):
    status = "200 OK"
    body = b""
    response_headers = {}

    if path == "/":
        pass
    elif path.startswith("/echo/"):
        body = path[len("/echo/"):].encode()
        response_headers["Content-Type"] = "text/plain"
        encodings = [item.strip() for item in headers.get("accept-encoding", "").split(",")]
        if "gzip" in encodings:
            body = gzip.compress(body)
            response_headers["Content-Encoding"] = "gzip"
    elif path == "/user-agent":
        body = headers.get("user-agent", "").encode()
        response_headers["Content-Type"] = "text/plain"
    elif path.startswith("/files/") and directory is not None:
        root = Path(directory).resolve()
        file_path = (root / path[len("/files/"):]).resolve()
        if not file_path.is_relative_to(root):
            status = "404 Not Found"
        elif method == "POST":
            try:
                file_path.write_bytes(request_body)
                status = "201 Created"
            except OSError:
                status = "500 Internal Server Error"
        else:
            try:
                body = file_path.read_bytes()
                response_headers["Content-Type"] = "application/octet-stream"
            except (FileNotFoundError, IsADirectoryError, PermissionError):
                status = "404 Not Found"
    else:
        status = "404 Not Found"

    response_headers["Content-Length"] = str(len(body))
    close_connection = "close" in [
        item.strip().lower() for item in headers.get("connection", "").split(",")
    ]
    if close_connection:
        response_headers["Connection"] = "close"
    head = f"HTTP/1.1 {status}\r\n"
    head += "".join(f"{name}: {value}\r\n" for name, value in response_headers.items())
    return head.encode() + b"\r\n" + body, close_connection


def handle_client(conn, directory):
    with conn:
        data = b""
        while True:
            while b"\r\n\r\n" not in data:
                chunk = conn.recv(4096)
                if not chunk:
                    return
                data += chunk

            header_data, data = data.split(b"\r\n\r\n", 1)
            lines = header_data.decode("iso-8859-1").split("\r\n")
            method, path, version = lines[0].split(" ")
            headers = {}
            for line in lines[1:]:
                name, value = line.split(":", 1)
                headers[name.lower()] = value.strip()

            content_length = int(headers.get("content-length", "0"))
            while len(data) < content_length:
                chunk = conn.recv(4096)
                if not chunk:
                    return
                data += chunk
            request_body, data = data[:content_length], data[content_length:]

            response, close_connection = make_response(
                method, path, headers, request_body, directory
            )
            conn.sendall(response)
            if close_connection:
                return


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
