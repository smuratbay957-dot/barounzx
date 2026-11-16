# ============================================================
#  PythonAnywhere "WSGI configuration file"
#  Web tab -> WSGI configuration file -> ichidagi hamma narsani
#  shu bilan almashtiring -> Save -> Reload.
#
#  Sayt GitHub Pages'da, bu web app esa bot uchun API bo'lib xizmat qiladi.
# ============================================================
import sys

sys.path.insert(0, "/home/zxmax/barounzx/deploy")

from pa_api_wsgi import application  # noqa: E402,F401
