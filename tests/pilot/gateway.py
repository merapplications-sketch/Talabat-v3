"""Local-only path bridge for the actual Supabase JS client and app HTML.
Not a deployed API or a replacement for hosted Kong/Realtime/Storage.
"""
import http.server, urllib.parse, urllib.request, urllib.error, pathlib, re
import lab

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def route(self, head=False):
        path = urllib.parse.urlsplit(self.path).path
        target = None
        if path.startswith('/rest/v1'):
            target = 'http://127.0.0.1:3000' + self.path[len('/rest/v1'):]
        elif path.startswith('/auth/v1'):
            target = 'http://127.0.0.1:9999' + self.path[len('/auth/v1'):]
        if target:
            data = self.rfile.read(int(self.headers.get('Content-Length', '0'))) if self.command in ('POST', 'PUT', 'PATCH') else None
            headers = {k: v for k, v in self.headers.items() if k.lower() in ['authorization', 'content-type', 'prefer', 'accept', 'apikey', 'range', 'accept-profile', 'content-profile']}
            req = urllib.request.Request(target, data=data, headers=headers, method=self.command)
            try:
                response = urllib.request.urlopen(req, timeout=20)
            except urllib.error.HTTPError as e:
                response = e
            body = response.read()
            self.send_response(response.status if hasattr(response, 'status') else response.code)
            self.send_header('Content-Type', response.headers.get('Content-Type', 'application/json'))
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            if not head:
                self.wfile.write(body)
            return
        if path == '/supabase.bundle.js':
            p = lab.HERE / 'node_modules/@supabase/supabase-js/dist/umd/supabase.js'
        else:
            p = (lab.ROOT / path.lstrip('/')).resolve()
            if not p.is_relative_to(lab.ROOT) or path.startswith(('/tests/', '/sql/', '/.git', '/docs/')):
                self.send_error(404)
                return
        if not p.is_file():
            self.send_error(404)
            return
        body = p.read_bytes()
        mime = 'application/octet-stream'
        if p.suffix in ('.html', '.js', '.css'):
            s = body.decode()
            if p.suffix == '.html':
                s = re.sub(r'https://cdn\.jsdelivr\.net/npm/@supabase/supabase-js@[^"\']+/dist/umd/supabase\.js', '/supabase.bundle.js', s)
                s = s.replace('https://dzydscryrnahnneydnry.supabase.co', 'http://127.0.0.1:8080').replace('wss://dzydscryrnahnneydnry.supabase.co', 'ws://127.0.0.1:8080')
                mime = 'text/html;charset=utf-8'
            elif p.name == 'talabat-core.js':
                s = re.sub(r"var SB_URL = '[^']+';", "var SB_URL = 'http://127.0.0.1:8080';", s)
                s = re.sub(r"var SB_KEY = '[^']+';", "var SB_KEY = '" + lab.jwt('anon') + "';", s)
                mime = 'application/javascript'
            else:
                mime = 'application/javascript' if p.suffix == '.js' else 'text/css'
            body = s.encode()
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if not head:
            self.wfile.write(body)

    def do_GET(self):
        self.route()

    def do_HEAD(self):
        self.route(True)

    def do_POST(self):
        self.route()

    def do_PATCH(self):
        self.route()

    def do_DELETE(self):
        self.route()

if __name__ == '__main__':
    http.server.ThreadingHTTPServer(('127.0.0.1', 8080), Handler).serve_forever()
