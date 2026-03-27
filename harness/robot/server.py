#!/usr/bin/env python3
"""0-1 Project Dashboard Server"""
import http.server, socketserver, json, subprocess, os, urllib.parse, sys

DIR = '/Users/lr/.openclaw/workspace/harness/robot'
WORKSPACE = '/Users/lr/.openclaw/workspace'
PORT = 18999
MDVIEW = os.path.join(WORKSPACE, 'tools', 'mdview.py')
MDVIEW_HTML_DIR = os.path.join(WORKSPACE, '.review', 'html')

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def translate_path(self, path):
        parsed = urllib.parse.urlparse(path)
        url_path = parsed.path
        if url_path.startswith('/review/') or url_path == '/review':
            relative = url_path[len('/review/'):]
            return os.path.join(MDVIEW_HTML_DIR, relative)
        return super().translate_path(path)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == '/api/open':
            params = urllib.parse.parse_qs(parsed.query)
            file_param = params.get('file', [''])[0]
            if not file_param:
                self._json(400, {'error': 'missing file param'})
                return

            if not file_param.startswith('/'):
                resolved = os.path.normpath(os.path.join(WORKSPACE, file_param))
            else:
                resolved = os.path.normpath(file_param)

            if not resolved.startswith(os.path.realpath(WORKSPACE)):
                self._json(403, {'error': 'path outside workspace'})
                return

            if not os.path.isfile(resolved):
                self._json(404, {'error': f'file not found'})
                return

            try:
                proc = subprocess.Popen(
                    [sys.executable, MDVIEW, resolved],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                proc.wait(timeout=15)
            except Exception as e:
                self._json(500, {'error': str(e)})
                return

            # mdview generated index.html in MDVIEW_HTML_DIR
            index = os.path.join(MDVIEW_HTML_DIR, 'index.html')
            if os.path.isfile(index):
                self._json(200, {'ok': True, 'url': f'http://127.0.0.1:{PORT}/review/index.html'})
            else:
                self._json(500, {'error': 'mdview did not generate index.html'})
            return

        super().do_GET()

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('127.0.0.1', PORT), Handler) as httpd:
    print(f'Serving on http://127.0.0.1:{PORT}', flush=True)
    httpd.serve_forever()
