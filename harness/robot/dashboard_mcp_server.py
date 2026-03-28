#!/usr/bin/env python3
"""
Dashboard MCP Server
- Wraps the original server.py HTTP functionality
- Runs HTTP server in background thread
- Exposes MCP tools via stdio for OpenClaw Gateway
- Preserves all existing functionality (static files, /api/open, /review/*)
"""
import json
import sys
import threading
import http.server
import socketserver
import subprocess
import os
import urllib.parse

# === Constants (from original server.py) ===
DIR = '/Users/lr/.openclaw/workspace/harness/robot'
WORKSPACE = '/Users/lr/.openclaw/workspace'
PORT = 18999
MDVIEW = os.path.join(WORKSPACE, 'tools', 'mdview.py')
MDVIEW_HTML_DIR = os.path.join(WORKSPACE, '.review', 'html')

# === HTTP Server (from original server.py, adapted) ===
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

        # Add explicit route for night-build files
        if parsed.path.startswith('/night-build/'):
            relative_path = urllib.parse.unquote(parsed.path[len('/night-build/'):])
            file_path = os.path.join(DIR, 'night-build', relative_path)
            if os.path.isfile(file_path):
                try:
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/markdown; charset=utf-8')
                    self.end_headers()
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.wfile.write(content.encode('utf-8'))
                    return
                except Exception as e:
                    self._json(500, {'error': str(e)})
                    return
            else:
                self._json(404, {'error': 'file not found'})
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

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/save':
            import re as regex_module
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8')
                data = json.loads(body)
                positions = data.get('positions', {})

                world_path = os.path.join(DIR, 'world.html')
                with open(world_path, 'r', encoding='utf-8') as f:
                    html = f.read()

                saved = []
                for obj_id, pos in positions.items():
                    x, y, z = pos['x'], pos['y'], pos['z']
                    # 1. 替换 group.position.set
                    pat = regex_module.escape(obj_id) + r'\.position\.set\([^)]+\)'
                    repl = obj_id + '.position.set(' + f'{x}, {y}, {z})'
                    new_html, n = regex_module.subn(pat, repl, html)
                    if n > 0:
                        html = new_html
                        saved.append(obj_id)
                    # 2. 替换 _treePositions[idx] → [x, z]
                    if obj_id.startswith('tree') and obj_id[4:].isdigit():
                        idx = int(obj_id[4:])
                        var_name = 'window._treePositions'
                        pos = html.find(var_name)
                        if pos >= 0:
                            arr_start = html.index('[', pos)
                            depth = 0; arr_end = arr_start
                            for j in range(arr_start, len(html)):
                                if html[j] == '[': depth += 1
                                elif html[j] == ']':
                                    depth -= 1
                                    if depth == 0: arr_end = j + 1; break
                            old_arr = html[arr_start:arr_end]
                            try:
                                import ast
                                arr = ast.literal_eval(old_arr)
                                if 0 <= idx < len(arr):
                                    arr[idx] = [round(x, 3), round(z, 3)]
                                    new_arr = str(arr).replace(' ', '')
                                    html = html[:arr_start] + new_arr + html[arr_end:]
                                    saved.append(obj_id + ' (tree array)')
                            except Exception:
                                pass
                    # 3. 替换 _streetLightPositions[idx] → [x, z]
                    if obj_id.startswith('streetLight') and len(obj_id) > 11 and obj_id[11:].isdigit():
                        idx = int(obj_id[11:])
                        var_name = 'window._streetLightPositions'
                        pos = html.find(var_name)
                        if pos >= 0:
                            arr_start = html.index('[', pos)
                            depth = 0; arr_end = arr_start
                            for j in range(arr_start, len(html)):
                                if html[j] == '[': depth += 1
                                elif html[j] == ']':
                                    depth -= 1
                                    if depth == 0: arr_end = j + 1; break
                            old_arr = html[arr_start:arr_end]
                            try:
                                import ast
                                arr = ast.literal_eval(old_arr)
                                if 0 <= idx < len(arr):
                                    arr[idx] = [round(x, 3), round(z, 3)]
                                    new_arr = str(arr).replace(' ', '')
                                    html = html[:arr_start] + new_arr + html[arr_end:]
                                    saved.append(obj_id + ' (streetLight array)')
                            except Exception:
                                pass

                with open(world_path, 'w', encoding='utf-8') as f:
                    f.write(html)

                self._json(200, {'ok': True, 'saved': saved, 'count': len(saved)})
            except Exception as e:
                import traceback
                self._json(500, {'error': str(e), 'trace': traceback.format_exc()})
        else:
            self._json(404, {'error': 'not found'})
        return

# === MCP Tools (stdio) ===
def handle_message(msg):
    if msg.get('method') == 'initialize':
        return {
            'jsonrpc': '2.0',
            'id': msg.get('id'),
            'result': {
                'capabilities': {},
                'serverInfo': {
                    'name': 'Dashboard MCP Server',
                    'version': '1.0.0'
                }
            }
        }
    return {'jsonrpc': '2.0', 'id': msg.get('id'), 'error': {'code': -32601, 'message': 'Method not found'}}

def read_message():
    try:
        line = input().strip()
        if not line:
            return None
        return json.loads(line)
    except EOFError:
        return None
    except Exception as e:
        return {'error': str(e)}

def write_message(msg):
    print(json.dumps(msg, ensure_ascii=False))

def mcp_server_loop():
    while True:
        msg = read_message()
        if msg is None:
            break
        response = handle_message(msg)
        write_message(response)

# === HTTP Server Management ===
_httpd = None
_http_thread = None

def start_http_server():
    global _httpd, _http_thread
    _httpd = socketserver.TCPServer(('127.0.0.1', PORT), Handler, bind_and_activate=False)
    _httpd.allow_reuse_address = True
    _httpd.server_bind()
    _httpd.server_activate()
    _http_thread = threading.Thread(target=_httpd.serve_forever, daemon=True)
    _http_thread.start()
    print(f"Dashboard HTTP server running on http://127.0.0.1:{PORT}")

def stop_http_server():
    global _httpd
    if _httpd:
        _httpd.shutdown()
        _httpd.server_close()

# === Main Entry Point ===
if __name__ == '__main__':
    # Start HTTP server in background
    start_http_server()
    
    # Handle MCP stdio
    try:
        mcp_server_loop()
    except KeyboardInterrupt:
        pass
    finally:
        stop_http_server()