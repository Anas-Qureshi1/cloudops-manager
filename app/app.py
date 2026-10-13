from flask import Flask, render_template
from app.database import get_db_connection

app = Flask(__name__)


def get_database():
    database = app.config.get("DATABASE")
    if database:
        return get_db_connection(database)
    return get_db_connection()


@app.route("/")
def dashboard():

    connection = get_database()

    total_servers = connection.execute(
        "SELECT COUNT(*) FROM servers"
    ).fetchone()[0]

    running_servers = connection.execute(
        "SELECT COUNT(*) FROM servers WHERE status = 'Running'"
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

    connection.close()

    return render_template(
        "dashboard.html",
        total_servers=total_servers,
        running_servers=running_servers,
        total_deployments=total_deployments,
        security_checks=security_checks,
        recent_deployments=recent_deployments
    )


@app.route("/servers")
def servers():

    connection = get_database()

    servers = connection.execute(
        "SELECT * FROM servers ORDER BY id DESC"
    ).fetchall()

    connection.close()

    return render_template(
        "servers.html",
        servers=servers
    )


@app.route("/deployments")
def deployments():

    connection = get_database()

    deployments = connection.execute(
        "SELECT * FROM deployments ORDER BY id DESC"
    ).fetchall()

    connection.close()

    return render_template(
        "deployments.html",
        deployments=deployments
    )


@app.route("/security")
def security():

    connection = get_database()

    security_checks = connection.execute(
        "SELECT * FROM security_checks"
    ).fetchall()

    connection.close()

    return render_template(
        "security.html",
        security_checks=security_checks
    )


if __name__ == "__main__":
    app.run(debug=True)