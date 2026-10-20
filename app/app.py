import os
import sqlite3
import traceback
from flask import Flask, render_template
from app.database import get_db_connection, get_default_db_path

app = Flask(__name__)


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
@app.route("/api/index.py", methods=["GET"])
@app.route("/api/index", methods=["GET"])
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