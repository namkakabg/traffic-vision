from pathlib import Path


def test_dashboard_failure_keeps_the_windows_launcher_open() -> None:
    """A failed Streamlit start must remain visible after double-clicking the BAT."""
    launcher = (Path(__file__).parents[1] / "run_app.bat").read_text(encoding="utf-8")
    dashboard_section = launcher.split(":RUN_APP", 1)[1].split(":RUN_TEST", 1)[0]

    assert '"%PYTHON_EXE%" -m streamlit run app.py' in dashboard_section
    assert "if errorlevel 1 (" in dashboard_section
    assert "pause" in dashboard_section
