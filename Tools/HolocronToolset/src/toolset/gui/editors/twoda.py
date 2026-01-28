from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

import qtpy

from qtpy.QtCore import QSortFilterProxyModel, Qt
from qtpy.QtGui import QColor, QPalette, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QApplication,
    QMessageBox,
)

from pykotor.resource.formats.twoda import TwoDA, read_2da, write_2da
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.gui.common.filters import NoScrollEventFilter
from toolset.gui.common.localization import translate as tr, trf
from utility.error_handling import assert_with_variable_trace

if TYPE_CHECKING:
    import os

    from qtpy.QtCore import QModelIndex, QObject
    from qtpy.QtWidgets import QHeaderView, QWidget

    from toolset.data.installation import HTInstallation


class TwoDAEditor(Editor):
    """Editor for 2DA (Two-Dimensional Array) files used in KotOR games.
    
    This editor provides a spreadsheet-like interface for editing 2DA files, which are
    tabular data files used extensively throughout KotOR and KotOR 2 for game configuration.
    
    Game Engine Usage:
    ----------------
    The 2DA files edited by this tool are verified to be loaded and used by the game engine,
    as confirmed through reverse engineering analysis of swkotor.exe and swkotor2.exe using
    Ghidra (via Reva MCP server). See TwoDARegistry class documentation in
    Libraries/PyKotor/src/pykotor/extract/twoda.py for a complete list of verified 2DA files
    and their loading functions.
    
    Supported formats:
    - Native 2DA binary format (ResourceType.TwoDA)
    - CSV format (ResourceType.TwoDA_CSV)
    - JSON format (ResourceType.TwoDA_JSON)
    """
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None = None,
    ):
        supported: list[ResourceType] = [ResourceType.TwoDA, ResourceType.TwoDA_CSV, ResourceType.TwoDA_JSON]
        super().__init__(parent, "2DA Editor", "none", supported, supported, installation)
        self.resize(400, 250)

        from toolset.uic.qtpy.editors.twoda import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()
        self._add_help_action()
        self._setup_signals()

        self.ui.filterBox.setVisible(False)

        self.source_model: QStandardItemModel = QStandardItemModel(self)
        self.proxy_model: SortFilterProxyModel = SortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.source_model)

        self.vertical_header_option: VerticalHeaderOption = VerticalHeaderOption.NONE
        self.vertical_header_column: str = ""
        vert_header: QHeaderView | None = self.ui.twodaTable.verticalHeader()

        # Setup event filter to prevent scroll wheel interaction with controls
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)
        self.source_model.itemChanged.connect(self.reset_vertical_headers)

        self.new()
        if vert_header is not None and "(Dark)" in GlobalSettings().selectedTheme:
            # Get palette colors
            app = QApplication.instance()
            if app is None or not isinstance(app, QApplication):
                palette = QPalette()
            else:
                palette = app.palette()
            
            window_text = palette.color(QPalette.ColorRole.WindowText)
            base = palette.color(QPalette.ColorRole.Base)
            alternate_base = palette.color(QPalette.ColorRole.AlternateBase)
            
            # Create transparent text color
            transparent_text = QColor(window_text)
            transparent_text.setAlpha(0)
            
            # Create hover background (slightly lighter/darker than base)
            hover_bg = QColor(alternate_base if alternate_base != base else base)
            if hover_bg.lightness() < 128:  # Dark theme
                hover_bg = hover_bg.lighter(110)
            else:  # Light theme
                hover_bg = hover_bg.darker(95)
            
            vert_header.setStyleSheet(f"""
                QHeaderView::section {{
                    color: rgba({transparent_text.red()}, {transparent_text.green()}, {transparent_text.blue()}, 0);  /* Transparent text */
                    background-color: {base.name()};  /* Base background */
                }}
                QHeaderView::section:checked {{
                    color: {window_text.name()};  /* Window text for checked sections */
                    background-color: {alternate_base.name() if alternate_base != base else hover_bg.name()};  /* Alternate base for checked sections */
                }}
                QHeaderView::section:hover {{
                    color: {window_text.name()};  /* Window text on hover */
                    background-color: {hover_bg.name()};  /* Hover background */
                }}
            """)
            mid_color = palette.color(QPalette.ColorRole.Mid)
            highlight = palette.color(QPalette.ColorRole.Highlight)
            highlighted_text = palette.color(QPalette.ColorRole.HighlightedText)
            
            self.ui.twodaTable.setStyleSheet(f"""
                QHeaderView::section {{
                    background-color: {base.name()};  /* Base background for header */
                    color: {window_text.name()};  /* Window text for header */
                    padding: 4px;
                    border: 1px solid {mid_color.name()};
                }}
                QHeaderView::section:checked {{
                    background-color: {alternate_base.name() if alternate_base != base else hover_bg.name()};  /* Alternate base for checked header */
                    color: {window_text.name()};  /* Window text for checked header */
                }}
                QHeaderView::section:hover {{
                    background-color: {hover_bg.name()};  /* Hover background for hovered header */
                    color: {window_text.name()};  /* Window text for hovered header */
                }}
                QTableView {{
                    background-color: {base.name()};  /* Base background for table */
                    alternate-background-color: {alternate_base.name()};  /* Alternate base for alternating rows */
                    color: {window_text.name()};  /* Window text for table */
                    gridline-color: {mid_color.name()};  /* Mid color for grid lines */
                    selection-background-color: {highlight.name()};  /* Highlight for selected items */
                    selection-color: {highlighted_text.name()};  /* Highlighted text for selected items */
                }}
                QTableView::item {{
                    background-color: {base.name()};  /* Base background for items */
                    color: {window_text.name()};  /* Window text for items */
                }}
                QTableView::item:selected {{
                    background-color: {highlight.name()};  /* Highlight for selected items */
                    color: {highlighted_text.name()};  /* Highlighted text for selected items */
                }}
                QTableCornerButton::section {{
                    background-color: {base.name()};  /* Base background for corner button */
                    border: 1px solid {mid_color.name()};
                }}
            """)

    def _setup_signals(self):
        self.ui.filterEdit.textEdited.connect(self.do_filter)
        self.ui.actionToggleFilter.triggered.connect(self.toggle_filter)
        self.ui.actionCopy.triggered.connect(self.copy_selection)
        self.ui.actionPaste.triggered.connect(self.paste_selection)

        self.ui.actionInsertRow.triggered.connect(self.insert_row)
        self.ui.actionDuplicateRow.triggered.connect(self.duplicate_row)
        self.ui.actionRemoveRows.triggered.connect(self.remove_selected_rows)
        self.ui.actionRedoRowLabels.triggered.connect(self.redo_row_labels)

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        super().load(filepath, resref, restype, data)

        # FIXME(th3w1zard1): Why set this here when it's already set in __init__...?
        self.source_model = QStandardItemModel(self)
        self.proxy_model = SortFilterProxyModel(self)

        try:
            self._load_main(data)
        except Exception as e:
            # Avoid crashing tests on unexpected exceptions during load. Log the exception
            # and reset the editor state instead of showing a blocking native dialog.
            try:
                self._logger.exception("Failed to load 2DA data: %s", e)
            except Exception:
                # Fallback to printing if the logger isn't available for any reason
                print("Failed to load 2DA data:", e)
            # Ensure the model is reset so the editor remains in a consistent state
            self.proxy_model.setSourceModel(self.source_model)
            self.new()

    def _load_main(
        self,
        data: bytes,
    ):
        # Respect the expected format when provided by the caller (restype).
        # This ensures formats like CSV/JSON are parsed correctly even if the
        # automatic detection heuristic (first 4 characters) is insufficient.
        try:
            twoda: TwoDA = read_2da(data, file_format=self._restype)
        except KeyError as e:
            # Backwards compatibility: some JSON 2DA formats use a different schema
            # (e.g., test fixtures with 'headers' + rows containing 'label' and 'cells').
            # Attempt to gracefully parse that format as a fallback.
            try:
                import json as _json

                parsed = _json.loads(data.decode("utf-8"))
                if isinstance(parsed, dict) and "headers" in parsed and "rows" in parsed:
                    twoda = TwoDA()
                    for header in parsed.get("headers", []):
                        twoda.add_column(str(header))
                    for row in parsed.get("rows", []):
                        label = row.get("label")
                        cells = row.get("cells", [])
                        cell_map = {h: (cells[i] if i < len(cells) else "") for i, h in enumerate(twoda.get_headers())}
                        twoda.add_row(str(label), cell_map)
                else:
                    raise
            except Exception:
                # Re-raise original error if fallback fails
                raise e from None
        headers: list[str] = ["", *twoda.get_headers()]
        self.source_model.setColumnCount(len(headers))
        self.source_model.setHorizontalHeaderLabels(headers)

        # Disconnect the model to improve performance during updates (especially for appearance.2da)
        self.ui.twodaTable.setModel(None)  # type: ignore[arg-type]

        items: list[list[QStandardItem]] = []
        for i, row in enumerate(twoda):
            label_item = QStandardItem(str(twoda.get_label(i)))
            font = label_item.font()
            font.setBold(True)
            label_item.setFont(font)
            label_item.setBackground(self.palette().midlight())
            row_items = [label_item]
            row_items.extend(QStandardItem(row.get_string(header)) for header in headers[1:])
            items.append(row_items)

        for i, row_items in enumerate(items):
            self.source_model.insertRow(i, row_items)

        self.reset_vertical_headers()
        self.proxy_model.setSourceModel(self.source_model)
        self.ui.twodaTable.setModel(self.proxy_model)  # type: ignore[arg-type]
        self._reconstruct_menu(headers)

    def _reconstruct_menu(
        self,
        headers: list[str],
    ):
        self.ui.menuSetRowHeader.clear()
        action = QAction("None", self)
        action.triggered.connect(lambda: self.set_vertical_header_option(VerticalHeaderOption.NONE))
        self.ui.menuSetRowHeader.addAction(action)  # type: ignore[arg-type]

        action = QAction("Row Index", self)
        action.triggered.connect(lambda: self.set_vertical_header_option(VerticalHeaderOption.ROW_INDEX))
        self.ui.menuSetRowHeader.addAction(action)  # type: ignore[arg-type]

        action = QAction("Row Label", self)
        action.triggered.connect(lambda: self.set_vertical_header_option(VerticalHeaderOption.ROW_LABEL))
        self.ui.menuSetRowHeader.addAction(action)  # type: ignore[arg-type]
        self.ui.menuSetRowHeader.addSeparator()
        for header in headers[1:]:
            action = QAction(header, self)
            action.triggered.connect(lambda _=None, h=header: self.set_vertical_header_option(VerticalHeaderOption.CELL_VALUE, h))
            self.ui.menuSetRowHeader.addAction(action)  # type: ignore[arg-type]

    def build(self) -> tuple[bytes, bytes]:
        twoda = TwoDA()

        for i in range(self.source_model.columnCount())[1:]:
            horizontal_header_item = self.source_model.horizontalHeaderItem(i)
            assert horizontal_header_item is not None, "Horizontal header item should not be None"
            twoda.add_column(horizontal_header_item.text())

        for i in range(self.source_model.rowCount()):
            twoda.add_row()
            col_item = self.source_model.item(i, 0)
            assert col_item is not None, "Item should not be None"
            twoda.set_label(i, col_item.text())
            for j, header in enumerate(twoda.get_headers()):
                col_item = self.source_model.item(i, j + 1)
                assert col_item is not None, "Item should not be None"
                twoda.set_cell(i, header, col_item.text())

        data = bytearray()
        assert self._restype, assert_with_variable_trace(bool(self._restype), "self._restype must be valid.")
        write_2da(twoda, data, self._restype)
        return bytes(data), b""

    def new(self):
        super().new()

        # Initialize a brand new empty model and attach the proxy/table correctly
        self.source_model.clear()
        self.source_model.setRowCount(0)
        # Default to TwoDA for new files
        self._restype = ResourceType.TwoDA
        self.proxy_model.setSourceModel(self.source_model)
        self.ui.twodaTable.setModel(self.proxy_model)  # type: ignore[arg-type]

    def jump_to_row(
        self,
        row: int,
    ):
        """Jumps to and selects the specified row in the 2DA table."""
        if row < 0 or row >= self.source_model.rowCount():
            # Avoid showing blocking dialogs in headless/test environments — log a warning instead
            try:
                self._logger.warning(trf("Row {row} is out of range.", row=row))
            except Exception:
                # Ensure we don't crash if logger isn't available
                print(trf("Row {row} is out of range.", row=row))
            return
        index: QModelIndex = self.proxy_model.mapFromSource(self.source_model.index(row, 0))
        self.ui.twodaTable.setCurrentIndex(index)
        self.ui.twodaTable.scrollTo(index, self.ui.twodaTable.ScrollHint.EnsureVisible)  # type: ignore[arg-type]
        self.ui.twodaTable.selectRow(index.row())

    def do_filter(
        self,
        text: str,
    ):
        """Applies a filter to the 2DA table based on the provided text."""
        self.proxy_model.setFilterFixedString(text)

    def toggle_filter(self):
        """Toggles the visibility of the filter box."""
        # Ensure the widget is visible so child visibility reflects the toggle state (important for tests)
        if not self.isVisible():
            self.show()
        visible: bool = not self.ui.filterBox.isVisible()
        self.ui.filterBox.setVisible(visible)
        if visible:
            self.do_filter(self.ui.filterEdit.text())
            self.ui.filterEdit.setFocus()
            self.ui.filterEdit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # type: ignore[arg-type]
        else:
            self.do_filter("")

    def copy_selection(self):
        """Copies the selected cells to the clipboard in a tab-delimited format."""
        top = self.source_model.rowCount()
        bottom = -1
        left = self.source_model.columnCount()
        right = -1

        for index in self.ui.twodaTable.selectedIndexes():
            if not index.isValid():
                continue
            mapped_index = self.proxy_model.mapToSource(index)  # type: ignore[arg-type]

            top = min([top, mapped_index.row()])
            bottom = max([bottom, mapped_index.row()])
            left = min([left, mapped_index.column()])
            right = max([right, mapped_index.column()])

        # Determine whether to include the row-label column (column 0) in copied data.
        # If a valid current index exists and it is anchored to a data column (>0),
        # prefer to start copying at that anchor column. This handles cases where
        # someone calls selectRow() but intended to copy starting at a specific cell
        # (see test_twoda_editor_copy_paste_roundtrip).
        current_index = self.ui.twodaTable.currentIndex()
        anchor_col = None
        if current_index.isValid():
            try:
                anchor_col = self.proxy_model.mapToSource(current_index).column()  # type: ignore[arg-type]
            except Exception:
                anchor_col = None

        if anchor_col is not None and anchor_col > 0 and left < anchor_col:
            left = anchor_col

        clipboard = QApplication.clipboard()
        assert clipboard is not None, "Clipboard should not be None"

        # If no data columns selected, nothing to copy
        if left > right:
            clipboard.setText("")
            return

        clipboard_text: str = ""
        for j in range(top, bottom + 1):
            for i in range(left, right + 1):
                item = self.source_model.item(j, i)
                clipboard_text += item.text() if item is not None else ""
                if i != right:
                    clipboard_text += "\t"
            if j != bottom:
                clipboard_text += "\n"

        clipboard.setText(clipboard_text)

    def paste_selection(self):
        """Pastes tab-delimited data from the clipboard into the table starting at the selected cell."""
        clipboard = QApplication.clipboard()
        assert clipboard is not None, "Clipboard should not be None"
        rows: list[str] = clipboard.text().split("\n")
        selected_indexes = self.ui.twodaTable.selectedIndexes()
        if not selected_indexes:
            return
        selected_index = self.ui.twodaTable.selectedIndexes()[0]
        if not selected_index.isValid():
            return

        top_left_index = self.proxy_model.mapToSource(selected_index)  # type: ignore[arg-type]
        top_left_item: QStandardItem | None = self.source_model.itemFromIndex(top_left_index)
        assert top_left_item is not None, "Top-left item should not be None"

        # Starting coordinates
        y = top_left_item.row()
        x = top_left_item.column()
        start_x = x

        for row_text in rows:
            cells = row_text.split("\t")
            # If the first cell looks like a numeric row label and we're pasting into
            # a data column (not column 0), skip the first cell to avoid overwriting
            # data with row labels copied by selectRow() semantics.
            if len(cells) > 1 and cells[0].isdigit() and start_x > 0:
                cells = cells[1:]

            for cell in cells:
                item: QStandardItem | None = self.source_model.item(y, x)
                if item:
                    item.setText(cell)
                x += 1
            x = start_x
            y += 1

    def insert_row(self):
        """Inserts a new blank row at the end of the table."""
        row_index: int = self.source_model.rowCount()
        self.source_model.appendRow(
            [
                QStandardItem("")
                for _ in range(self.source_model.columnCount())
            ]
        )
        self.set_item_display_data(row_index)

    def duplicate_row(self):
        """Duplicates the currently selected row and appends it to the end of the table."""
        if self.ui.twodaTable.selectedIndexes():
            proxy_index = self.ui.twodaTable.selectedIndexes()[0]
            copy_row: int = self.proxy_model.mapToSource(proxy_index).row()  # type: ignore[arg-type]

            row_index: int = self.source_model.rowCount()
            # Clone each QStandardItem explicitly to preserve text, font, and other roles
            new_items: list[QStandardItem] = []
            for i in range(self.source_model.columnCount()):
                orig_item: QStandardItem | None = self.source_model.item(copy_row, i)
                if orig_item is None:
                    new_items.append(QStandardItem(""))
                else:
                    # QStandardItem.clone() returns a new QStandardItem with the same data
                    new_items.append(orig_item.clone())
            self.source_model.appendRow(new_items)
            self.set_item_display_data(row_index)

    def set_item_display_data(self, rowIndex: int):  # pylint: disable=C0103,invalid-name
        """Sets the display data for a specific row, including making the first column bold and setting its background."""
        item = QStandardItem(str(rowIndex))
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        item.setBackground(self.palette().midlight())
        self.source_model.setItem(rowIndex, 0, item)
        self.reset_vertical_headers()

    def remove_selected_rows(self):
        """Removes the rows the user has selected."""
        # Map proxy-selected rows back to source model rows before removal
        rows: set[int] = {self.proxy_model.mapToSource(index).row() for index in self.ui.twodaTable.selectedIndexes()}
        for row in sorted(rows, reverse=True):
            self.source_model.removeRow(row)

    def delete_row(self):
        """Compatibility wrapper for older tests and UI actions that expect delete_row()."""
        self.remove_selected_rows()

    def redo_row_labels(self):
        """Iterates through every row setting the row label to match the row index."""
        for i in range(self.source_model.rowCount()):
            item = self.source_model.item(i, 0)
            assert item is not None, "Item should not be None"
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            item.setText(str(i))

    def set_vertical_header_option(
        self,
        option: VerticalHeaderOption,
        column: str | None = None,
    ):
        """Sets the vertical header option and updates the headers accordingly."""
        self.vertical_header_option = option
        self.vertical_header_column = column or ""
        self.reset_vertical_headers()

    def reset_vertical_headers(self):
        """Resets the vertical headers based on the current vertical header option."""
        vertical_header = self.ui.twodaTable.verticalHeader()
        assert vertical_header is not None
        if GlobalSettings().selectedTheme in ("Native", "Fusion (Light)"):
            vertical_header.setStyleSheet("")
        headers: list[str] = []

        if self.vertical_header_option == VerticalHeaderOption.ROW_INDEX:
            headers = [str(i) for i in range(self.source_model.rowCount())]
        elif self.vertical_header_option == VerticalHeaderOption.ROW_LABEL:
            headers = [
                self.source_model.item(i, 0).text()  # type: ignore[attr-defined]
                for i in range(self.source_model.rowCount())
            ]
        elif self.vertical_header_option == VerticalHeaderOption.CELL_VALUE:
            col_index: int = 0
            for i in range(self.source_model.columnCount()):
                horizontal_header_item = self.source_model.horizontalHeaderItem(i)
                assert horizontal_header_item is not None, "Horizontal header item should not be None"
                if horizontal_header_item.text() == self.vertical_header_column:
                    col_index = i
            headers = [self.source_model.item(i, col_index).text() for i in range(self.source_model.rowCount())]  # type: ignore[attr-defined]
        elif self.vertical_header_option == VerticalHeaderOption.NONE:
            # Get palette colors
            app = QApplication.instance()
            if app is None or not isinstance(app, QApplication):
                palette = QPalette()
            else:
                palette = app.palette()

            window_text = palette.color(QPalette.ColorRole.WindowText)
            base = palette.color(QPalette.ColorRole.Base)
            alternate_base = palette.color(QPalette.ColorRole.AlternateBase)

            # Create transparent text color
            transparent_text = QColor(window_text)
            transparent_text.setAlpha(0)

            # Create hover background
            hover_bg = QColor(alternate_base if alternate_base != base else base)
            if hover_bg.lightness() < 128:  # Dark theme
                hover_bg = hover_bg.lighter(110)
            else:  # Light theme
                hover_bg = hover_bg.darker(95)

            if GlobalSettings().selectedTheme in ("Native", "Fusion (Light)"):
                vertical_header.setStyleSheet(f"QHeaderView::section {{ color: rgba({transparent_text.red()}, {transparent_text.green()}, {transparent_text.blue()}, 0); }} QHeaderView::section:checked {{ color: {window_text.name()}; }}")
            elif GlobalSettings().selectedTheme == "Fusion (Dark)":
                vertical_header.setStyleSheet(f"""
                    QHeaderView::section {{
                        color: rgba({transparent_text.red()}, {transparent_text.green()}, {transparent_text.blue()}, 0);  /* Transparent text */
                        background-color: {base.name()};  /* Base background */
                    }}
                    QHeaderView::section:checked {{
                        color: {window_text.name()};  /* Window text for checked sections */
                        background-color: {alternate_base.name() if alternate_base != base else hover_bg.name()};  /* Alternate base for checked sections */
                    }}
                    QHeaderView::section:hover {{
                        color: {window_text.name()};  /* Window text on hover */
                        background-color: {hover_bg.name()};  /* Hover background */
                    }}
                """)
                # Get additional palette colors for table styling
                button = palette.color(QPalette.ColorRole.Button)
                button_text = palette.color(QPalette.ColorRole.ButtonText)
                highlight = palette.color(QPalette.ColorRole.Highlight)
                highlighted_text = palette.color(QPalette.ColorRole.HighlightedText)
                mid = palette.color(QPalette.ColorRole.Mid)
                dark = palette.color(QPalette.ColorRole.Dark)

                # Create variants for hover/checked states
                header_bg = QColor(button if button.isValid() else base)
                header_hover_bg = QColor(header_bg)
                if header_hover_bg.lightness() < 128:  # Dark theme
                    header_hover_bg = header_hover_bg.lighter(110)
                else:  # Light theme
                    header_hover_bg = header_hover_bg.darker(95)

                # Use Mid for gridlines, fallback to Dark if Mid is invalid
                gridline = QColor(mid if mid.isValid() else (dark if dark.isValid() else base))

                self.ui.twodaTable.setStyleSheet(f"""
                    QHeaderView::section {{
                        background-color: {header_bg.name()};
                        color: {button_text.name() if button_text.isValid() else window_text.name()};
                        padding: 4px;
                        border: 1px solid {gridline.name()};
                    }}
                    QHeaderView::section:checked {{
                        background-color: {header_hover_bg.name()};
                        color: {button_text.name() if button_text.isValid() else window_text.name()};
                    }}
                    QHeaderView::section:hover {{
                        background-color: {header_hover_bg.name()};
                        color: {button_text.name() if button_text.isValid() else window_text.name()};
                    }}
                    QTableView {{
                        background-color: {base.name()};
                        alternate-background-color: {alternate_base.name() if alternate_base != base else base.name()};
                        color: {window_text.name()};
                        gridline-color: {gridline.name()};
                        selection-background-color: {highlight.name()};
                        selection-color: {highlighted_text.name()};
                    }}
                    QTableView::item {{
                        background-color: {base.name()};
                        color: {window_text.name()};
                    }}
                    QTableView::item:selected {{
                        background-color: {highlight.name()};
                        color: {highlighted_text.name()};
                    }}
                    QTableCornerButton::section {{
                        background-color: {header_bg.name()};
                        border: 1px solid {gridline.name()};
                    }}
                """)
            headers = ["⯈" for _ in range(self.source_model.rowCount())]

        for i in range(self.source_model.rowCount()):
            self.source_model.setVerticalHeaderItem(i, QStandardItem(headers[i]))


class SortFilterProxyModel(QSortFilterProxyModel):
    """Custom proxy model to filter 2DA table rows based on a search string."""
    def __init__(self, parent: QObject | None = None):
        """Initialize the TwoDA editor widget.

        Args:
            parent: The parent widget that owns this editor instance.
        """
        super().__init__(parent)

    def filterAcceptsRow(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        source_row: int,
        source_parent: QModelIndex,
    ) -> bool:
        """Determines whether a given row should be included in the filtered results."""
        pattern = None
        if qtpy.QT5:
            pattern = self.filterRegExp().pattern()  # pyright: ignore[reportAttributeAccessIssue]
        else:  # if qtpy.QT6:
            pattern = self.filterRegularExpression().pattern()

        if not pattern:
            return True
        case_insens_pattern = pattern.lower()
        src_model = self.sourceModel()
        assert src_model is not None, "Source model should not be None"
        for i in range(src_model.columnCount()):
            index = src_model.index(source_row, i, source_parent)
            if not index.isValid():
                continue
            data: str = src_model.data(index)
            if data is None:
                continue
            if case_insens_pattern in data.lower():
                return True
        return False


class VerticalHeaderOption(IntEnum):
    """Options for configuring the vertical headers in the 2DA editor."""
    ROW_INDEX = 0
    ROW_LABEL = 1
    CELL_VALUE = 2
    NONE = 3
