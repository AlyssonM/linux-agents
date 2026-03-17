from click.testing import CliRunner

from rpi_gui.cli import cli


def test_gui_workflow_commands(monkeypatch):
    monkeypatch.setattr("rpi_gui.commands.see.capture_screenshot", lambda: type("Img", (), {"width": 800, "height": 600})())
    monkeypatch.setattr("rpi_gui.commands.see.save_screenshot", lambda image, output_path=None: "artifacts/s.png")
    monkeypatch.setattr("rpi_gui.commands.see.run_ocr", lambda image, min_confidence=0.0: type("R", (), {"text": "hello", "words": []})())
    monkeypatch.setattr("rpi_gui.commands.ocr.capture_screenshot", lambda: type("Img", (), {"width": 800, "height": 600})())
    monkeypatch.setattr("rpi_gui.commands.ocr.run_ocr", lambda image, min_confidence=0.0: type("R", (), {"text": "hello", "words": []})())
    monkeypatch.setattr("rpi_gui.modules.input.type_text", lambda text, interval=0.0, press_enter=False: None)
    monkeypatch.setattr("rpi_gui.modules.input.click_at", lambda x, y, button="left", clicks=1, interval=0.0: None)

    runner = CliRunner()
    assert runner.invoke(cli, ["see"]).exit_code == 0
    assert runner.invoke(cli, ["ocr"]).exit_code == 0
    assert runner.invoke(cli, ["type", "hello"]).exit_code == 0
    assert runner.invoke(cli, ["click", "--x", "10", "--y", "20"]).exit_code == 0
