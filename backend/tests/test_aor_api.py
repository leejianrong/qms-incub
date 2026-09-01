from unittest.mock import patch

from fastapi.testclient import TestClient

from qms_incub.aor_routing.classifier import RouteClassification
from qms_incub.main import app

client = TestClient(app)


def test_aor_classification_rejects_non_pdf() -> None:
    response = client.post("/aor/classify", files={"file": ("aor.txt", b"text", "text/plain")})
    assert response.status_code == 400


@patch("qms_incub.main.classify_aor_pdf")
def test_aor_classification_returns_route(mock_classify: object) -> None:
    mock_classify.return_value = RouteClassification(  # type: ignore[attr-defined]
        route="ssd",
        scores={"rt": 0.2, "ssd": 0.8},
        confidence=0.8,
        needs_review=False,
        evidence_excerpt="Build an in-house software system.",
    )
    response = client.post(
        "/aor/classify", files={"file": ("aor.pdf", b"%PDF-demo", "application/pdf")}
    )
    assert response.status_code == 200
    assert response.json()["route"] == "ssd"
    assert response.json()["label"] == "SSD"
