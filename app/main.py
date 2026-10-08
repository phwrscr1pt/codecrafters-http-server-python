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

            request_line = request.split("\r\n")[0]
            path = request.split(" ")[1]

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
            else:
                conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")

if __name__ == "__main__":
    main()
