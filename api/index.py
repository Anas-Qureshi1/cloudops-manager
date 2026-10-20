import os
import sys

# Ensure root directory is in sys.path for serverless runtime
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.app import app
from app.seed import seed_database

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
