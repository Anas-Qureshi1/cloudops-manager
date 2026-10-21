import os
import sqlite3
import traceback
import urllib.parse
from flask import Flask, render_template
from app.database import get_db_connection, get_default_db_path

app = Flask(__name__)


class VercelPathMiddleware:
    """
    WSGI middleware to correctly resolve client request paths on Vercel.
    Supports Vercel rewrites (?path=$1), edge proxy headers, and direct function invocations.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app
        self._is_vercel_middleware = True

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


# Wrap wsgi_app with VercelPathMiddleware
if not getattr(app.wsgi_app, "_is_vercel_middleware", False):
    app.wsgi_app = VercelPathMiddleware(app.wsgi_app)


def get_database():
    database = app.config.get("DATABASE") or get_default_db_path()
    connection = get_db_connection(database)
    try:
        connection.execute("SELECT 1 FROM servers LIMIT 1")
    except sqlite3.OperationalError:
        from app.seed import seed_database
        connection.close()
        seed_database(database)
        connection = get_db_connection(database)
    return connection


@app.after_request
def apply_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


@app.errorhandler(404)
def handle_not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def handle_internal_error(error):
    error_tb = traceback.format_exc()
    print("500 Internal Error:\n", error_tb)
    return render_template("500.html", error_details=error_tb), 500


@app.route("/", methods=["GET"])
def dashboard():
    connection = get_database()
    try:
        total_servers = connection.execute(
            "SELECT COUNT(*) FROM servers"
        ).fetchone()[0]

        running_servers = connection.execute(
            "SELECT COUNT(*) FROM servers WHERE status = 'Running'"
        ).fetchone()[0]

        stopped_servers = connection.execute(
            "SELECT COUNT(*) FROM servers WHERE status != 'Running'"
        ).fetchone()[0]

        total_deployments = connection.execute(
            "SELECT COUNT(*) FROM deployments"
        ).fetchone()[0]

        security_checks = connection.execute(
            "SELECT * FROM security_checks"
        ).fetchall()

        recent_deployments = connection.execute(
            """
            SELECT *
            FROM deployments
            ORDER BY id DESC
            LIMIT 5
            """
        ).fetchall()
    finally:
        connection.close()

    return render_template(
        "dashboard.html",
        total_servers=total_servers,
        running_servers=running_servers,
        stopped_servers=stopped_servers,
        total_deployments=total_deployments,
        security_checks=security_checks,
        recent_deployments=recent_deployments
    )


@app.route("/servers", methods=["GET"])
def servers():
    connection = get_database()
    try:
        servers_list = connection.execute(
            "SELECT * FROM servers ORDER BY id DESC"
        ).fetchall()
    finally:
        connection.close()

    return render_template(
        "servers.html",
        servers=servers_list
    )


@app.route("/deployments", methods=["GET"])
def deployments():
    connection = get_database()
    try:
        deployments_list = connection.execute(
            "SELECT * FROM deployments ORDER BY id DESC"
        ).fetchall()
    finally:
        connection.close()

    return render_template(
        "deployments.html",
        deployments=deployments_list
    )


@app.route("/security", methods=["GET"])
def security():
    connection = get_database()
    try:
        security_checks = connection.execute(
            "SELECT * FROM security_checks"
        ).fetchall()
    finally:
        connection.close()

    return render_template(
        "security.html",
        security_checks=security_checks
    )


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") in ("1", "true", "True")
    app.run(host="127.0.0.1", port=5000, debug=debug_mode)