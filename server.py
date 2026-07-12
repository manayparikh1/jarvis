# MARVIS server — serves index.html and relays chat requests to Hack Club AI.
# Browsers block direct calls to ai.hackclub.com (CORS), so we pass them through here.
# Run:  python3 server.py   then open  http://localhost:8934

import json
import os
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

HACKCLUB = 'https://ai.hackclub.com/proxy/v1/chat/completions'
PORT = 8934
HERE = os.path.dirname(os.path.abspath(__file__))


class Handler(BaseHTTPRequestHandler):
    # any POST is a chat request — no way to 404 by path
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        req = urllib.request.Request(HACKCLUB, data=body, headers={
            'Content-Type': 'application/json',
            'Authorization': self.headers.get('Authorization', ''),
        })
        try:
            with urllib.request.urlopen(req, timeout=90) as res:
                data = res.read()
                status = res.status
        except urllib.error.HTTPError as e:
            data = e.read()
            status = e.code
        except Exception as e:
            data = json.dumps({'error': {'message': str(e)}}).encode()
            status = 502

        # Hack Club sometimes replies with plain text or nothing at all
        # (e.g. "Authentication failed") — always hand the browser valid JSON.
        try:
            json.loads(data)
        except (ValueError, TypeError):
            text = data.decode('utf-8', 'replace').strip() or ('HTTP ' + str(status))
            data = json.dumps({'error': {'message': text}}).encode()

        self.reply(status, data, 'application/json')

    def do_GET(self):
        try:
            with open(os.path.join(HERE, 'index.html'), 'rb') as f:
                self.reply(200, f.read(), 'text/html')
        except FileNotFoundError:
            self.reply(404, b'index.html not found next to server.py', 'text/plain')

    def reply(self, status, data, ctype):
        self.send_response(status)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')  # never serve a stale page
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        print(self.address_string(), '-', fmt % args)


print(f'MARVIS running → http://localhost:{PORT}')
HTTPServer(('localhost', PORT), Handler).serve_forever()
