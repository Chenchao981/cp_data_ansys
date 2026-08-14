import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

from gui.multi_company_gui import MultiCompanyCPDataGUI
from gui.widgets.lion_die_count_widget import LionDieCountWidget


def test_sidebar_registers_and_switches_to_lion_die_count_page():
    app = QApplication.instance() or QApplication([])
    window = MultiCompanyCPDataGUI(remember_theme=False)

    assert "lion_die_count" in window.company_widgets
    assert isinstance(window.company_widgets["lion_die_count"], LionDieCountWidget)
    assert window.lion_die_count_button.text() == "lion-管芯数"

    window.on_company_selected("lion_die_count")

    assert window.current_company == "lion_die_count"
    assert window.content_stack.currentWidget() is window.company_widgets["lion_die_count"]
    assert window.lion_die_count_button.isChecked()
    window.hide()
    window.deleteLater()
    app.processEvents()

