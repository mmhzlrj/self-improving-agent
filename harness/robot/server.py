#!/usr/bin/env python3
"""0-1 Project Dashboard Server - Simplified"""
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
        
        # Handle review directory specially
        if url_path.startswith('/review/') or url_path == '/review':
            relative = url_path[len('/review/'):]
            return os.path.join(MDVIEW_HTML_DIR, relative)
        
        # Handle night-build directory
        if url_path.startswith('/night-build/'):
            relative_path = url_path[len('/night-build/'):]
            nb_dir = os.path.join(DIR, 'night-build')
            
            # Attempt 1: raw URL path
            file_path = os.path.join(nb_dir, relative_path)
            if os.path.isfile(file_path):
                return file_path
            
            # Attempt 2: URL-decoded path
            decoded = urllib.parse.unquote(relative_path)
            file_path = os.path.join(nb_dir, decoded)
            if os.path.isfile(file_path):
                return file_path
            
            # Attempt 3: fuzzy match - list directory and find closest file
            dir_part = os.path.dirname(decoded)
            file_part = os.path.basename(decoded)
            target_dir = os.path.join(nb_dir, dir_part) if dir_part else nb_dir
            if os.path.isdir(target_dir):
                # Normalize both strings for comparison (strip spaces, lowercase ASCII)
                norm_target = file_part.replace(' ', '').lower()
                for entry in os.listdir(target_dir):
                    if entry.replace(' ', '').lower() == norm_target:
                        return os.path.join(target_dir, entry)
            
            # Attempt 4: fall through to parent class (returns valid path or 404)
            return super().translate_path(path)
        
        return super().translate_path(path)

    def do_HEAD(self):
        # HEAD should behave like GET for our custom routes
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/index.html':
            self.send_response(302)
            self.send_header('Location', '/dashboard.html')
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            return
        super().do_HEAD()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        # Handle /index.html - redirect to dashboard
        if parsed.path == '/index.html':
            self.send_response(302)
            self.send_header('Location', '/dashboard.html')
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            return

        # Handle /api/open
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
                    [sys.executable, MDVIEW, '--no-browser', resolved],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                proc.wait(timeout=15)
            except Exception as e:
                self._json(500, {'error': str(e)})
                return

            index = os.path.join(MDVIEW_HTML_DIR, 'index.html')
            if os.path.isfile(index):
                self._json(200, {'ok': True, 'url': f'http://127.0.0.1:{PORT}/review/index.html'})
            else:
                self._json(500, {'error': 'mdview did not generate index.html'})
            return

        # Let the superclass handle static files with our custom translate_path
        super().do_GET()

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/save':
            import traceback
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8')
                data = json.loads(body)
                positions = data.get('positions', {})

                world_path = os.path.join(DIR, 'world.html')
                with open(world_path, 'r', encoding='utf-8') as f:
                    html = f.read()

                import re
                saved = []
                for obj_id, pos in positions.items():
                    x, y, z = pos['x'], pos['y'], pos['z']
                    pattern = r'(' + re.escape(obj_id) + r'\.position\.set\()[^)]+\)'
                    replacement = r'\1(' + f'{x}, {y}, {z})'
                    new_html, n = re.subn(pattern, replacement, html)
                    if n > 0:
                        html = new_html
                        saved.append(obj_id)

                with open(world_path, 'w', encoding='utf-8') as f:
                    f.write(html)

                self._json(200, {'ok': True, 'saved': saved, 'count': len(saved)})
            except Exception as e:
                self._json(500, {'error': str(e), 'trace': traceback.format_exc()})
        else:
            self._json(404, {'error': 'not found'})
        return

    def log_message(self, format, *args):
        pass

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('127.0.0.1', PORT), Handler) as httpd:
    print(f'Serving on http://127.0.0.1:{PORT}', flush=True)
    httpd.serve_forever()