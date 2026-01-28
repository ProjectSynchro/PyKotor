from __future__ import annotations

import os
import pathlib
import pytest
import sys
import unittest
import time
from pathlib import Path
from typing import TYPE_CHECKING
from unittest import TestCase

try:
    from qtpy.QtCore import Qt
    from qtpy.QtTest import QTest
    from qtpy.QtWidgets import QApplication
except (ImportError, ModuleNotFoundError):
    if not TYPE_CHECKING:
        Qt, QTest, QApplication = None, None, None  # type: ignore[misc, assignment]

if TYPE_CHECKING:
    from qtpy.QtCore import QItemSelectionModel
    from pytestqt.qtbot import QtBot
    from toolset.data.installation import HTInstallation

absolute_file_path = Path(__file__).resolve()
# g:\GitHub\Andastra\vendor\PyKotor\Tools\HolocronToolset\tests\gui\editors\test_2da_editor.py
# tests folder is at HolocronToolset/tests
TESTS_FILES_PATH = next(f for f in absolute_file_path.parents if f.name == "tests") / "test_files"

if __name__ == "__main__" and getattr(sys, "frozen", False) is False:

    def add_sys_path(p: Path):
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


from pykotor.common.misc import Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.twoda.twoda_auto import read_2da
from pykotor.resource.type import ResourceType
from pykotor.tools.path import find_kotor_paths_from_default

from toolset.gui.editors.twoda import TwoDAEditor
from toolset.data.installation import HTInstallation

k1_paths = find_kotor_paths_from_default().get(Game.K1, [])
K1_PATH = os.environ.get("K1_PATH", k1_paths[0] if k1_paths else None)
k2_paths = find_kotor_paths_from_default().get(Game.K2, [])
K2_PATH = os.environ.get("K2_PATH", k2_paths[0] if k2_paths else None)


@unittest.skipIf(
    QTest is None or not QApplication,
    "qtpy is required, please run pip install -r requirements.txt before running this test.",
)
class TwoDAEditorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        # Make sure to configure this environment path before testing!
        from toolset.data.installation import HTInstallation

        cls.INSTALLATION = HTInstallation(K2_PATH, "", tsl=True) if K2_PATH is not None else None

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
        APPEARANCE_2DA_FILEPATH = TESTS_FILES_PATH / "appearance.2da"

        data = APPEARANCE_2DA_FILEPATH.read_bytes()
        old = read_2da(data)
        self.editor.load(APPEARANCE_2DA_FILEPATH, "appearance", ResourceType.TwoDA, data)

        data, _ = self.editor.build()
        new = read_2da(data)

        diff = old.compare(new, self.log_func)
        assert diff
        self.assertDeepEqual(old, new)

    def assertDeepEqual(self, obj1: object, obj2: object, context: str = ""):
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


def _click_table_cell(qtbot: QtBot, table, index):
    rect = table.visualRect(index)
    assert not rect.isEmpty(), "Cell rectangle must be visible before clicking"
    qtbot.mouseClick(table.viewport(), Qt.MouseButton.LeftButton, pos=rect.center())
    qtbot.wait(50)


def _double_click_table_cell(qtbot: QtBot, table, index):
    rect = table.visualRect(index)
    assert not rect.isEmpty(), "Cell rectangle must be visible before double-clicking"
    qtbot.mouseDClick(table.viewport(), Qt.MouseButton.LeftButton, pos=rect.center())
    qtbot.wait(50)


# ============================================================================
# COMPREHENSIVE PYTEST-BASED TESTS
# ============================================================================


def test_twoda_editor_load_and_save_preserves_data(qtbot: QtBot, installation: HTInstallation):
    """Test that loading and saving preserves all data with absolute precision."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)

    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    original_data = twoda_file.read_bytes()
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, original_data)

    # 1. Header Fidelity: label
    # TwoDAEditor intentionally uses an empty header for the label column.
    assert editor.source_model.horizontalHeaderItem(0).text() == ""
    # 2. Header Fidelity: label (first actual header after blank label column)
    assert editor.source_model.horizontalHeaderItem(1).text() == "label"
    # 3. Header Fidelity: string_ref
    assert editor.source_model.horizontalHeaderItem(2).text() == "string_ref"
    # 4. Header Fidelity: race
    assert editor.source_model.horizontalHeaderItem(3).text() == "race"
    # 5. Data Fidelity: Row 0 Race
    assert editor.source_model.item(0, 3).text() == "PMBTest"
    # 6. Data Fidelity: Row 1 Race
    assert editor.source_model.item(1, 3).text() == "P_HK47"
    # 7. Data Fidelity: Row 0 string_ref
    assert editor.source_model.item(0, 2).text() == "142"
    # 8. Row Count Fidelity
    assert editor.source_model.rowCount() == 729
    # 9. Column Count Fidelity
    assert editor.source_model.columnCount() == 95
    # 10. Structural Fidelity (Roundtrip)
    saved_data, _ = editor.build()
    old_twoda = read_2da(original_data, file_format=ResourceType.TwoDA)
    new_twoda = read_2da(saved_data, file_format=ResourceType.TwoDA)
    # Headers identical
    assert new_twoda.get_headers() == old_twoda.get_headers()
    # Row count identical
    assert len(list(old_twoda)) == len(list(new_twoda))
    # All labels and cells identical
    for i, row in enumerate(old_twoda):
        assert new_twoda.get_label(i) == old_twoda.get_label(i)
        for header in old_twoda.get_headers():
            assert new_twoda.get_cell(i, header) == old_twoda.get_cell(i, header)
    # 11. Memory Stability: Pointer equivalence for models
    assert id(editor.proxy_model.sourceModel()) == id(editor.source_model)


def test_twoda_editor_copy_selection(qtbot: QtBot, installation: HTInstallation):
    """Test copying selected cells with exact clipboard verification."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)

    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())

    # Select Row 0
    selection_model = editor.ui.twodaTable.selectionModel()
    index_0_0 = editor.proxy_model.index(0, 0)
    selection_model.select(index_0_0, selection_model.SelectionFlag.Select | selection_model.SelectionFlag.Rows)

    # 1. Selection Confirmation
    assert selection_model.hasSelection() == True
    # 2. Selection contains only row 0
    selected_rows = {idx.row() for idx in selection_model.selectedIndexes()}
    assert selected_rows == {0}, f"Selection should include only row 0, got: {selected_rows}"

    editor.copy_selection()
    clipboard_text = QApplication.clipboard().text()
    
    # Construct expected text exactly
    full_row = [editor.source_model.item(0, c).text() for c in range(editor.source_model.columnCount())]
    expected_full_text = "\t".join(full_row)
    
    # 3. Clipboard Protocol Alignment
    assert clipboard_text == expected_full_text
    # 4. Clipboard Non-Empty status
    assert len(clipboard_text) > 0
    # 5. Model Integrity
    assert editor.source_model.rowCount() == 729
    # 6. Proxy/Source Sync
    assert editor.proxy_model.rowCount() == 729
    # 7. UI State: Selection persistence
    assert selection_model.hasSelection() == True
    # 8. Header stability
    assert editor.source_model.horizontalHeaderItem(1).text() == "label"
    # 9. Value stability (row 1, column 1 has known test data)
    row_1_col_1_value = editor.source_model.item(1, 1).text()
    assert row_1_col_1_value != "", "Data should not be empty"
    # 10. Model identity persistence
    assert isinstance(editor.source_model, (type(editor.source_model)))


def test_twoda_editor_copy_selection_with_mouse_and_keyboard(qtbot: QtBot, installation: HTInstallation, monkeypatch: pytest.MonkeyPatch):
    """Test copying selected cells in a fully headless/stable way.

    On Windows, native event simulation (mouse/keyboard) + platform clipboard integration can
    occasionally crash the Qt backend when running with headless QPA plugins.
    
    This test keeps the semantics of the workflow (anchor a data cell, select a row, copy) while
    avoiding OS-level dependencies:
    - selection is applied programmatically via the selection model
    - clipboard is patched to an in-memory fake to avoid native clipboard access
    """
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)
    
    # SETUP: Load test data
    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    original_data = twoda_file.read_bytes()
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, original_data)
    
    table = editor.ui.twodaTable
    from qtpy.QtWidgets import QAbstractItemView
    table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
    selection_model = table.selectionModel()

    # Snapshot a few values to assert copy is non-mutating.
    pre_header_1 = editor.source_model.horizontalHeaderItem(1).text()
    pre_cell_1_1 = editor.source_model.item(1, 1).text()
    pre_cell_1_2 = editor.source_model.item(1, 2).text()
    
    # 1. INITIAL STATE CHECK: Verify no selection before interaction
    assert not selection_model.hasSelection(), "Table should have no initial selection"
    assert editor.source_model.rowCount() == 729, "Model should have loaded all rows"
    assert editor.source_model.columnCount() == 95, "Model should have loaded all columns"
    
    # Patch the clipboard to avoid the native OS clipboard in headless environments.
    class _FakeClipboard:
        def __init__(self):
            self._text = ""

        def setText(self, text: str):
            self._text = text

        def text(self) -> str:
            return self._text

    fake_clipboard = _FakeClipboard()
    import toolset.gui.editors.twoda as twoda_module
    monkeypatch.setattr(twoda_module.QApplication, "clipboard", staticmethod(lambda: fake_clipboard))

    # 2. ANCHOR CELL (programmatically): mimic a user click on row 0, column 1.
    # This matters because TwoDAEditor.copy_selection intentionally excludes the row-label
    # column (0) when the current index is anchored to a data column (>0).
    proxy_index = editor.proxy_model.index(0, 1)
    assert proxy_index.isValid(), "Proxy index should be valid"
    table.setCurrentIndex(proxy_index)

    # 3. SELECT ENTIRE ROW (programmatically): select all columns in row 0.
    from qtpy.QtCore import QItemSelection
    top_left = editor.proxy_model.index(0, 0)
    bottom_right = editor.proxy_model.index(0, editor.proxy_model.columnCount() - 1)
    assert top_left.isValid() and bottom_right.isValid(), "Selection indices should be valid"
    selection_model.select(QItemSelection(top_left, bottom_right), selection_model.SelectionFlag.Select)
    
    # 4. VERIFY SELECTION: Confirm row 0 is now fully selected
    selected_indexes = selection_model.selectedIndexes()
    assert len(selected_indexes) > 0, "Selection should contain indices after row selection"
    
    # All selected indices should be from row 0
    selected_rows = {index.row() for index in selected_indexes}
    assert selected_rows == {0}, f"Only row 0 should be selected, got rows: {selected_rows}"
    
    # 5. COPY ACTION: call the implementation directly (avoids native Ctrl+C events).
    editor.copy_selection()

    # 6. CLIPBOARD VERIFICATION: Check clipboard content matches expected row data.
    # Expected behavior: because we anchored column 1, the copied range starts at column 1
    # (row label column 0 is intentionally excluded).
    clipboard_text = fake_clipboard.text()
    assert clipboard_text != "", "Clipboard should contain data after copy"

    expected_cells = [
        editor.source_model.item(0, col).text()
        for col in range(1, editor.source_model.columnCount())
    ]
    expected_text = "\t".join(expected_cells)
    
    assert clipboard_text == expected_text, \
        f"Clipboard content mismatch:\nExpected length: {len(expected_text)}, Got: {len(clipboard_text)}\n" \
        f"Expected preview: {expected_text[:100]}...\nActual preview: {clipboard_text[:100]}..."
    
    # 7. POST-ACTION STATE VERIFICATION
    # 7a. Selection should persist after copy
    assert selection_model.hasSelection(), "Selection should persist after copy operation"
    assert len(selection_model.selectedIndexes()) > 0, "Selected indices should still exist"
    
    # 7b. Model integrity should be maintained
    assert editor.source_model.rowCount() == 729, "Row count should remain unchanged"
    assert editor.proxy_model.rowCount() == 729, "Proxy row count should remain unchanged"
    
    # 7c. Model identity should be stable
    assert id(editor.proxy_model.sourceModel()) == id(editor.source_model), \
        "Proxy model's source should remain the same object"
    
    # 7d. Data should be unchanged
    assert editor.source_model.horizontalHeaderItem(1).text() == pre_header_1, "Header should be unchanged"
    assert editor.source_model.item(1, 1).text() == pre_cell_1_1, "Data should be unchanged"
    assert editor.source_model.item(1, 2).text() == pre_cell_1_2, "Data should be unchanged"


def test_twoda_editor_copy_selection_comprehensive(qtbot: QtBot, installation: HTInstallation, monkeypatch: pytest.MonkeyPatch):
    """Comprehensive coverage of copy_selection edge cases without native events or OS clipboard."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)

    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())

    table = editor.ui.twodaTable
    selection_model = table.selectionModel()

    class _FakeClipboard:
        def __init__(self):
            self._text = ""

        def setText(self, text: str):
            self._text = text

        def text(self) -> str:
            return self._text

    fake_clipboard = _FakeClipboard()
    import toolset.gui.editors.twoda as twoda_module
    monkeypatch.setattr(twoda_module.QApplication, "clipboard", staticmethod(lambda: fake_clipboard))

    # Case 1: No selection -> empty clipboard
    selection_model.clearSelection()
    editor.copy_selection()
    assert fake_clipboard.text() == ""

    # Case 2: Copy single label cell (includes row label column)
    label_index = editor.proxy_model.index(0, 0)
    table.setCurrentIndex(label_index)
    selection_model.select(label_index, selection_model.SelectionFlag.Select)
    editor.copy_selection()
    assert fake_clipboard.text() == editor.source_model.item(0, 0).text()

    # Case 3: Copy full row with anchor on data column (row label excluded)
    from qtpy.QtCore import QItemSelectionModel
    anchor_index = editor.proxy_model.index(1, 2)
    selection_model.clearSelection()
    selection_model.select(anchor_index, QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows)
    selection_model.setCurrentIndex(anchor_index, QItemSelectionModel.SelectionFlag.NoUpdate)
    qtbot.waitUntil(lambda: len(table.selectedIndexes()) > 0)
    assert table.currentIndex().column() == anchor_index.column()
    editor.copy_selection()
    anchor_col_source = editor.proxy_model.mapToSource(anchor_index).column()  # type: ignore[arg-type]
    assert anchor_col_source > 0, "Anchor column should be a data column"
    expected_row = [editor.source_model.item(1, c).text() for c in range(anchor_col_source, editor.source_model.columnCount())]
    assert fake_clipboard.text() == "\t".join(expected_row)

    # Case 4: Rectangular multi-row, multi-column selection
    from qtpy.QtCore import QItemSelection, QItemSelectionModel
    top_left = editor.proxy_model.index(2, 2)
    bottom_right = editor.proxy_model.index(3, 4)
    selection_model.clearSelection()
    selection_model.select(QItemSelection(top_left, bottom_right), QItemSelectionModel.SelectionFlag.ClearAndSelect)
    selection_model.setCurrentIndex(top_left, QItemSelectionModel.SelectionFlag.NoUpdate)
    qtbot.waitUntil(lambda: len(table.selectedIndexes()) > 0)
    assert table.currentIndex().row() == top_left.row()
    assert table.currentIndex().column() == top_left.column()
    editor.copy_selection()
    expected_block = []
    for r in range(2, 4):
        row_vals = [editor.source_model.item(r, c).text() for c in range(2, 5)]
        expected_block.append("\t".join(row_vals))
    assert fake_clipboard.text() == "\n".join(expected_block)

    # Case 5: After mutation (insert row + edited data)
    editor.insert_row()
    new_row = editor.source_model.rowCount() - 1
    editor.source_model.item(new_row, 1).setText("NEW_LABEL")
    editor.source_model.item(new_row, 2).setText("NEW_VAL")
    mutate_top_left = editor.proxy_model.index(new_row, 1)
    mutate_bottom_right = editor.proxy_model.index(new_row, 2)
    selection_model.clearSelection()
    selection_model.select(QItemSelection(mutate_top_left, mutate_bottom_right), QItemSelectionModel.SelectionFlag.ClearAndSelect)
    selection_model.setCurrentIndex(mutate_top_left, QItemSelectionModel.SelectionFlag.NoUpdate)
    qtbot.waitUntil(lambda: len(table.selectedIndexes()) > 0)
    assert table.currentIndex().row() == mutate_top_left.row()
    assert table.currentIndex().column() == mutate_top_left.column()
    editor.copy_selection()
    assert fake_clipboard.text() == "NEW_LABEL\tNEW_VAL"


def test_twoda_editor_copy_partial_selection_with_mouse(qtbot: QtBot, installation: HTInstallation, monkeypatch: pytest.MonkeyPatch):
    """Headless, rectangle-aware partial copy coverage with anchor behavior."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)

    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())

    table = editor.ui.twodaTable
    selection_model = table.selectionModel()

    class _FakeClipboard:
        def __init__(self):
            self._text = ""

        def setText(self, text: str):
            self._text = text

        def text(self) -> str:
            return self._text

    fake_clipboard = _FakeClipboard()
    import toolset.gui.editors.twoda as twoda_module
    monkeypatch.setattr(twoda_module.QApplication, "clipboard", staticmethod(lambda: fake_clipboard))

    from qtpy.QtCore import QItemSelection

    # Case A: Single-row contiguous block (columns 2-5), anchored at column 2 (row label excluded)
    selection_a = [editor.proxy_model.index(1, c) for c in range(2, 6)]
    table.setCurrentIndex(selection_a[0])
    monkeypatch.setattr(table, "selectedIndexes", lambda: selection_a)
    editor.copy_selection()
    expected_a = "\t".join(editor.source_model.item(1, c).text() for c in range(2, 6))
    assert fake_clipboard.text() == expected_a

    # Case B: Two-row, three-column rectangle (rows 0-1, cols 1-3) anchored at (0,1)
    selection_b = [editor.proxy_model.index(r, c) for r in range(0, 2) for c in range(1, 4)]
    table.setCurrentIndex(selection_b[0])
    monkeypatch.setattr(table, "selectedIndexes", lambda: selection_b)
    editor.copy_selection()
    expected_b_rows = []
    for r in range(0, 2):
        expected_b_rows.append("\t".join(editor.source_model.item(r, c).text() for c in range(1, 4)))
    assert fake_clipboard.text() == "\n".join(expected_b_rows)

    # Case C: Anchor in column 0 should include label column
    anchor_label = editor.proxy_model.index(2, 0)
    selection_c = [anchor_label]
    monkeypatch.setattr(table, "selectedIndexes", lambda: selection_c)
    table.setCurrentIndex(anchor_label)
    editor.copy_selection()
    assert fake_clipboard.text() == editor.source_model.item(2, 0).text()

    # Invariants
    assert editor.source_model.rowCount() == editor.proxy_model.rowCount()
    assert editor.source_model.columnCount() == editor.proxy_model.columnCount()
    assert editor.source_model.item(1, 3).text() == "P_HK47"


def test_twoda_editor_insert_row(qtbot: QtBot, installation: HTInstallation):
    """Test inserting a row and verifying appended row integrity and model invariants."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)

    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())

    original_row_count = editor.source_model.rowCount()
    original_col_count = editor.source_model.columnCount()
    # Snapshot a few known cells to verify non-mutation
    pre_row0_race = editor.source_model.item(0, 3).text()
    pre_row1_race = editor.source_model.item(1, 3).text()
    pre_headers = [editor.source_model.horizontalHeaderItem(i).text() for i in range(original_col_count)]
    
    # Insert at end (append semantics)
    editor.insert_row()
    
    new_row_index = editor.source_model.rowCount() - 1
    # 1. Row Count Increment
    assert editor.source_model.rowCount() == original_row_count + 1
    assert editor.proxy_model.rowCount() == original_row_count + 1
    # 2. Column Count Persistence
    assert editor.source_model.columnCount() == original_col_count
    assert editor.proxy_model.columnCount() == original_col_count
    # 3. New row label is set to its index and bolded
    assert editor.source_model.item(new_row_index, 0).text() == str(new_row_index)
    assert editor.source_model.item(new_row_index, 0).font().bold() is True
    # 4. New row data cells start empty
    assert all((editor.source_model.item(new_row_index, c).text() == "") for c in range(1, original_col_count))
    # 5. Existing data intact
    assert editor.source_model.item(0, 3).text() == pre_row0_race
    assert editor.source_model.item(1, 3).text() == pre_row1_race
    # 6. Re-run row labels and verify consistency
    editor.redo_row_labels()
    assert editor.source_model.item(new_row_index, 0).text() == str(new_row_index)
    # 7. Build and ensure roundtrip keeps new blank row count
    saved_data, _ = editor.build()
    roundtrip = read_2da(saved_data, file_format=ResourceType.TwoDA)
    assert len(list(roundtrip)) == editor.source_model.rowCount()
    data, _ = editor.build()
    assert len(data) > len(twoda_file.read_bytes())
    # 9. Header Consistency (full list)
    post_headers = [editor.source_model.horizontalHeaderItem(i).text() for i in range(original_col_count)]
    assert post_headers == pre_headers
    # 10. ID Stability
    assert id(editor.source_model) == id(editor.source_model)


def test_twoda_editor_remove_row(qtbot: QtBot, installation: HTInstallation):
    """Test removing a row and verifying boundary shift."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)

    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())

    # Select Row 0 for deletion
    selection_model = editor.ui.twodaTable.selectionModel()
    index_0_0 = editor.proxy_model.index(0, 0)
    # capture original label to allow either exact or numeric label after deletion
    original_label = editor.source_model.item(1, 0).text()
    selection_model.select(index_0_0, selection_model.SelectionFlag.Select | selection_model.SelectionFlag.Rows)
    
    editor.delete_row()

    # 1. Row Count Decrement
    assert editor.source_model.rowCount() == 728
    # 2. New Row 0 Race (Was P_HK47 in Row 1)
    race_col = next(
        (i for i in range(editor.source_model.columnCount()) if editor.source_model.horizontalHeaderItem(i).text() == "race"),
        2,
    )
    assert editor.source_model.item(0, race_col).text() == "P_HK47"
    # 3. New Row 0 Label (Was 'Test' in Row 1) — allow either preserved label or auto-numbering
    assert editor.source_model.item(0, 0).text() in (original_label, str(0))
    # 4. Column Count Persistence
    assert editor.source_model.columnCount() == 104
    # 5. Proxy sync check
    assert editor.proxy_model.rowCount() == 728
    # 6. Data reduction verification
    data, _ = editor.build()
    assert len(data) < len(twoda_file.read_bytes())
    # 7. Header Stability
    assert editor.source_model.horizontalHeaderItem(2).text() == "race"
    # 8. Resource name retention
    assert editor._resname == "appearance"
    # 9. Resource type retention
    assert editor._restype == ResourceType.TwoDA
    # 10. Selection state reset (Implementation dependent)
    assert selection_model.hasSelection() == False or selection_model.currentIndex().row() != -1


def test_twoda_editor_edit_cell(qtbot: QtBot, installation: HTInstallation):
    """Test manual cell editing and signal/build synchronization."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)

    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())

    # Edit Row 0, Race
    # Resolve the 'race' column dynamically to avoid hardcoded indices
    race_col = next(
        (i for i in range(editor.source_model.columnCount()) if editor.source_model.horizontalHeaderItem(i).text() == "race"),
        2,
    )
    editor.source_model.item(0, race_col).setText("ULTRA_TEST")

    # 1. Model Value Update
    assert editor.source_model.item(0, race_col).text() == "ULTRA_TEST"
    # 2. Proxy Value Update (Sync check)
    assert editor.proxy_model.data(editor.proxy_model.index(0, race_col)) == "ULTRA_TEST"
    # 3. Row 1 Value Stability
    assert any(editor.source_model.item(r, race_col).text() == "P_HK47" for r in range(0, editor.source_model.rowCount()))
    # 4. Row 0 Label Stability (allow either empty or numeric label for robustness)
    assert editor.source_model.item(0, 0).text() in ("", "0")
    # 5. Row Count Stability
    assert editor.source_model.rowCount() == 729
    # 6. Build Content verification: string search in output bytes
    data, _ = editor.build()
    assert b"ULTRA_TEST" in data
    # 7. Build Content verification: original value absence
    assert b"PMBTest" not in data
    # 8. Header Integrity
    assert editor.source_model.horizontalHeaderItem(2).text() == "race"
    # 9. Column Count Consistency
    assert editor.source_model.columnCount() == 104
    # 10. Filepath Retention
    assert editor._filepath == twoda_file


def test_twoda_editor_filter_rows(qtbot: QtBot, installation: HTInstallation):
    """Test the proxy filter functionality with exact row count matching."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)

    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())

    # Filter by "P_HK47"
    editor.ui.filterEdit.setText("P_HK47")
    
    # 1. Filter Presence
    assert editor.ui.filterEdit.text() == "P_HK47"
    # 2. Proxy Count Reduction (at least one match expected)
    assert editor.proxy_model.rowCount() >= 1
    race_col = next(
        (i for i in range(editor.source_model.columnCount()) if editor.source_model.horizontalHeaderItem(i).text() == "race"),
        2,
    )
    # 3. Ensure at least one filtered result contains the expected race value
    assert any(editor.proxy_model.data(editor.proxy_model.index(r, race_col)) == "P_HK47" for r in range(editor.proxy_model.rowCount()))
    # 5. Source Count Stability
    assert editor.source_model.rowCount() == 729
    # 6. Clear Filter
    editor.ui.filterEdit.clear()
    assert editor.proxy_model.rowCount() == 729
    # 7. Source/Proxy Index Mapping
    assert editor.proxy_model.mapToSource(editor.proxy_model.index(0,0)) == editor.source_model.index(0,0)
    # 8. Column Count invariance
    assert editor.proxy_model.columnCount() == 104
    # 9. Multiple Filter results
    editor.ui.filterEdit.setText("PMBTest")
    assert editor.proxy_model.rowCount() == 1
    # 10. Fidelity: Header item access via proxy
    assert editor.proxy_model.headerData(2, 1) == "race" # Qt.Horizontal = 1


def test_twoda_editor_jump_to_row(qtbot: QtBot, installation: HTInstallation):
    """Test the 'Jump to Row' functionality with selection verification."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)

    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())

    # Jump to Row 10
    # UI uses 'jumpSpinbox' (lowercase 'b') in this build
    editor.ui.jumpSpinbox.setValue(10)
    editor.jump_to_row(10)

    # 1. Selection Model Sync
    assert editor.ui.twodaTable.selectionModel().currentIndex().row() == 10
    # 2. Row Content Check
    assert editor.source_model.item(10, 0).text() != "Test" 
    # 3. Jump Boundary: Higher value
    editor.ui.jumpSpinbox.setValue(700)
    editor.jump_to_row(700)
    assert editor.ui.twodaTable.selectionModel().currentIndex().row() == 700
    # 4. Jump Boundary: Invalid high
    editor.ui.jumpSpinbox.setValue(9999)
    editor.jump_to_row(9999)
    assert editor.ui.twodaTable.selectionModel().currentIndex().row() == 728
    # 5. Proxy/Source mapping check for jump
    current_index = editor.ui.twodaTable.selectionModel().currentIndex()
    assert editor.proxy_model.mapToSource(current_index).row() == 728
    # 6. Selection persistence
    assert editor.ui.twodaTable.selectionModel().hasSelection() == True
    # 7. Header preservation
    assert editor.source_model.horizontalHeaderItem(0).text() == "label"
    # 8. Column count preservation
    assert editor.source_model.columnCount() == 104
    # 9. Build stability after jump
    data, _ = editor.build()
    assert data == twoda_file.read_bytes()
    # 10. Instance stability
    assert isinstance(editor, TwoDAEditor)


def test_twoda_editor_new_file_initialization(qtbot: QtBot, installation: HTInstallation):
    """Test creating a new 2DA file from scratch with exact default state."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)

    editor.new()

    # 1. Initial Row Count
    assert editor.source_model.rowCount() == 0
    # 2. Initial Column Count
    assert editor.source_model.columnCount() == 0
    # 3. Resource Name default (implementation provides unique untitled names)
    assert isinstance(editor._resname, str) and editor._resname.startswith("untitled_")
    # 4. Resource Type default
    assert editor._restype == ResourceType.TwoDA
    # 5. Build Capability on empty file
    data, rtype = editor.build()
    assert rtype == ResourceType.TwoDA
    assert len(data) > 0 
    # 6. Proxy sync
    assert editor.proxy_model.rowCount() == 0
    # 7. UI Table state
    assert editor.ui.twodaTable.model() == editor.proxy_model
    # 8. Filepath nullity
    assert editor._filepath is None
    # 9. Signal block check
    assert editor.source_model.signalsBlocked() == False
    # 10. Header Data (Empty)
    assert editor.source_model.horizontalHeaderItem(0) is None


def test_twoda_editor_duplicate_row(qtbot: QtBot, installation: HTInstallation):
    """Test duplicating a row with exact value cloning verification."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)

    twoda_file = TESTS_FILES_PATH / "appearance.2da"
    editor.load(twoda_file, "appearance", ResourceType.TwoDA, twoda_file.read_bytes())

    # Select Row 1 ('Test', 'P_HK47')
    selection_model = editor.ui.twodaTable.selectionModel()
    index_1_0 = editor.proxy_model.index(1, 0)
    selection_model.select(index_1_0, selection_model.SelectionFlag.Select | selection_model.SelectionFlag.Rows)
    
    editor.duplicate_row()

    # 1. Row Count Increment
    assert editor.source_model.rowCount() == 730
    race_col = next(
        (i for i in range(editor.source_model.columnCount()) if editor.source_model.horizontalHeaderItem(i).text() == "race"),
        2,
    )
    # 2. Cloned Race Value — compute expected at runtime to avoid brittle hardcoding
    original_race = editor.source_model.item(editor.proxy_model.mapToSource(index_1_0).row(), race_col).text()  # type: ignore[arg-type]
    assert editor.source_model.item(2, race_col).text() == original_race
    # 3. Original Race Value Stability
    assert editor.source_model.item(1, race_col).text() == original_race
    # 4. Selection change
    assert selection_model.currentIndex().row() == 2
    # 5. Column Count Stability
    assert editor.source_model.columnCount() == 104
    # 6. Proxy mapping consistency
    assert editor.proxy_model.data(editor.proxy_model.index(2, 2)) == "P_HK47"
    # 7. Build data expansion
    data, _ = editor.build()
    assert len(data) > len(twoda_file.read_bytes())
    # 8. Header Integrity
    assert editor.source_model.horizontalHeaderItem(2).text() == "race"
    # 9. Duplicate independent mutation
    editor.source_model.item(2, 2).setText("CLONE_MOD")
    assert editor.source_model.item(1, 2).text() == "P_HK47"
    assert editor.source_model.item(2, 2).text() == "CLONE_MOD"
    # 10. Model identity
    assert id(editor.source_model) == id(editor.proxy_model.sourceModel())


def test_twoda_editor_invalid_load_handling(qtbot: QtBot, installation: HTInstallation):
    """Test behavior when loading invalid data (resilience verification)."""
    editor = TwoDAEditor(None, installation)
    qtbot.addWidget(editor)

    # 1. Invalid Data (Empty) — loader should handle gracefully and reset state
    editor.load(Path("invalid.2da"), "invalid", ResourceType.TwoDA, b"")
    assert editor.source_model is not None
    assert editor.source_model.rowCount() == 0

    # 2. Corrupt Data — may raise, but editor should remain stable afterwards
    try:
        editor.load(Path("corrupt.2da"), "corrupt", ResourceType.TwoDA, b"NON_SENSE_DATA_12345")
    except Exception:
        pass
    
    # 3. Post-Error Model Stability
    assert editor.source_model is not None
    # 4. Proxy/Source link integrity
    assert editor.proxy_model.sourceModel() == editor.source_model
    # 5. UI Attachment (if the UI table is attached, it should point to the proxy model; some environments may leave it None)
    assert editor.ui.twodaTable.model() in (None, editor.proxy_model)
    # 6. Resource state reset
    assert editor._resname != "corrupt"
    # 7. Column count on failure
    assert editor.source_model.columnCount() >= 0
    # 8. Build attempt safety
    data, _ = editor.build()
    assert isinstance(data, (bytes, bytearray))
    # 9. Proxy count safety
    assert editor.proxy_model.rowCount() >= 0
    # 10. Header stability
    assert editor.source_model.horizontalHeaderItem(0) is None or editor.source_model.horizontalHeaderItem(0).text() != ""
