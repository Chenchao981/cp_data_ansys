import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

from gui.path_preferences import RecentPathPreferences
from gui.widgets.guoyu_widget import GuoyuWidget
from gui.widgets.huahong_widget import HuaHongWidget
from gui.widgets.jetech_widget import JeTechWidget
from gui.widgets.lion_widget import LionWidget


def make_preferences(tmp_path, company_id="huahong"):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.IniFormat)
    settings.clear()
    return RecentPathPreferences(
        company_id,
        settings=settings,
        default_directory=tmp_path,
    )


def test_remembers_input_sources_and_output_directory_across_instances(tmp_path):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.IniFormat)
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    first = RecentPathPreferences(
        "huahong", settings=settings, default_directory=tmp_path
    )
    first.remember_input_sources([input_dir])
    first.remember_output_directory(output_dir)

    restored = RecentPathPreferences(
        "huahong", settings=settings, default_directory=tmp_path
    )
    assert restored.initial_input_sources() == (str(input_dir),)
    assert restored.input_start_directory() == str(input_dir)
    assert restored.output_directory() == str(output_dir)


def test_multiple_zip_selection_restores_files_and_opens_their_parent(tmp_path):
    first_zip = tmp_path / "lot-a.zip"
    second_zip = tmp_path / "lot-b.zip"
    first_zip.touch()
    second_zip.touch()
    preferences = make_preferences(tmp_path)

    preferences.remember_input_sources([first_zip, second_zip])

    assert preferences.initial_input_sources() == (
        str(first_zip),
        str(second_zip),
    )
    assert preferences.input_start_directory() == str(tmp_path)


def test_huahong_7z_selection_is_restored(tmp_path):
    archive = tmp_path / "lot.7z"
    archive.touch()
    preferences = make_preferences(tmp_path)

    preferences.remember_input_sources([archive])

    assert preferences.initial_input_sources() == (str(archive),)
    assert preferences.input_start_directory() == str(tmp_path)


def test_missing_saved_paths_fall_back_to_default_directory(tmp_path):
    preferences = make_preferences(tmp_path)
    preferences.remember_input_sources([tmp_path / "missing.zip"])
    preferences.remember_output_directory(tmp_path / "missing-output")

    assert preferences.initial_input_sources() == (str(tmp_path),)
    assert preferences.output_directory() == str(tmp_path)


def test_deleted_zip_still_opens_its_existing_parent(tmp_path):
    default_dir = tmp_path / "desktop"
    source_dir = tmp_path / "source"
    default_dir.mkdir()
    source_dir.mkdir()
    archive = source_dir / "processed.zip"
    archive.touch()
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.IniFormat)
    preferences = RecentPathPreferences(
        "huahong", settings=settings, default_directory=default_dir
    )
    preferences.remember_input_sources([archive])
    archive.unlink()

    restored_sources = preferences.initial_input_sources()

    assert restored_sources == (str(default_dir),)
    assert preferences.input_start_directory(restored_sources) == str(source_dir)


def test_company_paths_are_kept_separate(tmp_path):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.IniFormat)
    hh_input = tmp_path / "hh"
    jt_input = tmp_path / "jt"
    hh_input.mkdir()
    jt_input.mkdir()

    RecentPathPreferences(
        "huahong", settings=settings, default_directory=tmp_path
    ).remember_input_sources([hh_input])
    RecentPathPreferences(
        "jetech", settings=settings, default_directory=tmp_path
    ).remember_input_sources([jt_input])

    assert RecentPathPreferences(
        "huahong", settings=settings, default_directory=tmp_path
    ).initial_input_sources() == (str(hh_input),)
    assert RecentPathPreferences(
        "jetech", settings=settings, default_directory=tmp_path
    ).initial_input_sources() == (str(jt_input),)


@pytest.mark.parametrize(
    ("widget_class", "company_id"),
    [
        (HuaHongWidget, "huahong"),
        (JeTechWidget, "jetech"),
        (LionWidget, "lion"),
        (GuoyuWidget, "guoyu"),
    ],
)
def test_company_widgets_restore_their_saved_paths(
    tmp_path, widget_class, company_id
):
    app = QApplication.instance() or QApplication([])
    input_dir = tmp_path / f"{company_id}-input"
    output_dir = tmp_path / f"{company_id}-output"
    input_dir.mkdir()
    output_dir.mkdir()
    preferences = make_preferences(tmp_path, company_id)
    preferences.remember_input_sources([input_dir])
    preferences.remember_output_directory(output_dir)

    widget = widget_class(path_preferences=preferences)

    assert widget.input_path_edit.text() == str(input_dir)
    assert widget.output_path_edit.text() == str(output_dir)

    widget.hide()
    widget.deleteLater()
    app.processEvents()
