"""Centralized light and dark themes for the multi-company PyQt5 GUI."""

from __future__ import annotations

from typing import Mapping

from PyQt5.QtWidgets import QApplication, QWidget


DARK_THEME = "dark"
LIGHT_THEME = "light"
DEFAULT_THEME = DARK_THEME
THEME_SETTINGS_ORGANIZATION = "CP Data Analysis Team"
THEME_SETTINGS_APPLICATION = "CP Data Analysis Tool"
THEME_SETTINGS_KEY = "ui/theme"


THEME_COLORS: dict[str, dict[str, str]] = {
    DARK_THEME: {
        "window": "#101827",
        "surface": "#172033",
        "surface_alt": "#1D293D",
        "sidebar": "#0B1220",
        "sidebar_header": "#111C2F",
        "input": "#0D1628",
        "log": "#0A1221",
        "text": "#F3F6FA",
        "muted": "#A7B1C2",
        "border": "#34435A",
        "border_strong": "#4A5D78",
        "primary": "#2563EB",
        "primary_hover": "#1D4ED8",
        "primary_pressed": "#1E40AF",
        "primary_soft": "#1E3A5F",
        "success": "#15803D",
        "success_hover": "#166534",
        "success_pressed": "#14532D",
        "error": "#F87171",
        "warning": "#FBBF24",
        "disabled": "#354155",
        "disabled_text": "#8390A3",
        "selection": "#1D4ED8",
        "scroll_handle": "#4A5D78",
        "scroll_hover": "#607590",
    },
    LIGHT_THEME: {
        "window": "#F4F7FB",
        "surface": "#FFFFFF",
        "surface_alt": "#F8FAFC",
        "sidebar": "#EEF3F8",
        "sidebar_header": "#E2E8F0",
        "input": "#FFFFFF",
        "log": "#F8FAFC",
        "text": "#1E293B",
        "muted": "#64748B",
        "border": "#CBD5E1",
        "border_strong": "#94A3B8",
        "primary": "#2563EB",
        "primary_hover": "#1D4ED8",
        "primary_pressed": "#1E40AF",
        "primary_soft": "#DBEAFE",
        "success": "#15803D",
        "success_hover": "#166534",
        "success_pressed": "#14532D",
        "error": "#DC2626",
        "warning": "#D97706",
        "disabled": "#E2E8F0",
        "disabled_text": "#94A3B8",
        "selection": "#2563EB",
        "scroll_handle": "#AAB8C8",
        "scroll_hover": "#8798AB",
    },
}


def normalize_theme(theme_name: object) -> str:
    """Return a supported theme name, defaulting to dark."""

    normalized = str(theme_name or "").strip().casefold()
    return normalized if normalized in THEME_COLORS else DEFAULT_THEME


def opposite_theme(theme_name: object) -> str:
    """Return the alternate theme."""

    return LIGHT_THEME if normalize_theme(theme_name) == DARK_THEME else DARK_THEME


def get_theme_colors(theme_name: object) -> Mapping[str, str]:
    """Return the immutable-by-convention color mapping for one theme."""

    return THEME_COLORS[normalize_theme(theme_name)]


def theme_button_text(theme_name: object) -> str:
    """Describe the theme that will be activated by the toggle button."""

    return "☀️ 亮色主题" if normalize_theme(theme_name) == DARK_THEME else "🌙 暗黑主题"


def theme_button_tooltip(theme_name: object) -> str:
    """Return a clear theme-toggle tooltip."""

    return (
        "切换到亮色主题"
        if normalize_theme(theme_name) == DARK_THEME
        else "切换到暗黑主题"
    )


def set_widget_property(widget: QWidget, name: str, value: object) -> None:
    """Update a dynamic property and immediately refresh QSS selectors."""

    widget.setProperty(name, value)
    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)
    widget.update()


def build_stylesheet(theme_name: object) -> str:
    """Build the application-wide QSS for all menus, forms, and dialogs."""

    c = get_theme_colors(theme_name)
    return f"""
        QMainWindow,
        QWidget#appRoot,
        QWidget#companyPage,
        QStackedWidget#contentStack,
        QDialog {{
            background-color: {c['window']};
            color: {c['text']};
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        }}

        QWidget#navigationPanel {{
            background-color: {c['sidebar']};
            border-right: 1px solid {c['border']};
        }}

        QLabel {{
            color: {c['text']};
            background-color: transparent;
        }}

        QLabel#navigationHeader {{
            color: {c['text']};
            background-color: {c['sidebar_header']};
            border-bottom: 1px solid {c['border_strong']};
            padding: 24px 12px;
            font-size: 27px;
            font-weight: 600;
        }}

        QLabel#versionLabel {{
            color: {c['muted']};
            border-top: 1px solid {c['border']};
            padding: 13px;
            font-size: 11px;
        }}

        QLabel[role="pageTitle"] {{
            color: {c['primary']};
            padding-bottom: 10px;
        }}

        QLabel[role="placeholder"] {{
            color: {c['muted']};
            padding: 50px;
            font-size: 24px;
        }}

        QLabel[role="helpText"],
        QLabel[tone="muted"] {{
            color: {c['muted']};
            font-size: 14px;
        }}

        QLabel[tone="success"] {{
            color: {c['success']};
        }}

        QLabel[tone="error"] {{
            color: {c['error']};
        }}

        QLineEdit,
        QTextEdit,
        QPlainTextEdit,
        QComboBox,
        QSpinBox,
        QDoubleSpinBox,
        QDateEdit,
        QTimeEdit,
        QDateTimeEdit {{
            color: {c['text']};
            background-color: {c['input']};
            selection-color: #FFFFFF;
            selection-background-color: {c['selection']};
            border: 1px solid {c['border']};
            border-radius: 7px;
            padding: 6px 9px;
        }}

        QLineEdit:focus,
        QTextEdit:focus,
        QPlainTextEdit:focus,
        QComboBox:focus {{
            border: 1px solid {c['primary']};
        }}

        QLineEdit:disabled,
        QTextEdit:disabled,
        QPlainTextEdit:disabled,
        QComboBox:disabled {{
            color: {c['disabled_text']};
            background-color: {c['disabled']};
        }}

        QLineEdit::placeholder,
        QTextEdit::placeholder,
        QPlainTextEdit::placeholder {{
            color: {c['muted']};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}

        QComboBox QAbstractItemView {{
            color: {c['text']};
            background-color: {c['surface']};
            selection-color: #FFFFFF;
            selection-background-color: {c['selection']};
            border: 1px solid {c['border']};
            outline: none;
        }}

        QPushButton {{
            color: {c['text']};
            background-color: {c['surface_alt']};
            border: 1px solid {c['border']};
            border-radius: 7px;
            padding: 7px 13px;
            font-weight: 500;
        }}

        QPushButton:hover {{
            background-color: {c['primary_soft']};
            border-color: {c['primary']};
        }}

        QPushButton:pressed {{
            background-color: {c['primary_pressed']};
            color: #FFFFFF;
        }}

        QPushButton:disabled {{
            color: {c['disabled_text']};
            background-color: {c['disabled']};
            border-color: {c['border']};
        }}

        QPushButton#navButton {{
            text-align: left;
            margin: 7px 10px;
            padding: 10px 12px 10px 18px;
            border-radius: 11px;
            font-size: 20px;
            font-weight: 500;
        }}

        QPushButton#navButton:checked {{
            color: #FFFFFF;
            background-color: {c['primary']};
            border: 1px solid {c['primary']};
            border-left: 5px solid {c['primary_pressed']};
            font-weight: 600;
        }}

        QPushButton#navButton:checked:hover {{
            background-color: {c['primary_hover']};
        }}

        QPushButton[role="primary"] {{
            color: #FFFFFF;
            background-color: {c['primary']};
            border: 1px solid {c['primary']};
            border-radius: 8px;
            font-size: 18px;
            font-weight: 600;
        }}

        QPushButton[role="primary"]:hover {{
            background-color: {c['primary_hover']};
            border-color: {c['primary_hover']};
        }}

        QPushButton[role="primary"]:pressed {{
            background-color: {c['primary_pressed']};
            border-color: {c['primary_pressed']};
        }}

        QPushButton[role="success"] {{
            color: #FFFFFF;
            background-color: {c['success']};
            border: 1px solid {c['success']};
            border-radius: 8px;
            font-size: 18px;
            font-weight: 600;
        }}

        QPushButton[role="success"]:hover {{
            background-color: {c['success_hover']};
            border-color: {c['success_hover']};
        }}

        QPushButton[role="success"]:pressed {{
            background-color: {c['success_pressed']};
            border-color: {c['success_pressed']};
        }}

        QPushButton[role="primary"]:disabled,
        QPushButton[role="success"]:disabled {{
            color: {c['disabled_text']};
            background-color: {c['disabled']};
            border-color: {c['border']};
        }}

        QPushButton#themeToggleButton {{
            color: {c['text']};
            background-color: {c['surface']};
            border: 1px solid {c['border_strong']};
            margin: 8px 18px 10px 18px;
            padding: 8px 10px;
            font-size: 14px;
            font-weight: 600;
        }}

        QPushButton#themeToggleButton:hover {{
            color: #FFFFFF;
            background-color: {c['primary']};
            border-color: {c['primary']};
        }}

        QTextEdit[role="log"] {{
            color: {c['text']};
            background-color: {c['log']};
            border: 1px solid {c['border']};
            border-radius: 8px;
            padding: 12px;
            font-family: 'Cascadia Mono', 'Consolas', monospace;
            font-size: 14px;
        }}

        QProgressBar {{
            color: {c['text']};
            background-color: {c['surface_alt']};
            border: 1px solid {c['border']};
            border-radius: 7px;
            text-align: center;
        }}

        QProgressBar::chunk {{
            background-color: {c['primary']};
            border-radius: 6px;
        }}

        QTreeView,
        QListView,
        QTableView {{
            color: {c['text']};
            background-color: {c['surface']};
            alternate-background-color: {c['surface_alt']};
            border: 1px solid {c['border']};
            gridline-color: {c['border']};
            selection-color: #FFFFFF;
            selection-background-color: {c['selection']};
            outline: none;
        }}

        QHeaderView::section {{
            color: {c['text']};
            background-color: {c['surface_alt']};
            border: none;
            border-right: 1px solid {c['border']};
            border-bottom: 1px solid {c['border']};
            padding: 7px;
            font-weight: 600;
        }}

        QMenu,
        QMenuBar {{
            color: {c['text']};
            background-color: {c['surface']};
            border: 1px solid {c['border']};
        }}

        QMenu::item,
        QMenuBar::item {{
            background-color: transparent;
            padding: 7px 24px 7px 12px;
        }}

        QMenu::item:selected,
        QMenuBar::item:selected {{
            color: #FFFFFF;
            background-color: {c['selection']};
        }}

        QStatusBar {{
            color: {c['muted']};
            background-color: {c['surface_alt']};
            border-top: 1px solid {c['border']};
        }}

        QStatusBar::item {{
            border: none;
        }}

        QMessageBox {{
            background-color: {c['surface']};
        }}

        QMessageBox QLabel {{
            color: {c['text']};
            min-width: 280px;
        }}

        QToolTip {{
            color: {c['text']};
            background-color: {c['surface_alt']};
            border: 1px solid {c['border_strong']};
            padding: 5px;
        }}

        QScrollBar:vertical {{
            background-color: {c['surface_alt']};
            width: 12px;
            margin: 0;
        }}

        QScrollBar::handle:vertical {{
            background-color: {c['scroll_handle']};
            border-radius: 5px;
            min-height: 28px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {c['scroll_hover']};
        }}

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {{
            background: none;
            border: none;
        }}

        QScrollBar:horizontal {{
            background-color: {c['surface_alt']};
            height: 12px;
            margin: 0;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {c['scroll_handle']};
            border-radius: 5px;
            min-width: 28px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {c['scroll_hover']};
        }}

        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal,
        QScrollBar::add-page:horizontal,
        QScrollBar::sub-page:horizontal {{
            background: none;
            border: none;
        }}
    """


def apply_application_theme(app: QApplication, theme_name: object) -> str:
    """Apply one supported theme to the entire application."""

    normalized = normalize_theme(theme_name)
    app.setStyle("Fusion")
    app.setStyleSheet(build_stylesheet(normalized))
    return normalized
