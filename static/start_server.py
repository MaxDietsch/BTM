import http.server
import socketserver
import json

PORT = 8000
DIRECTORY = "."  # The directory where your HTML and other static files are located

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == '/':
            self.path = './landing_page.html'
        elif self.path == 'favicon.ico':
            self.send_response(204)  # No Content
            self.end_headers()
            return
        return super().do_GET()

    def do_POST(self):
        if self.path == '/register':
            # Determine the length of the data
            content_length = int(self.headers['Content-Length'])
            # Read the POST data
            post_data = self.rfile.read(content_length)
            # Parse the JSON data
            data = json.loads(post_data)
            
            # Extract username and password
            username = data.get('username')
            password = data.get('password')
            
            # Print the username and password to the console
            print(f"Received registration: username = {username}, password = {password}")
            
            # Send a response back to the client
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'message': 'Registration successful'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

Handler = CustomHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()
