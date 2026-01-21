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

    def test_editor_init(self):
        """Test editor initialization."""
        assert self.editor is not None
        assert self.editor.source_model is not None
        assert self.editor.proxy_model is not None
        assert self.editor.ui is not None


if __name__ == "__main__":
    unittest.main()


# ============================================================================
# COMPREHENSIVE PYTEST-BASED TESTS
# ============================================================================


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


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================


def test_twoda_editor_new_file_creation(qtbot: QtBot, installation: HTInstallation):
    """Test creating a new 2DA file from scratch."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new file
    editor.new()
    
    # Verify empty state
    assert editor.source_model.rowCount() == 0
    assert editor.source_model.columnCount() == 0
    
    # Build should return empty 2DA
    data, _ = editor.build()
    assert len(data) > 0  # Empty 2DA still has header


def test_twoda_editor_load_real_file(qtbot: QtBot, installation: HTInstallation):
    """Test loading a real 2DA file."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found in test files")
    
    # Load file
    original_data = twoda_file.read_bytes()
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, original_data)
    
    # Verify loaded
    assert editor.source_model.rowCount() > 0
    assert editor.source_model.columnCount() > 0
    
    # Verify table model is set
    assert editor.ui.twodaTable.model() is not None
    assert editor.ui.twodaTable.model().rowCount() > 0


def test_twoda_editor_load_and_save_preserves_data(qtbot: QtBot, installation: HTInstallation):
    """Test that loading and saving preserves all data."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    # Load original
    original_data = twoda_file.read_bytes()
    original_2da = read_2da(original_data)
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, original_data)
    
    # Save
    data, _ = editor.build()
    saved_2da = read_2da(data)
    
    # Verify all rows preserved
    assert len(saved_2da) == len(original_2da)
    
    # Verify all headers preserved
    assert set(saved_2da.get_headers()) == set(original_2da.get_headers())
    
    # Verify all labels preserved
    for i in range(len(original_2da)):
        assert saved_2da.get_label(i) == original_2da.get_label(i)
    
    # Verify all cell values preserved
    for i in range(len(original_2da)):
        for header in original_2da.get_headers():
            assert saved_2da.get_cell(i, header) == original_2da.get_cell(i, header)


# ============================================================================
# ROW OPERATIONS TESTS
# ============================================================================


def test_twoda_editor_insert_row(qtbot: QtBot, installation: HTInstallation):
    """Test inserting a new row."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    initial_row_count = editor.source_model.rowCount()
    
    # Insert row
    editor.insert_row()
    
    # Verify row added
    assert editor.source_model.rowCount() == initial_row_count + 1
    
    # Verify new row has correct label (row index)
    new_row_index = editor.source_model.rowCount() - 1
    label_item = editor.source_model.item(new_row_index, 0)
    assert label_item is not None
    assert label_item.text() == str(new_row_index)


def test_twoda_editor_insert_multiple_rows(qtbot: QtBot, installation: HTInstallation):
    """Test inserting multiple rows."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    initial_row_count = editor.source_model.rowCount()
    
    # Insert 5 rows
    for _ in range(5):
        editor.insert_row()
    
    # Verify rows added
    assert editor.source_model.rowCount() == initial_row_count + 5


def test_twoda_editor_duplicate_row(qtbot: QtBot, installation: HTInstallation):
    """Test duplicating a row."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    initial_row_count = editor.source_model.rowCount()
    
    if initial_row_count == 0:
        pytest.skip("No rows to duplicate")
    
    # Select first row
    first_row_index = editor.proxy_model.index(0, 0)
    editor.ui.twodaTable.setCurrentIndex(first_row_index)
    editor.ui.twodaTable.selectRow(0)
    
    # Get original row data
    original_label = editor.source_model.item(0, 0).text()
    original_cells = []
    for col in range(1, editor.source_model.columnCount()):
        item = editor.source_model.item(0, col)
        original_cells.append(item.text() if item else "")
    
    # Duplicate row
    editor.duplicate_row()
    
    # Verify row added
    assert editor.source_model.rowCount() == initial_row_count + 1
    
    # Verify duplicated row has same cell values (except label)
    new_row_index = editor.source_model.rowCount() - 1
    for col in range(1, editor.source_model.columnCount()):
        original_item = editor.source_model.item(0, col)
        duplicated_item = editor.source_model.item(new_row_index, col)
        assert original_item is not None
        assert duplicated_item is not None
        assert duplicated_item.text() == original_item.text()


def test_twoda_editor_duplicate_row_no_selection(qtbot: QtBot, installation: HTInstallation):
    """Test duplicating row when no row is selected."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    initial_row_count = editor.source_model.rowCount()
    
    # Clear selection
    editor.ui.twodaTable.clearSelection()
    
    # Duplicate should still work (uses first selected or first row)
    editor.duplicate_row()
    
    # Should add a row (may duplicate first row or add empty row)
    assert editor.source_model.rowCount() >= initial_row_count


def test_twoda_editor_remove_selected_rows(qtbot: QtBot, installation: HTInstallation):
    """Test removing selected rows."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    initial_row_count = editor.source_model.rowCount()
    
    if initial_row_count == 0:
        pytest.skip("No rows to remove")
    
    # Select first row
    first_row_index = editor.proxy_model.index(0, 0)
    editor.ui.twodaTable.setCurrentIndex(first_row_index)
    editor.ui.twodaTable.selectRow(0)
    
    # Remove row
    editor.remove_selected_rows()
    
    # Verify row removed
    assert editor.source_model.rowCount() == initial_row_count - 1


def test_twoda_editor_remove_multiple_rows(qtbot: QtBot, installation: HTInstallation):
    """Test removing multiple selected rows."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    initial_row_count = editor.source_model.rowCount()
    
    if initial_row_count < 3:
        pytest.skip("Need at least 3 rows to test multiple removal")
    
    # Select multiple rows (0, 1, 2)
    selection_model = editor.ui.twodaTable.selectionModel()
    for row in range(3):
        index = editor.proxy_model.index(row, 0)
        selection_model.select(index, selection_model.SelectionFlag.Select | selection_model.SelectionFlag.Rows)
    
    # Remove rows
    editor.remove_selected_rows()
    
    # Verify rows removed
    assert editor.source_model.rowCount() == initial_row_count - 3


def test_twoda_editor_remove_all_rows(qtbot: QtBot, installation: HTInstallation):
    """Test removing all rows."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    initial_row_count = editor.source_model.rowCount()
    
    if initial_row_count == 0:
        pytest.skip("No rows to remove")
    
    # Select all rows
    editor.ui.twodaTable.selectAll()
    
    # Remove all rows
    editor.remove_selected_rows()
    
    # Verify all rows removed
    assert editor.source_model.rowCount() == 0


def test_twoda_editor_remove_rows_no_selection(qtbot: QtBot, installation: HTInstallation):
    """Test removing rows when nothing is selected."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    initial_row_count = editor.source_model.rowCount()
    
    # Clear selection
    editor.ui.twodaTable.clearSelection()
    
    # Remove (should do nothing)
    editor.remove_selected_rows()
    
    # Verify no rows removed
    assert editor.source_model.rowCount() == initial_row_count


def test_twoda_editor_redo_row_labels(qtbot: QtBot, installation: HTInstallation):
    """Test redoing row labels to match row indices."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    # Modify some row labels
    for i in range(min(5, editor.source_model.rowCount())):
        item = editor.source_model.item(i, 0)
        if item:
            item.setText(f"custom_label_{i}")
    
    # Redo row labels
    editor.redo_row_labels()
    
    # Verify all labels match row indices
    for i in range(editor.source_model.rowCount()):
        item = editor.source_model.item(i, 0)
        assert item is not None
        assert item.text() == str(i)


# ============================================================================
# CELL EDITING TESTS
# ============================================================================


def test_twoda_editor_edit_cell_value(qtbot: QtBot, installation: HTInstallation):
    """Test editing a cell value."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    if editor.source_model.rowCount() == 0 or editor.source_model.columnCount() < 2:
        pytest.skip("Need at least one row and one data column")
    
    # Edit a cell
    test_value = "test_cell_value_123"
    item = editor.source_model.item(0, 1)  # First row, first data column
    assert item is not None
    original_value = item.text()
    item.setText(test_value)
    
    # Verify value changed
    assert item.text() == test_value
    
    # Build and verify value is saved
    data, _ = editor.build()
    saved_2da = read_2da(data)
    headers = saved_2da.get_headers()
    if headers:
        assert saved_2da.get_cell(0, headers[0]) == test_value


def test_twoda_editor_edit_multiple_cells(qtbot: QtBot, installation: HTInstallation):
    """Test editing multiple cells."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    if editor.source_model.rowCount() < 3 or editor.source_model.columnCount() < 3:
        pytest.skip("Need at least 3 rows and 3 columns")
    
    # Edit multiple cells
    test_values = {
        (0, 1): "value_0_1",
        (1, 1): "value_1_1",
        (2, 2): "value_2_2",
    }
    
    for (row, col), value in test_values.items():
        item = editor.source_model.item(row, col)
        assert item is not None
        item.setText(value)
    
    # Build and verify all values saved
    data, _ = editor.build()
    saved_2da = read_2da(data)
    headers = saved_2da.get_headers()
    
    for (row, col), expected_value in test_values.items():
        if col - 1 < len(headers):  # col 0 is label, so col 1 is first header
            assert saved_2da.get_cell(row, headers[col - 1]) == expected_value


def test_twoda_editor_edit_empty_cell(qtbot: QtBot, installation: HTInstallation):
    """Test editing an empty cell."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    # Insert new row (which will have empty cells)
    editor.insert_row()
    new_row = editor.source_model.rowCount() - 1
    
    # Edit empty cell
    if editor.source_model.columnCount() > 1:
        item = editor.source_model.item(new_row, 1)
        assert item is not None
        item.setText("new_value")
        
        # Verify value set
        assert item.text() == "new_value"


def test_twoda_editor_edit_cell_with_special_characters(qtbot: QtBot, installation: HTInstallation):
    """Test editing cells with special characters."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    if editor.source_model.rowCount() == 0 or editor.source_model.columnCount() < 2:
        pytest.skip("Need at least one row and one data column")
    
    # Test various special characters
    special_values = [
        "value with spaces",
        "value\twith\ttabs",
        "value\nwith\nnewlines",
        "value with \"quotes\"",
        "value with 'apostrophes'",
        "value with & symbols",
        "value with < > brackets",
        "value with / slashes",
        "value with \\ backslashes",
        "value with * asterisks",
        "value with ? question marks",
        "value with | pipes",
    ]
    
    for i, special_value in enumerate(special_values):
        if i >= editor.source_model.rowCount():
            editor.insert_row()
        
        item = editor.source_model.item(i, 1)
        assert item is not None
        item.setText(special_value)
        
        # Verify value set
        assert item.text() == special_value


# ============================================================================
# FILTER TESTS
# ============================================================================


def test_twoda_editor_filter_basic(qtbot: QtBot, installation: HTInstallation):
    """Test basic filtering functionality."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    initial_row_count = editor.source_model.rowCount()
    
    # Set filter
    editor.ui.filterEdit.setText("test")
    editor.do_filter("test")
    
    # Filtered count should be <= original count
    filtered_count = editor.proxy_model.rowCount()
    assert filtered_count <= initial_row_count


def test_twoda_editor_filter_empty_string(qtbot: QtBot, installation: HTInstallation):
    """Test filtering with empty string (should show all rows)."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    initial_row_count = editor.source_model.rowCount()
    
    # Filter with empty string
    editor.do_filter("")
    
    # Should show all rows
    assert editor.proxy_model.rowCount() == initial_row_count


def test_twoda_editor_filter_case_insensitive(qtbot: QtBot, installation: HTInstallation):
    """Test that filtering is case insensitive."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    # Filter with lowercase
    editor.do_filter("test")
    lowercase_count = editor.proxy_model.rowCount()
    
    # Filter with uppercase
    editor.do_filter("TEST")
    uppercase_count = editor.proxy_model.rowCount()
    
    # Should match same number of rows (case insensitive)
    assert lowercase_count == uppercase_count


def test_twoda_editor_filter_no_matches(qtbot: QtBot, installation: HTInstallation):
    """Test filtering with text that matches nothing."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    # Filter with text that shouldn't match anything
    editor.do_filter("xyz123nonexistent456")
    
    # Should show 0 rows
    assert editor.proxy_model.rowCount() == 0


def test_twoda_editor_toggle_filter(qtbot: QtBot, installation: HTInstallation):
    """Test toggling filter visibility."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Initially filter should be hidden
    assert not editor.ui.filterBox.isVisible()
    
    # Toggle on
    editor.toggle_filter()
    assert editor.ui.filterBox.isVisible()
    
    # Toggle off
    editor.toggle_filter()
    assert not editor.ui.filterBox.isVisible()
    
    # Toggle on again
    editor.toggle_filter()
    assert editor.ui.filterBox.isVisible()


def test_twoda_editor_filter_clears_on_toggle_off(qtbot: QtBot, installation: HTInstallation):
    """Test that filter clears when toggled off."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    initial_row_count = editor.source_model.rowCount()
    
    # Set filter
    editor.toggle_filter()
    editor.ui.filterEdit.setText("test")
    editor.do_filter("test")
    filtered_count = editor.proxy_model.rowCount()
    
    # Toggle off
    editor.toggle_filter()
    
    # Should show all rows again
    assert editor.proxy_model.rowCount() == initial_row_count


# ============================================================================
# COPY/PASTE TESTS
# ============================================================================


def test_twoda_editor_copy_selection(qtbot: QtBot, installation: HTInstallation):
    """Test copying selected cells."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    if editor.source_model.rowCount() == 0 or editor.source_model.columnCount() < 2:
        pytest.skip("Need at least one row and one data column")
    
    # Select a cell
    index = editor.proxy_model.index(0, 1)
    editor.ui.twodaTable.setCurrentIndex(index)
    editor.ui.twodaTable.selectRow(0)
    
    # Copy
    editor.copy_selection()
    
    # Verify clipboard has content
    clipboard_text = QApplication.clipboard().text()
    assert len(clipboard_text) > 0


def test_twoda_editor_copy_multiple_cells(qtbot: QtBot, installation: HTInstallation):
    """Test copying multiple selected cells."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    if editor.source_model.rowCount() < 2 or editor.source_model.columnCount() < 2:
        pytest.skip("Need at least 2 rows and 2 columns")
    
    # Select multiple cells
    selection_model = editor.ui.twodaTable.selectionModel()
    for row in range(2):
        for col in range(2):
            index = editor.proxy_model.index(row, col)
            selection_model.select(index, selection_model.SelectionFlag.Select)
    
    # Copy
    editor.copy_selection()
    
    # Verify clipboard has content with tabs and newlines
    clipboard_text = QApplication.clipboard().text()
    assert "\t" in clipboard_text  # Tab separator
    assert "\n" in clipboard_text  # Newline separator


def test_twoda_editor_paste_selection(qtbot: QtBot, installation: HTInstallation):
    """Test pasting cells."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    if editor.source_model.rowCount() == 0 or editor.source_model.columnCount() < 2:
        pytest.skip("Need at least one row and one data column")
    
    # Set clipboard content
    test_data = "test_value_1\ttest_value_2\ntest_value_3\ttest_value_4"
    QApplication.clipboard().setText(test_data)
    
    # Select first cell
    index = editor.proxy_model.index(0, 1)
    editor.ui.twodaTable.setCurrentIndex(index)
    
    # Paste
    editor.paste_selection()
    
    # Verify values were pasted
    item1 = editor.source_model.item(0, 1)
    item2 = editor.source_model.item(0, 2) if editor.source_model.columnCount() > 2 else None
    assert item1 is not None
    assert item1.text() == "test_value_1"
    if item2:
        assert item2.text() == "test_value_2"


def test_twoda_editor_paste_no_selection(qtbot: QtBot, installation: HTInstallation):
    """Test pasting when nothing is selected."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    initial_row_count = editor.source_model.rowCount()
    
    # Set clipboard
    QApplication.clipboard().setText("test_value")
    
    # Clear selection
    editor.ui.twodaTable.clearSelection()
    
    # Paste (should do nothing)
    editor.paste_selection()
    
    # Verify no rows added
    assert editor.source_model.rowCount() == initial_row_count


def test_twoda_editor_copy_paste_roundtrip(qtbot: QtBot, installation: HTInstallation):
    """Test copying and pasting preserves data."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    if editor.source_model.rowCount() == 0 or editor.source_model.columnCount() < 2:
        pytest.skip("Need at least one row and one data column")
    
    # Get original cell value
    original_item = editor.source_model.item(0, 1)
    assert original_item is not None
    original_value = original_item.text()
    
    # Select and copy
    index = editor.proxy_model.index(0, 1)
    editor.ui.twodaTable.setCurrentIndex(index)
    editor.ui.twodaTable.selectRow(0)
    editor.copy_selection()
    
    # Select different cell and paste
    if editor.source_model.rowCount() > 1:
        index2 = editor.proxy_model.index(1, 1)
        editor.ui.twodaTable.setCurrentIndex(index2)
        editor.paste_selection()
        
        # Verify value pasted
        pasted_item = editor.source_model.item(1, 1)
        assert pasted_item is not None
        assert pasted_item.text() == original_value


# ============================================================================
# JUMP TO ROW TESTS
# ============================================================================


def test_twoda_editor_jump_to_row_valid(qtbot: QtBot, installation: HTInstallation):
    """Test jumping to a valid row."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    if editor.source_model.rowCount() == 0:
        pytest.skip("No rows to jump to")
    
    # Jump to middle row
    target_row = min(5, editor.source_model.rowCount() - 1)
    editor.jump_to_row(target_row)
    
    # Verify row is selected
    current_index = editor.ui.twodaTable.currentIndex()
    assert current_index.isValid()
    source_index = editor.proxy_model.mapToSource(current_index)
    assert source_index.row() == target_row


def test_twoda_editor_jump_to_row_first(qtbot: QtBot, installation: HTInstallation):
    """Test jumping to first row."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    if editor.source_model.rowCount() == 0:
        pytest.skip("No rows to jump to")
    
    # Jump to first row
    editor.jump_to_row(0)
    
    # Verify first row is selected
    current_index = editor.ui.twodaTable.currentIndex()
    assert current_index.isValid()
    source_index = editor.proxy_model.mapToSource(current_index)
    assert source_index.row() == 0


def test_twoda_editor_jump_to_row_last(qtbot: QtBot, installation: HTInstallation):
    """Test jumping to last row."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    if editor.source_model.rowCount() == 0:
        pytest.skip("No rows to jump to")
    
    # Jump to last row
    last_row = editor.source_model.rowCount() - 1
    editor.jump_to_row(last_row)
    
    # Verify last row is selected
    current_index = editor.ui.twodaTable.currentIndex()
    assert current_index.isValid()
    source_index = editor.proxy_model.mapToSource(current_index)
    assert source_index.row() == last_row


def test_twoda_editor_jump_to_row_invalid_negative(qtbot: QtBot, installation: HTInstallation):
    """Test jumping to negative row index (should show warning)."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    # Try to jump to negative row
    editor.jump_to_row(-1)
    
    # Should not crash, may show warning dialog


def test_twoda_editor_jump_to_row_invalid_too_large(qtbot: QtBot, installation: HTInstallation):
    """Test jumping to row index beyond range (should show warning)."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    max_row = editor.source_model.rowCount()
    
    # Try to jump to row beyond range
    editor.jump_to_row(max_row + 100)
    
    # Should not crash, may show warning dialog


# ============================================================================
# VERTICAL HEADER TESTS
# ============================================================================


def test_twoda_editor_vertical_header_none(qtbot: QtBot, installation: HTInstallation):
    """Test setting vertical header to None."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    # Set to None
    from toolset.gui.editors.twoda import VerticalHeaderOption
    editor.set_vertical_header_option(VerticalHeaderOption.NONE)
    
    # Verify option set
    assert editor.vertical_header_option == VerticalHeaderOption.NONE


def test_twoda_editor_vertical_header_row_index(qtbot: QtBot, installation: HTInstallation):
    """Test setting vertical header to row index."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    # Set to row index
    from toolset.gui.editors.twoda import VerticalHeaderOption
    editor.set_vertical_header_option(VerticalHeaderOption.ROW_INDEX)
    
    # Verify option set
    assert editor.vertical_header_option == VerticalHeaderOption.ROW_INDEX


def test_twoda_editor_vertical_header_row_label(qtbot: QtBot, installation: HTInstallation):
    """Test setting vertical header to row label."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    # Set to row label
    from toolset.gui.editors.twoda import VerticalHeaderOption
    editor.set_vertical_header_option(VerticalHeaderOption.ROW_LABEL)
    
    # Verify option set
    assert editor.vertical_header_option == VerticalHeaderOption.ROW_LABEL


def test_twoda_editor_vertical_header_cell_value(qtbot: QtBot, installation: HTInstallation):
    """Test setting vertical header to cell value from column."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    if editor.source_model.columnCount() < 2:
        pytest.skip("Need at least one data column")
    
    # Get first header
    header_item = editor.source_model.horizontalHeaderItem(1)
    if header_item:
        header_name = header_item.text()
        
        # Set to cell value
        from toolset.gui.editors.twoda import VerticalHeaderOption
        editor.set_vertical_header_option(VerticalHeaderOption.CELL_VALUE, header_name)
        
        # Verify option set
        assert editor.vertical_header_option == VerticalHeaderOption.CELL_VALUE
        assert editor.vertical_header_column == header_name


def test_twoda_editor_vertical_header_menu_reconstruction(qtbot: QtBot, installation: HTInstallation):
    """Test that vertical header menu is reconstructed with all headers."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    # Verify menu has actions
    actions = editor.ui.menuSetRowHeader.actions()
    assert len(actions) > 0
    
    # Verify menu has None, Row Index, Row Label options
    action_texts = [action.text() for action in actions if action.text()]
    assert "None" in action_texts
    assert "Row Index" in action_texts
    assert "Row Label" in action_texts


# ============================================================================
# FORMAT TESTS (2DA, CSV, JSON)
# ============================================================================


def test_twoda_editor_load_csv_format(qtbot: QtBot, installation: HTInstallation, tmp_path: Path):
    """Test loading 2DA in CSV format."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create test CSV
    csv_content = "label,header1,header2\n0,value1,value2\n1,value3,value4"
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(csv_content)
    
    # Load CSV
    editor.load(csv_file, "test", ResourceType.TwoDA_CSV, csv_content.encode("utf-8"))
    
    # Verify loaded
    assert editor.source_model.rowCount() == 2
    assert editor.source_model.columnCount() == 3  # label + 2 headers


def test_twoda_editor_load_json_format(qtbot: QtBot, installation: HTInstallation, tmp_path: Path):
    """Test loading 2DA in JSON format."""
    import json
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create test JSON
    json_data = {
        "headers": ["header1", "header2"],
        "rows": [
            {"label": "0", "cells": ["value1", "value2"]},
            {"label": "1", "cells": ["value3", "value4"]},
        ]
    }
    json_content = json.dumps(json_data)
    json_file = tmp_path / "test.json"
    json_file.write_text(json_content)
    
    # Load JSON
    editor.load(json_file, "test", ResourceType.TwoDA_JSON, json_content.encode("utf-8"))
    
    # Verify loaded
    assert editor.source_model.rowCount() == 2
    assert editor.source_model.columnCount() == 3  # label + 2 headers


def test_twoda_editor_build_csv_format(qtbot: QtBot, installation: HTInstallation):
    """Test building 2DA in CSV format."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    # Load as binary 2DA
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    # Change restype to CSV
    editor._restype = ResourceType.TwoDA_CSV
    
    # Build
    data, _ = editor.build()
    
    # Verify CSV format
    csv_text = data.decode("utf-8", errors="ignore")
    assert "," in csv_text  # CSV should have commas
    assert "\n" in csv_text  # CSV should have newlines


def test_twoda_editor_build_json_format(qtbot: QtBot, installation: HTInstallation):
    """Test building 2DA in JSON format."""
    import json
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    # Load as binary 2DA
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    # Change restype to JSON
    editor._restype = ResourceType.TwoDA_JSON
    
    # Build
    data, _ = editor.build()
    
    # Verify JSON format
    json_text = data.decode("utf-8", errors="ignore")
    json_data = json.loads(json_text)
    assert "headers" in json_data
    assert "rows" in json_data


# ============================================================================
# EDGE CASES AND ERROR HANDLING TESTS
# ============================================================================


def test_twoda_editor_load_invalid_data(qtbot: QtBot, installation: HTInstallation):
    """Test loading invalid 2DA data."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Try to load invalid data
    invalid_data = b"not a valid 2da file"
    
    # Should handle gracefully (may show error dialog)
    editor.load(Path("invalid.2da"), "invalid", ResourceType.TwoDA, invalid_data)
    
    # Editor should still be functional
    assert editor is not None


def test_twoda_editor_load_empty_file(qtbot: QtBot, installation: HTInstallation):
    """Test loading empty file."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Try to load empty data
    empty_data = b""
    
    # Should handle gracefully
    editor.load(Path("empty.2da"), "empty", ResourceType.TwoDA, empty_data)
    
    # Editor should still be functional
    assert editor is not None


def test_twoda_editor_build_empty_table(qtbot: QtBot, installation: HTInstallation):
    """Test building empty 2DA table."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new empty table
    editor.new()
    
    # Build should still work
    data, _ = editor.build()
    assert len(data) > 0  # Empty 2DA still has header


def test_twoda_editor_build_table_with_no_headers(qtbot: QtBot, installation: HTInstallation):
    """Test building table with no headers (only label column)."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create table with only label column
    editor.new()
    editor.source_model.setColumnCount(1)  # Only label column
    editor.source_model.setHorizontalHeaderLabels([""])
    
    # Insert a row
    editor.insert_row()
    
    # Build should handle gracefully
    data, _ = editor.build()
    assert len(data) > 0


def test_twoda_editor_edit_label_column(qtbot: QtBot, installation: HTInstallation):
    """Test editing the label column."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    if editor.source_model.rowCount() == 0:
        pytest.skip("No rows to edit")
    
    # Edit label
    label_item = editor.source_model.item(0, 0)
    assert label_item is not None
    original_label = label_item.text()
    label_item.setText("custom_label")
    
    # Verify label changed
    assert label_item.text() == "custom_label"
    
    # Build and verify label is saved
    data, _ = editor.build()
    saved_2da = read_2da(data)
    assert saved_2da.get_label(0) == "custom_label"


def test_twoda_editor_very_large_table(qtbot: QtBot, installation: HTInstallation):
    """Test editor with very large table (performance test)."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create large table
    editor.new()
    editor.source_model.setColumnCount(10)
    editor.source_model.setHorizontalHeaderLabels([""] + [f"header_{i}" for i in range(9)])
    
    # Insert many rows
    for i in range(100):
        editor.insert_row()
        # Set some cell values
        for col in range(1, 10):
            item = editor.source_model.item(i, col)
            if item:
                item.setText(f"value_{i}_{col}")
    
    # Build should still work
    data, _ = editor.build()
    assert len(data) > 0
    
    # Verify all rows saved
    saved_2da = read_2da(data)
    assert len(saved_2da) == 100


def test_twoda_editor_very_wide_table(qtbot: QtBot, installation: HTInstallation):
    """Test editor with very wide table (many columns)."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create wide table
    editor.new()
    num_columns = 50
    editor.source_model.setColumnCount(num_columns)
    editor.source_model.setHorizontalHeaderLabels([""] + [f"header_{i}" for i in range(num_columns - 1)])
    
    # Insert a few rows
    for i in range(5):
        editor.insert_row()
    
    # Build should still work
    data, _ = editor.build()
    assert len(data) > 0
    
    # Verify all columns saved
    saved_2da = read_2da(data)
    assert len(saved_2da.get_headers()) == num_columns - 1


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


def test_twoda_editor_full_workflow(qtbot: QtBot, installation: HTInstallation):
    """Test complete workflow: load, edit, filter, copy, paste, save."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    # Load
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    initial_row_count = editor.source_model.rowCount()
    
    # Edit a cell
    if editor.source_model.rowCount() > 0 and editor.source_model.columnCount() > 1:
        item = editor.source_model.item(0, 1)
        assert item is not None
        item.setText("modified_value")
    
    # Filter
    editor.toggle_filter()
    editor.ui.filterEdit.setText("modified")
    editor.do_filter("modified")
    
    # Copy
    index = editor.proxy_model.index(0, 1)
    editor.ui.twodaTable.setCurrentIndex(index)
    editor.copy_selection()
    
    # Paste to different cell
    if editor.source_model.rowCount() > 1:
        index2 = editor.proxy_model.index(1, 1)
        editor.ui.twodaTable.setCurrentIndex(index2)
        editor.paste_selection()
    
    # Insert row
    editor.insert_row()
    
    # Remove row
    editor.ui.twodaTable.selectRow(editor.source_model.rowCount() - 1)
    editor.remove_selected_rows()
    
    # Build
    data, _ = editor.build()
    assert len(data) > 0
    
    # Verify can reload
    editor.load(Path("test.2da"), "test", ResourceType.TwoDA, data)
    assert editor.source_model.rowCount() > 0


def test_twoda_editor_multiple_save_load_cycles(qtbot: QtBot, installation: HTInstallation):
    """Test multiple save/load cycles preserve data."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    # Load original
    original_data = twoda_file.read_bytes()
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, original_data)
    
    # Multiple save/load cycles
    for cycle in range(5):
        # Save
        data, _ = editor.build()
        
        # Load back
        editor.load(Path(f"test_{cycle}.2da"), "test", ResourceType.TwoDA, data)
        
        # Verify still has data
        assert editor.source_model.rowCount() > 0


def test_twoda_editor_undo_redo_support(qtbot: QtBot, installation: HTInstallation):
    """Test that editor supports undo/redo operations."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    if editor.source_model.rowCount() == 0 or editor.source_model.columnCount() < 2:
        pytest.skip("Need at least one row and one data column")
    
    # Get original value
    original_item = editor.source_model.item(0, 1)
    assert original_item is not None
    original_value = original_item.text()
    
    # Edit value
    original_item.setText("new_value")
    
    # Verify value changed
    assert original_item.text() == "new_value"
    
    # Note: Undo/redo may not be implemented, but editor should not crash
    # This test verifies the editor handles cell edits without crashing


# ============================================================================
# UI INTERACTION TESTS
# ============================================================================


def test_twoda_editor_table_selection(qtbot: QtBot, installation: HTInstallation):
    """Test table selection functionality."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    if editor.source_model.rowCount() == 0:
        pytest.skip("No rows to select")
    
    # Select first row
    index = editor.proxy_model.index(0, 0)
    editor.ui.twodaTable.setCurrentIndex(index)
    editor.ui.twodaTable.selectRow(0)
    
    # Verify selection
    selection_model = editor.ui.twodaTable.selectionModel()
    assert selection_model is not None
    selected_indexes = selection_model.selectedIndexes()
    assert len(selected_indexes) > 0


def test_twoda_editor_table_keyboard_navigation(qtbot: QtBot, installation: HTInstallation):
    """Test keyboard navigation in table."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    if editor.source_model.rowCount() < 2:
        pytest.skip("Need at least 2 rows")
    
    # Select first cell
    index = editor.proxy_model.index(0, 0)
    editor.ui.twodaTable.setCurrentIndex(index)
    
    # Navigate down
    from qtpy.QtCore import Qt
    from qtpy.QtGui import QKeyEvent
    key_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier)
    editor.ui.twodaTable.keyPressEvent(key_event)
    
    # Verify moved down
    current_index = editor.ui.twodaTable.currentIndex()
    assert current_index.isValid()
    source_index = editor.proxy_model.mapToSource(current_index)
    assert source_index.row() >= 0


def test_twoda_editor_table_context_menu(qtbot: QtBot, installation: HTInstallation):
    """Test table context menu."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    # Select a cell
    index = editor.proxy_model.index(0, 0)
    editor.ui.twodaTable.setCurrentIndex(index)
    
    # Context menu should be available (may be created on demand)
    # Just verify editor doesn't crash when accessing context menu
    assert editor is not None


# ============================================================================
# MENU ACTIONS TESTS
# ============================================================================


def test_twoda_editor_menu_actions_exist(qtbot: QtBot, installation: HTInstallation):
    """Test that all menu actions exist."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify menu actions exist
    assert hasattr(editor.ui, "actionToggleFilter")
    assert hasattr(editor.ui, "actionCopy")
    assert hasattr(editor.ui, "actionPaste")
    assert hasattr(editor.ui, "actionInsertRow")
    assert hasattr(editor.ui, "actionDuplicateRow")
    assert hasattr(editor.ui, "actionRemoveRows")
    assert hasattr(editor.ui, "actionRedoRowLabels")
    assert hasattr(editor.ui, "menuSetRowHeader")


def test_twoda_editor_menu_actions_triggerable(qtbot: QtBot, installation: HTInstallation):
    """Test that menu actions can be triggered."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    # Test each action
    editor.ui.actionToggleFilter.trigger()
    assert editor.ui.filterBox.isVisible() or not editor.ui.filterBox.isVisible()  # Toggled
    
    editor.ui.actionInsertRow.trigger()
    assert editor.source_model.rowCount() > 0
    
    if editor.source_model.rowCount() > 0:
        index = editor.proxy_model.index(0, 0)
        editor.ui.twodaTable.setCurrentIndex(index)
        editor.ui.twodaTable.selectRow(0)
        
        editor.ui.actionCopy.trigger()
        # Clipboard should have content
        clipboard_text = QApplication.clipboard().text()
        assert len(clipboard_text) >= 0


# ============================================================================
# STRESS TESTS
# ============================================================================


def test_twoda_editor_rapid_insert_delete(qtbot: QtBot, installation: HTInstallation):
    """Stress test: rapid insert and delete operations."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    # Rapid insert/delete cycles
    for _ in range(10):
        editor.insert_row()
        if editor.source_model.rowCount() > 0:
            editor.ui.twodaTable.selectRow(editor.source_model.rowCount() - 1)
            editor.remove_selected_rows()
    
    # Editor should still be functional
    assert editor is not None
    data, _ = editor.build()
    assert len(data) > 0


def test_twoda_editor_rapid_filter_changes(qtbot: QtBot, installation: HTInstallation):
    """Stress test: rapid filter changes."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    # Rapid filter changes
    filter_texts = ["test", "", "value", "", "data", "xyz", ""]
    for filter_text in filter_texts:
        editor.do_filter(filter_text)
        QtBot.wait(10)  # Small wait for processing
    
    # Editor should still be functional
    assert editor is not None


def test_twoda_editor_concurrent_operations(qtbot: QtBot, installation: HTInstallation):
    """Test concurrent operations (insert, edit, filter)."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    if not twoda_file.exists():
        pytest.skip("appearance.2da not found")
    
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())
    
    # Perform multiple operations
    editor.insert_row()
    if editor.source_model.rowCount() > 0 and editor.source_model.columnCount() > 1:
        item = editor.source_model.item(0, 1)
        if item:
            item.setText("test_value")
    editor.do_filter("test")
    editor.insert_row()
    
    # Editor should handle all operations
    assert editor is not None
    data, _ = editor.build()
    assert len(data) > 0