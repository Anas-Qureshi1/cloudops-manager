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

from app.app import app, VercelPathMiddleware
from app.seed import seed_database

app.config["DATABASE"] = DB_PATH

# Seed the database on cold boot if needed
try:
    if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) == 0:
        seed_database(DB_PATH)
except Exception as err:
    print(f"Vercel initial seed notice: {err}")

# Ensure WSGI app is wrapped with VercelPathMiddleware
if not getattr(app.wsgi_app, "_is_vercel_middleware", False):
    app.wsgi_app = VercelPathMiddleware(app.wsgi_app)

