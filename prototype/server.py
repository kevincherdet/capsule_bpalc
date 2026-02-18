"""
Serveur local pour la capsule.
Usage : python server.py [port]
Ouvre automatiquement le navigateur.
"""
import http.server
import os
import sys
import webbrowser
import json
import cgi
import re
from urllib.parse import urlparse, parse_qs

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class CapsuleHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == '/save':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length).decode('utf-8')

            params = parse_qs(parsed.query)
            capsule_path = params.get('path', ['bpalc/capsule.md'])[0]

            # Security: only allow .md files within the directory
            full_path = os.path.normpath(os.path.join(DIRECTORY, capsule_path))
            if not full_path.startswith(DIRECTORY) or not full_path.endswith('.md'):
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b'Interdit')
                return

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(body)

            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f'OK - {capsule_path} sauvegarde'.encode('utf-8'))
            print(f'[SAVE] {capsule_path} ({len(body)} caracteres)')

        elif parsed.path == '/upload-image':
            # Parse multipart form data
            content_type = self.headers['Content-Type']
            if 'multipart/form-data' not in content_type:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Content-Type multipart requis')
                return

            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST',
                         'CONTENT_TYPE': content_type}
            )

            # Get the image file
            file_item = form['image']
            folder = form.getvalue('folder', 'bpalc/images')

            if not file_item.filename:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Pas de fichier')
                return

            # Sanitize filename: keep only safe characters
            safe_name = re.sub(r'[^\w\-.]', '_', file_item.filename)

            # Security: folder must be within DIRECTORY
            full_folder = os.path.normpath(os.path.join(DIRECTORY, folder))
            if not full_folder.startswith(DIRECTORY):
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b'Interdit')
                return

            os.makedirs(full_folder, exist_ok=True)
            full_path = os.path.join(full_folder, safe_name)

            with open(full_path, 'wb') as f:
                f.write(file_item.file.read())

            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(safe_name.encode('utf-8'))
            print(f'[IMAGE] {safe_name} -> {folder}/ ({os.path.getsize(full_path)} bytes)')

        else:
            self.send_response(404)
            self.end_headers()

    def end_headers(self):
        # CORS headers for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        # Disable cache for .md files (so edits appear immediately)
        if hasattr(self, 'path') and self.path.endswith('.md'):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # Cleaner logging
        msg = format % args
        if '304' not in msg and 'favicon' not in msg:
            print(f'  {msg}')

if __name__ == '__main__':
    os.chdir(DIRECTORY)
    print(f'\n  Capsule server running on http://localhost:{PORT}')
    print(f'  Admin mode: http://localhost:{PORT}?admin=true')
    print(f'  Directory: {DIRECTORY}')
    print(f'  Ctrl+C pour arreter\n')

    webbrowser.open(f'http://localhost:{PORT}')

    server = http.server.HTTPServer(('', PORT), CapsuleHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n  Serveur arrete.')
        server.server_close()
