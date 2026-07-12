# MARVIS server — serves index.html and relays chat requests to Hack Club AI.
# Browsers block direct calls to ai.hackclub.com (CORS), so we pass them through here.
# Run:  python3 server.py   then open  http://localhost:8934

import json
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

HACKCLUB = 'https://ai.hackclub.com/proxy/v1/chat/completions'
PORT = 8934


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/api/chat':
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
            return

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            req = urllib.request.Request(HACKCLUB, data=body, headers={
                'Content-Type': 'application/json',
                'Authorization': self.headers.get('Authorization', ''),
            })

            with urllib.request.urlopen(req, timeout=90) as res:
                data = res.read()
                status = res.status
        except urllib.error.HTTPError as e:
            data = e.read()
            status = e.code
        except Exception as e:
            data = json.dumps({'error': {'message': str(e)}}).encode()
            status = 502

        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        # Serve index.html for everything else
        if self.path == '/' or self.path == '':
            self.path = '/index.html'

        try:
            with open('index.html', 'rb') as f:
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(f.read())
        except FileNotFoundError:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not found')

    def log_message(self, fmt, *args):
        print(self.address_string(), '-', fmt % args)


print(f'MARVIS running → http://localhost:{PORT}')
HTTPServer(('localhost', PORT), Handler).serve_forever()
