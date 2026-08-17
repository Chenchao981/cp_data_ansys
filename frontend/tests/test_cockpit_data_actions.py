from __future__ import annotations

from streamlit.testing.v1 import AppTest


def _empty_cockpit(tmp_path, monkeypatch) -> AppTest:
    monkeypatch.setenv("CP_COCKPIT_DATA_DIR", str(tmp_path))
    return AppTest.from_file("frontend/cp_dashboard_app.py").run(timeout=15)


def test_data_management_exposes_save_load_and_reset(tmp_path, monkeypatch) -> None:
    app = _empty_cockpit(tmp_path, monkeypatch)
    buttons = {button.label: button for button in app.button}

    assert {"💾 保存数据", "📂 加载数据", "🔄 重置"}.issubset(buttons)
    assert buttons["💾 保存数据"].disabled is True

    buttons["📂 加载数据"].click()
    app.run(timeout=15)
    assert app.radio[0].value == "手动加载已保存文件"
    assert any("加载数据" in message.value for message in app.info)


def test_reset_clears_current_view_and_waits_for_new_data(tmp_path, monkeypatch) -> None:
    app = _empty_cockpit(tmp_path, monkeypatch)
    next(button for button in app.button if button.label == "🔄 重置").click()
    app.run(timeout=15)

    assert app.radio[0].value == "手动加载已保存文件"
    assert any("已重置" in message.value for message in app.success)
    assert not app.exception
