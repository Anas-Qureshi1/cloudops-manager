import os

from app.database import get_db_connection, init_db


def seed_database(database=None):
    database = database or os.environ.get("DATABASE_PATH", "cloudops.db")
    init_db(database)
    connection = get_db_connection(database)

    # Check whether data already exists
    server_count = connection.execute(
        "SELECT COUNT(*) FROM servers"
    ).fetchone()[0]

    if server_count == 0:

        servers = [
            ("web-server-01", "Running", 42, "ap-south-1"),
            ("api-server-01", "Running", 31, "ap-south-1"),
            ("db-server-01", "Stopped", 0, "ap-south-1"),
            ("worker-server-01", "Running", 57, "ap-south-1"),
            ("monitoring-server-01", "Running", 24, "ap-south-1")
        ]

        connection.executemany(
            """
            INSERT INTO servers
            (name, status, cpu, region)
            VALUES (?, ?, ?, ?)
            """,
            servers
        )

    deployment_count = connection.execute(
        "SELECT COUNT(*) FROM deployments"
    ).fetchone()[0]

    if deployment_count == 0:

        deployments = [
            ("v1.0.4", "Production", "SUCCESS"),
            ("v1.0.3", "Production", "SUCCESS"),
            ("v1.0.2", "Production", "FAILED"),
            ("v1.0.1", "Production", "SUCCESS"),
            ("v1.0.0", "Production", "SUCCESS")
        ]

        connection.executemany(
            """
            INSERT INTO deployments
            (version, environment, status)
            VALUES (?, ?, ?)
            """,
            deployments
        )

    security_count = connection.execute(
        "SELECT COUNT(*) FROM security_checks"
    ).fetchone()[0]

    if security_count == 0:

        security_checks = [
            (
                "Gitleaks",
                "Secret detection",
                "PASS"
            ),
            (
                "pytest",
                "Unit testing",
                "PASS"
            ),
            (
                "SonarQube",
                "Static application security testing",
                "PASS"
            ),
            (
                "OWASP Dependency-Check",
                "Dependency vulnerability scanning",
                "PASS"
            ),
            (
                "Trivy",
                "Container vulnerability scanning",
                "PASS"
            )
        ]

        connection.executemany(
            """
            INSERT INTO security_checks
            (tool, description, status)
            VALUES (?, ?, ?)
            """,
            security_checks
        )

    connection.commit()
    connection.close()

    print("Database seeded successfully.")


if __name__ == "__main__":
    seed_database()