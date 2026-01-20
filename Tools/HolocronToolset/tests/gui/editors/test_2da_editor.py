from __future__ import annotations

import os
import pathlib
import pytest
import sys
import unittest
from typing import TYPE_CHECKING
from unittest import TestCase

try:
    from qtpy.QtTest import QTest
    from qtpy.QtWidgets import QApplication
except (ImportError, ModuleNotFoundError):
    if not TYPE_CHECKING:
        QTest, QApplication = None, None  # type: ignore[misc, assignment]

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot
    from toolset.data.installation import HTInstallation

absolute_file_path = pathlib.Path(__file__).resolve()
TESTS_FILES_PATH = next(f for f in absolute_file_path.parents if f.name == "tests") / "test_files"

if (
    __name__ == "__main__"
    and getattr(sys, "frozen", False) is False
):
    def add_sys_path(p: pathlib.Path):
        working_dir = str(p)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)

    pykotor_path = absolute_file_path.parents[6] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        add_sys_path(pykotor_path.parent)
    gl_path = absolute_file_path.parents[6] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
    if gl_path.exists():
        add_sys_path(gl_path.parent)
    utility_path = absolute_file_path.parents[6] / "Libraries" / "Utility" / "src" / "utility"
    if utility_path.exists():
        add_sys_path(utility_path.parent)
    toolset_path = absolute_file_path.parents[6] / "Tools" / "HolocronToolset" / "src" / "toolset"
    if toolset_path.exists():
        add_sys_path(toolset_path.parent)


K1_PATH = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
K2_PATH = os.environ.get("K2_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II")

from pykotor.extract.installation import Installation
from pykotor.resource.formats.twoda.twoda_auto import read_2da
from pykotor.resource.type import ResourceType

from toolset.gui.editors.twoda import TwoDAEditor
from toolset.data.installation import HTInstallation


@unittest.skipIf(
    QTest is None or not QApplication,
    "qtpy is required, please run pip install -r requirements.txt before running this test.",
)
class TwoDAEditorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        # Make sure to configure this environment path before testing!
        from toolset.data.installation import HTInstallation

        cls.INSTALLATION = HTInstallation(K2_PATH, "", tsl=True)

    def setUp(self):
        from toolset.gui.editors.twoda import TwoDAEditor

        self.app: QApplication = QApplication([])
        self.editor: TwoDAEditor = TwoDAEditor(None, self.INSTALLATION)
        self.log_messages: list[str] = [os.linesep]

    def tearDown(self):
        self.app.deleteLater()

    def log_func(self, *args):
        self.log_messages.append("\t".join(args))

    def test_save_and_load(self):
        filepath = TESTS_FILES_PATH / "appearance.2da"

        data = filepath.read_bytes()
        old = read_2da(data)
        self.editor.load(filepath, "appearance", ResourceType.TwoDA, data)

        data, _ = self.editor.build()
        new = read_2da(data)

        diff = old.compare(new, self.log_func)
        assert diff
        self.assertDeepEqual(old, new)

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_2da_save_load_from_k1_installation(self):
        self.installation = Installation(K1_PATH)  # type: ignore[arg-type]
        for twoda_resource in (resource for resource in self.installation if resource.restype() is ResourceType.TwoDA):
            old = read_2da(twoda_resource.data())
            self.editor.load(twoda_resource.filepath(), twoda_resource.resname(), twoda_resource.restype(), twoda_resource.data())

            data, _ = self.editor.build()
            new = read_2da(data)

            diff = old.compare(new, self.log_func)
            assert diff, os.linesep.join(self.log_messages)

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_2da_save_load_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for twoda_resource in (resource for resource in self.installation if resource.restype() is ResourceType.TwoDA):
            old = read_2da(twoda_resource.data())
            self.editor.load(twoda_resource.filepath(), twoda_resource.resname(), twoda_resource.restype(), twoda_resource.data())

            data, _ = self.editor.build()
            new = read_2da(data)

            diff = old.compare(new, self.log_func)
            assert diff, os.linesep.join(self.log_messages)

    def assertDeepEqual(self, obj1, obj2, context=""):
        if isinstance(obj1, dict) and isinstance(obj2, dict):
            assert set(obj1.keys()) == set(obj2.keys()), context
            for key in obj1:
                new_context = f"{context}.{key}" if context else str(key)
                self.assertDeepEqual(obj1[key], obj2[key], new_context)

        elif isinstance(obj1, (list, tuple)) and isinstance(obj2, (list, tuple)):
            assert len(obj1) == len(obj2), context
            for index, (item1, item2) in enumerate(zip(obj1, obj2)):
                new_context = f"{context}[{index}]" if context else f"[{index}]"
                self.assertDeepEqual(item1, item2, new_context)

        elif hasattr(obj1, "__dict__") and hasattr(obj2, "__dict__"):
            self.assertDeepEqual(obj1.__dict__, obj2.__dict__, context)

        else:
            assert obj1 == obj2, context

    def test_basic_syntax(self):
        ...


if __name__ == "__main__":
    unittest.main()


# ============================================================================
# Additional UI tests (merged from test_ui_other_editors.py)
# ============================================================================


@pytest.mark.comprehensive
def test_twodaeditor_editor_help_dialog_opens_correct_file(qtbot: QtBot, installation: HTInstallation):
    """Test that TwoDAEditor help dialog opens and displays the correct help file (not 'Help File Not Found')."""
    from toolset.gui.dialogs.editor_help import EditorHelpDialog, get_wiki_path
    
    # Check if wiki file exists - fail test if it doesn't (test environment issue)
    toolset_wiki_path, root_wiki_path = get_wiki_path()
    assert toolset_wiki_path.exists(), f"Toolset wiki path: {toolset_wiki_path} does not exist"
    assert root_wiki_path is None or root_wiki_path.exists(), f"Root wiki path: {root_wiki_path} does not exist"
    wiki_file = toolset_wiki_path / "2DA-File-Format.md"
    if not wiki_file.exists():
        assert root_wiki_path is not None
        wiki_file = root_wiki_path / "2DA-File-Format.md"
        assert wiki_file.exists(), f"Wiki file '2DA-File-Format.md' not found at {wiki_file}"
    
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Trigger help dialog with the correct file for TwoDAEditor
    editor._show_help_dialog("2DA-File-Format.md")
    
    # Process events to allow dialog to be created
    qtbot.waitUntil(lambda: len(editor.findChildren(EditorHelpDialog)) > 0, timeout=2000)
    
    # Find the help dialog
    dialogs = [child for child in editor.findChildren(EditorHelpDialog)]
    assert len(dialogs) > 0, "Help dialog should be opened"
    
    dialog = dialogs[0]
    qtbot.addWidget(dialog)  # Add to qtbot for proper lifecycle management
    qtbot.waitExposed(dialog, timeout=2000)
    
    # Wait for content to load by checking if HTML is populated
    qtbot.waitUntil(lambda: dialog.text_browser.toHtml().strip() != "", timeout=2000)
    
    # Get the HTML content
    html = dialog.text_browser.toHtml()
    
    # Assert that "Help File Not Found" error is NOT shown
    assert "Help File Not Found" not in html, \
        f"Help file '2DA-File-Format.md' should be found, but error was shown. HTML: {html[:500]}"
    
    # Assert that some content is present (file was loaded successfully)
    assert len(html) > 100, "Help dialog should contain content"

    """Test TwoDA Editor."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    
    assert editor.isVisible()
    
    # Load 2DA
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if twoda_file.exists():
        editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
        twodaTableModel = editor.ui.twodaTable.model()
        assert twodaTableModel is not None
        assert twodaTableModel.rowCount() > 0
        
        # Build and verify it works
        data, _ = editor.build()
        assert len(data) > 0
        
        # Interact
        editor.ui.filterEdit.setText("test")
        # TODO: Add test to check filter logic if immediate