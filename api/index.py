import os
import sys

# Ensure root directory is in sys.path for serverless runtime
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.app import app
from app.seed import seed_database


class VercelPathMiddleware:
    """
    WSGI middleware to correctly restore the client's requested path.
    Vercel serverless rewrites route to /api/index.py by default, which
    can overwrite PATH_INFO and cause Flask to return 404 for root and sub-routes.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # Read proxy headers injected by Vercel edge proxy
        forwarded_uri = (
            environ.get("HTTP_X_FORWARDED_URI")
            or environ.get("HTTP_X_MATCHED_PATH")
            or environ.get("HTTP_X_ORIGINAL_URI")
            or environ.get("HTTP_X_NOW_ROUTE_MATCHES")
        )

        if forwarded_uri:
            parts = forwarded_uri.split("?", 1)
            environ["PATH_INFO"] = parts[0]
            if len(parts) > 1 and not environ.get("QUERY_STRING"):
                environ["QUERY_STRING"] = parts[1]
        else:
            path_info = environ.get("PATH_INFO", "")
            if path_info in ("/api/index.py", "/api/index", "/api", ""):
                environ["PATH_INFO"] = "/"
            elif path_info.startswith("/api/index.py/"):
                environ["PATH_INFO"] = path_info[len("/api/index.py"):]
            elif path_info.startswith("/api/index/"):
                environ["PATH_INFO"] = path_info[len("/api/index"):]

        return self.wsgi_app(environ, start_response)


# Apply middleware to Flask WSGI app
app.wsgi_app = VercelPathMiddleware(app.wsgi_app)

# Configure database location for Vercel Serverless environment
# In serverless environments, only /tmp is writable
if os.environ.get("VERCEL"):
    db_path = "/tmp/cloudops.db"
    os.environ["DATABASE_PATH"] = db_path
    app.config["DATABASE"] = db_path
else:
    db_path = app.config.get("DATABASE") or os.environ.get(
        "DATABASE_PATH", os.path.join(ROOT_DIR, "cloudops.db")
    )

# Auto-seed the database on cold start if not yet initialized
if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
    seed_database(db_path)
