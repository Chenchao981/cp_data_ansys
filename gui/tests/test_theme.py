import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

from gui.theme import (
    DARK_THEME,
    DEFAULT_THEME,
    LIGHT_THEME,
    THEME_COLORS,
    build_stylesheet,
    normalize_theme,
    opposite_theme,
    theme_button_text,
)


def _relative_luminance(hex_color):
    channels = [int(hex_color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(first, second):
    first_luminance = _relative_luminance(first)
    second_luminance = _relative_luminance(second)
    lighter = max(first_luminance, second_luminance)
    darker = min(first_luminance, second_luminance)
    return (lighter + 0.05) / (darker + 0.05)


def test_theme_helpers_default_to_dark_and_toggle():
    assert normalize_theme("unknown") == DEFAULT_THEME == DARK_THEME
    assert normalize_theme(" LIGHT ") == LIGHT_THEME
    assert opposite_theme(DARK_THEME) == LIGHT_THEME
    assert opposite_theme(LIGHT_THEME) == DARK_THEME
    assert "亮色主题" in theme_button_text(DARK_THEME)
    assert "暗黑主题" in theme_button_text(LIGHT_THEME)


def test_both_stylesheets_cover_navigation_forms_menus_and_logs():
    for theme_name in (DARK_THEME, LIGHT_THEME):
        stylesheet = build_stylesheet(theme_name)
        assert THEME_COLORS[theme_name]["window"] in stylesheet
        assert "QPushButton#navButton:checked" in stylesheet
        assert "QPushButton#themeToggleButton" in stylesheet
        assert "QLineEdit" in stylesheet
        assert "QTextEdit[role=\"log\"]" in stylesheet
        assert "QMenu" in stylesheet
        assert "QMessageBox" in stylesheet


def test_primary_text_and_action_buttons_keep_readable_contrast():
    for colors in THEME_COLORS.values():
        assert _contrast_ratio(colors["text"], colors["window"]) >= 7
        assert _contrast_ratio("#FFFFFF", colors["primary"]) >= 4.5
        assert _contrast_ratio("#FFFFFF", colors["success"]) >= 4.5


def test_main_window_switches_theme_without_losing_form_state():
    from gui.multi_company_gui import MultiCompanyCPDataGUI

    app = QApplication.instance() or QApplication([])
    window = MultiCompanyCPDataGUI(
        initial_theme=DARK_THEME,
        remember_theme=False,
    )
    original_input = window.company_widgets["huahong"].input_path_edit.text()

    assert window.current_theme == DARK_THEME
    assert set(window.company_widgets) == {"huahong", "jetech", "lion", "guoyu"}
    for widget in window.company_widgets.values():
        assert widget.objectName() == "companyPage"
        assert widget.clean_btn.property("role") == "primary"
        assert widget.cockpit_btn.property("role") == "success"
        assert widget.status_text.property("role") == "log"
        assert widget.status_text.isReadOnly()

    window.toggle_theme()

    assert window.current_theme == LIGHT_THEME
    assert THEME_COLORS[LIGHT_THEME]["window"] in app.styleSheet()
    assert window.company_widgets["huahong"].input_path_edit.text() == original_input

    window.hide()
    window.deleteLater()
    app.processEvents()
