from __future__ import annotations

from streamlit.testing.v1 import AppTest


def _empty_cockpit(tmp_path, monkeypatch) -> AppTest:
    monkeypatch.setenv("CP_COCKPIT_DATA_DIR", str(tmp_path))
    return AppTest.from_file("frontend/cp_dashboard_app.py").run(timeout=15)


def test_data_management_exposes_save_load_and_reset(tmp_path, monkeypatch) -> None:
    app = _empty_cockpit(tmp_path, monkeypatch)
    buttons = {button.label: button for button in app.button}
    uploaders = app.get("file_uploader")

    assert {"💾 保存数据", "🔄 重置"}.issubset(buttons)
    assert "📂 加载数据" not in buttons
    assert "📁 重新加载当前目录" not in buttons
    assert buttons["💾 保存数据"].disabled is True
    assert len(uploaders) == 1
    assert uploaders[0].label == "📂 加载数据"
    assert len(app.radio) == 0
    assert all("确认加载" not in button.label for button in app.button)
    assert not app.exception


def test_reset_clears_file_browser_without_changing_current_page(tmp_path, monkeypatch) -> None:
    app = _empty_cockpit(tmp_path, monkeypatch)
    next(button for button in app.button if button.label == "🔄 重置").click()
    app.run(timeout=15)

    assert len(app.text_input) == 1
    assert len(app.get("file_uploader")) == 1
    assert any("已清空本次文件选择" in message.value for message in app.success)
    assert not app.exception
