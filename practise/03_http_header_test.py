from http.server import HTTPServer, BaseHTTPRequestHandler

class HeaderHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.print_headers()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_POST(self):
        self.print_headers()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_HEAD(self):
        self.print_headers()
        self.send_response(200)
        self.end_headers()

    def print_headers(self):
        print(f"\n--- New Request: {self.command} {self.path} ---")
        print(self.headers)


if __name__ == "__main__":
    # 监听所有网卡上的 8080 端口
    server = HTTPServer(('0.0.0.0', 8091), HeaderHandler)
    print("Starting server on port 8091...")
    server.serve_forever()

