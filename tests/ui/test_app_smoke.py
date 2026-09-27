from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_smoke_no_model(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TRAFFICVISION_ROOT", str(tmp_path))

    app_path = str(Path(__file__).parents[2] / "app.py")
    at = AppTest.from_file(app_path, default_timeout=25)
    at.run()

    assert not at.exception
    # Assert app renders TrafficVision title
    title_texts = [t.value for t in at.title]
    assert any("TrafficVision" in t for t in title_texts)

    # Assert setup action / warning when no model installed
    warning_or_info = [w.value for w in at.warning] + [info.value for info in at.info]
    assert any(
        "chưa được cài đặt" in str(msg).lower() or "bootstrap" in str(msg).lower()
        for msg in warning_or_info
    )

    # Assert it does not claim 82 lớp
    all_text = " ".join(
        [m.value for m in at.markdown] + [c.value for c in at.caption] + title_texts
    )
    assert "82 lớp" not in all_text
