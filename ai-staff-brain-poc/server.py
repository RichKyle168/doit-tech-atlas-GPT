from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import base64
import hmac
import os
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
USER = os.environ.get('POC_USERNAME', 'poc')
PASSWORD = os.environ.get('POC_PASSWORD', '')

class Handler(BaseHTTPRequestHandler):
    def respond(self, status, data=b'', mime='text/plain; charset=utf-8', extra=None):
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('X-Robots-Tag', 'noindex, nofollow, noarchive')
        if extra:
            for k,v in extra.items(): self.send_header(k, v)
        self.end_headers()
        if self.command != 'HEAD': self.wfile.write(data)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/health':
            return self.respond(200, b'ok')
        if not PASSWORD:
            return self.respond(503, b'POC authentication not configured.')
        expected = 'Basic ' + base64.b64encode(f'{USER}:{PASSWORD}'.encode()).decode()
        received = self.headers.get('Authorization', '')
        if not hmac.compare_digest(received, expected):
            return self.respond(401, '請使用測試帳號登入。'.encode(), extra={'WWW-Authenticate': 'Basic realm="AI Staff Brain Demo", charset="UTF-8"'})
        if path == '/robots.txt':
            return self.respond(200, b'User-agent: *\nDisallow: /\n')
        if path not in ('/', '/index.html'):
            return self.respond(404, b'Not found')
        body = (ROOT / 'index.html').read_bytes()
        return self.respond(200, body, mime='text/html; charset=utf-8')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8080'))
    print(f'AI Staff Brain demo listening on port {port}', flush=True)
    ThreadingHTTPServer(('0.0.0.0', port), Handler).serve_forever()
