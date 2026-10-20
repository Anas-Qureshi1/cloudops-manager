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
    Supports edge proxy headers, query parameter rewrites (?path=$1),
    and direct function invocations.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # 1. Edge proxy headers
        forwarded_uri = (
            environ.get("HTTP_X_FORWARDED_URI")
            or environ.get("HTTP_X_MATCHED_PATH")
            or environ.get("HTTP_X_ORIGINAL_URI")
        )

        if forwarded_uri:
            parts = forwarded_uri.split("?", 1)
            environ["PATH_INFO"] = parts[0]
            if len(parts) > 1 and not environ.get("QUERY_STRING"):
                environ["QUERY_STRING"] = parts[1]
        else:
            # 2. Check query string for path injected by vercel.json rewrite
            qs = environ.get("QUERY_STRING", "")
            params = urllib.parse.parse_qs(qs)
            if "path" in params and params["path"][0]:
                raw_target = params["path"][0]
                environ["PATH_INFO"] = "/" + raw_target.lstrip("/")
            else:
                path_info = environ.get("PATH_INFO", "")
                if path_info in ("/api/index.py", "/api/index", "/api", ""):
                    environ["PATH_INFO"] = "/"
                elif path_info.startswith("/api/index.py/"):
                    environ["PATH_INFO"] = path_info[len("/api/index.py"):]
                elif path_info.startswith("/api/index/"):
                    environ["PATH_INFO"] = path_info[len("/api/index"):]

        return self.wsgi_app(environ, start_response)


# Wrap Flask WSGI app with path resolver middleware
app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
