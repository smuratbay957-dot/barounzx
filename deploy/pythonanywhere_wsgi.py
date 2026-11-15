# ============================================================
#  PythonAnywhere web app uchun statik sayt serveri
#  (GitHub Pages ishlatilsa, bu fayl shart emas)
#
#  Ishlatish:
#   Web tab -> Add a new web app -> Manual configuration -> Python 3.13
#   So'ng "WSGI configuration file" havolasini ochib, ichidagi hamma
#   narsani shu fayl mazmuni bilan almashtiring va Reload bosing.
# ============================================================
import os

SITE_DIR = "/home/zxmax/barounzx/sayt"

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
}


def application(environ, start_response):
    path = environ.get("PATH_INFO", "/") or "/"
    if path.endswith("/"):
        path += "index.html"

    base = os.path.realpath(SITE_DIR)
    fs_path = os.path.realpath(os.path.join(base, path.lstrip("/")))

    if not (fs_path == base or fs_path.startswith(base + os.sep)) or not os.path.isfile(fs_path):
        start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
        return [b"404 Not found"]

    ext = os.path.splitext(fs_path)[1].lower()
    ctype = CONTENT_TYPES.get(ext, "application/octet-stream")
    with open(fs_path, "rb") as fh:
        data = fh.read()

    start_response("200 OK", [("Content-Type", ctype), ("Content-Length", str(len(data)))])
    return [data]
