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


def test_deployments_show_data_from_configured_database(client):
    response = client.get("/deployments")

    assert response.status_code == 200
    assert b"v-test" in response.data
    assert b"Testing" in response.data
    assert b"SUCCESS" in response.data


def test_security_show_data_from_configured_database(client):
    response = client.get("/security")

    assert response.status_code == 200
    assert b"pytest" in response.data
    assert b"Unit testing" in response.data
    assert b"PASS" in response.data


def test_empty_database_rendering(monkeypatch):
    database_fd, database_path = tempfile.mkstemp()
    os.close(database_fd)

    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(app.config, "DATABASE", database_path)
    init_db(database_path)

    try:
        empty_client = app.test_client()
        for path in ["/", "/servers", "/deployments", "/security"]:
            response = empty_client.get(path)
            assert response.status_code == 200
            assert b"empty-state" in response.data or b"No " in response.data
    finally:
        os.unlink(database_path)


def test_404_error_page(client):
    response = client.get("/nonexistent-page")

    assert response.status_code == 404
    assert b"404 Not Found" in response.data or b"could not be found" in response.data


def test_security_headers_present(client):
    response = client.get("/")

    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"


def test_seed_database(monkeypatch):
    from app.seed import seed_database

    database_fd, database_path = tempfile.mkstemp()
    os.close(database_fd)

    monkeypatch.setenv("DATABASE_PATH", database_path)
    try:
        seed_database()
        connection = get_db_connection(database_path)
        server_count = connection.execute("SELECT COUNT(*) FROM servers").fetchone()[0]
        deployment_count = connection.execute("SELECT COUNT(*) FROM deployments").fetchone()[0]
        security_count = connection.execute("SELECT COUNT(*) FROM security_checks").fetchone()[0]
        connection.close()

        assert server_count > 0
        assert deployment_count > 0
        assert security_count > 0

        # Running again should not insert duplicates
        seed_database()
        connection = get_db_connection(database_path)
        assert connection.execute("SELECT COUNT(*) FROM servers").fetchone()[0] == server_count
        connection.close()
    finally:
        os.unlink(database_path)


def test_vercel_entrypoint(monkeypatch):
    database_fd, database_path = tempfile.mkstemp()
    os.close(database_fd)

    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("DATABASE_PATH", database_path)

    import api.index as vercel_entry
    from werkzeug.test import Client
    from werkzeug.wrappers import Response

    client = Client(vercel_entry.app.wsgi_app, Response)

    try:
        # 1. Direct requests
        response = client.get("/")
        assert response.status_code == 200
        assert "Cloud Infrastructure Overview" in response.text
        assert 'href="/" class="nav-link active"' in response.text
        assert 'href="/api/index"' not in response.text

        # 2. Vercel rewrite with path=servers
        servers_res = client.get("/api/index.py?path=servers")
        assert servers_res.status_code == 200
        assert "Cloud Server Inventory" in servers_res.text
        assert 'href="/servers" class="nav-link active"' in servers_res.text
        assert 'href="/" class="nav-link' in servers_res.text
        assert 'href="/api/index"' not in servers_res.text

        # 3. Vercel rewrite with path=deployments
        dep_res = client.get("/api/index.py?path=deployments")
        assert dep_res.status_code == 200
        assert "Deployment History" in dep_res.text
        assert 'href="/deployments" class="nav-link active"' in dep_res.text
        assert 'href="/api/index"' not in dep_res.text

        # 4. Vercel rewrite with path=security
        sec_res = client.get("/api/index.py?path=security")
        assert sec_res.status_code == 200
        assert "DevSecOps Security Checks" in sec_res.text
        assert 'href="/security" class="nav-link active"' in sec_res.text
        assert 'href="/api/index"' not in sec_res.text

        # 5. Vercel direct rewrite for root dashboard
        dash_res = client.get("/api/index.py?path=")
        assert dash_res.status_code == 200
        assert "Cloud Infrastructure Overview" in dash_res.text
        assert 'href="/" class="nav-link active"' in dash_res.text
        assert 'href="/api/index"' not in dash_res.text

        # 6. Legacy /api/index path normalization
        api_index_res = client.get("/api/index.py?path=api/index")
        assert api_index_res.status_code == 200
        assert "Cloud Infrastructure Overview" in api_index_res.text
        assert 'href="/" class="nav-link active"' in api_index_res.text
        assert 'href="/api/index"' not in api_index_res.text
    finally:
        try:
            os.unlink(database_path)
        except OSError:
            pass




