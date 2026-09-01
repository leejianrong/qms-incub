from fastapi.testclient import TestClient

from qms_incub.main import app

client = TestClient(app)


def test_upload_rejects_non_pdf() -> None:
    response = client.post(
        "/documents", files={"file": ("notes.txt", b"hello", "text/plain")}
    )
    assert response.status_code == 400
