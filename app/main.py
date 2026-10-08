import socket  # noqa: F401


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # TODO: Uncomment the code below to pass the first stage
    
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    while True:
        conn, addr = server_socket.accept()
        with conn:
            request = conn.recv(1024).decode()

            header_section = request.split("\r\n\r\n", 1)[0]
            lines = header_section.split("\r\n")

            path = lines[0].split(" ")[1]

            headers = {}
            for line in lines[1:]:
                name, value = line.split(":", 1)
                headers[name.lower()] = value.strip()

            if path == "/":
                conn.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
            elif path.startswith("/echo/"):
                body = path[len("/echo/"):].encode()

                headers = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/plain\r\n"
                    f"Content-Length: {len(body)}\r\n"
                    "\r\n"
                ).encode()

                conn.sendall(headers + body)
            elif path == "/user-agent":
                body = headers.get("user-agent", "").encode()

                response_headers = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/plain\r\n"
                    f"Content-Length: {len(body)}\r\n"
                    "\r\n"
                ).encode()
                
                conn.sendall(response_headers + body)
            else:
                conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")

if __name__ == "__main__":
    main()
