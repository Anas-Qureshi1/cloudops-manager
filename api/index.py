import os
import sys
import urllib.parse

# Ensure root directory is in sys.path for serverless runtime
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Force SQLite database to /tmp on serverless environments (only /tmp is writable)
DB_PATH = "/tmp/cloudops.db"
os.environ["DATABASE_PATH"] = DB_PATH

from app.app import app
from app.seed import seed_database

app.config["DATABASE"] = DB_PATH

# Seed the database on cold boot if needed
try:
    if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) == 0:
        seed_database(DB_PATH)
except Exception as err:
    print(f"Vercel initial seed notice: {err}")


class VercelPathMiddleware:
    """
    WSGI middleware to correctly resolve client request paths on Vercel.
    Supports Vercel rewrites (?path=$1), edge proxy headers, and direct function invocations.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get("QUERY_STRING", "")
        resolved_path = None

        # 1. Check query string for path injected by vercel.json rewrite (?path=$1)
        if query_string:
            parsed_params = urllib.parse.parse_qs(query_string, keep_blank_values=True)
            if "path" in parsed_params:
                raw_path = parsed_params.pop("path")[0].strip()
                # Clean 'path' parameter out of QUERY_STRING so request.args is clean
                clean_pairs = []
                for key, values in parsed_params.items():
                    for val in values:
                        clean_pairs.append((key, val))
                environ["QUERY_STRING"] = urllib.parse.urlencode(clean_pairs)

                clean_path = raw_path.strip("/")
                if clean_path and clean_path not in ("api/index.py", "api/index", "api"):
                    resolved_path = "/" + clean_path
                else:
                    resolved_path = "/"

        # 2. Check edge proxy headers if not resolved via query string
        if not resolved_path:
            forwarded_uri = (
                environ.get("HTTP_X_FORWARDED_URI")
                or environ.get("HTTP_X_ORIGINAL_URI")
            )
            if forwarded_uri and not forwarded_uri.startswith(("/api/index.py", "/api/index")):
                parts = forwarded_uri.split("?", 1)
                clean_path = parts[0].strip("/")
                if clean_path and clean_path not in ("api/index.py", "api/index", "api"):
                    resolved_path = "/" + clean_path
                else:
                    resolved_path = "/"
                if len(parts) > 1 and not environ.get("QUERY_STRING"):
                    environ["QUERY_STRING"] = parts[1]

        # 3. Apply resolved path or normalize existing PATH_INFO
        if resolved_path:
            environ["PATH_INFO"] = resolved_path
        else:
            path_info = environ.get("PATH_INFO", "")
            if path_info in ("/api/index.py", "/api/index", "/api", ""):
                environ["PATH_INFO"] = "/"
            elif path_info.startswith("/api/index.py/"):
                environ["PATH_INFO"] = "/" + path_info[len("/api/index.py/"):].lstrip("/")
            elif path_info.startswith("/api/index/"):
                environ["PATH_INFO"] = "/" + path_info[len("/api/index/"):].lstrip("/")

        # 4. Clear SCRIPT_NAME to prevent url_for() from prepending /api/index
        environ["SCRIPT_NAME"] = ""

        return self.wsgi_app(environ, start_response)


# Wrap Flask WSGI app with path resolver middleware
app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
