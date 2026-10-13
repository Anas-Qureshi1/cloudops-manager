import os
import tempfile

import pytest

from app.app import app
from app.database import get_db_connection, init_db


@pytest.fixture
def client(monkeypatch):
    database_fd, database_path = tempfile.mkstemp()
    os.close(database_fd)

    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(app.config, "DATABASE", database_path)
    init_db(database_path)

    connection = get_db_connection(database_path)
    connection.execute(
        """
        INSERT INTO servers (name, status, cpu, region)
        VALUES (?, ?, ?, ?)
        """,
        ("test-server", "Running", 25, "ap-south-1"),
    )
    connection.execute(
        """
        INSERT INTO deployments (version, environment, status)
        VALUES (?, ?, ?)
        """,
        ("v-test", "Testing", "SUCCESS"),
    )
    connection.execute(
        """
        INSERT INTO security_checks (tool, description, status)
        VALUES (?, ?, ?)
        """,
        ("pytest", "Unit testing", "PASS"),
    )
    connection.commit()
    connection.close()

    try:
        yield app.test_client()
    finally:
        os.unlink(database_path)


@pytest.mark.parametrize(
    "path",
    ["/", "/servers", "/deployments", "/security"],
)
def test_pages_use_configured_database(client, path):
    response = client.get(path)

    assert response.status_code == 200


def test_pages_show_data_from_configured_database(client):
    servers_response = client.get("/servers")
    dashboard_response = client.get("/")

    assert b"test-server" in servers_response.data
    assert b"v-test" in dashboard_response.data
    assert b"Total Servers</p>\n\n        <h2>1</h2>" in dashboard_response.data


def test_server_data(client):
    response = client.get("/servers")

    assert response.status_code == 200
    assert b"test-server" in response.data
    assert b"Running" in response.data
    assert b"ap-south-1" in response.data
