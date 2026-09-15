from pathlib import Path

from sentinel.api.app import safe_web_dist_file


def test_safe_web_dist_file_rejects_path_escape(tmp_path: Path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html></html>", encoding="utf-8")
    secret = tmp_path / "secret.txt"
    secret.write_text("nope", encoding="utf-8")

    assert safe_web_dist_file("index.html", dist) == (dist / "index.html").resolve()
    assert safe_web_dist_file("../secret.txt", dist) is None
    assert safe_web_dist_file("..\\secret.txt", dist) is None
    assert safe_web_dist_file("", dist) is None
