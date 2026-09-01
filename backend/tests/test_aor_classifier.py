from pathlib import Path

from qms_incub.aor_routing.classifier import classify_text


class KeywordEmbedding:
    def get_text_embedding(self, text: str) -> list[float]:
        lowered = text.lower()
        return [
            float(sum(lowered.count(word) for word in ("research", "university", "study"))),
            float(sum(lowered.count(word) for word in ("software", "coding", "agile"))),
        ]


def test_classifies_text_against_labeled_references(tmp_path: Path) -> None:
    (tmp_path / "rt.txt").write_text("research university study", encoding="utf-8")
    (tmp_path / "ssd.txt").write_text("software coding agile", encoding="utf-8")

    result = classify_text(
        "The university will conduct a research study.",
        reference_dir=tmp_path,
        embed_model=KeywordEmbedding(),
    )

    assert result.route == "rt"
    assert result.scores["rt"] > result.scores["ssd"]
    assert result.needs_review is False
