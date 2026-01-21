from __future__ import annotations

from typing import Callable

from qtpy.QtCore import QSize, Qt
from qtpy.QtGui import QAction
from qtpy.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QMenu,
    QSizePolicy,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from utility.ui_libraries.qt.common.action_definitions import FileExplorerActions
from utility.ui_libraries.qt.common.column_options_dialog import SetDefaultColumnsDialog
from utility.ui_libraries.qt.common.menu_definitions import FileExplorerMenus


class RibbonsWidget(QWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
        flags: Qt.WindowFlags | Qt.WindowType | None = None,  # pyright: ignore[reportAttributeAccessIssue]
        menus: FileExplorerMenus | None = None,
        columns_callback: Callable[[], None] | None = None,
    ):
        if flags is None:
            super().__init__(parent)
        else:
            super().__init__(parent, flags)
        self.menus: FileExplorerMenus = FileExplorerMenus() if menus is None else menus
        # Reuse the same actions instance as the menus when provided so dispatcher wiring applies.
        self.actions_definitions: FileExplorerActions = self.menus.actions if hasattr(self.menus, "actions") else FileExplorerActions()
        self.columns_callback: Callable[[], None] | None = columns_callback
        self.setup_main_layout()
        self.set_stylesheet()

    def setup_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.tab_widget: QTabWidget = QTabWidget()

        file_tab = QWidget()
        self.setup_file_ribbon(file_tab)
        self.tab_widget.addTab(file_tab, "File")

        home_tab = QWidget()
        self.setup_home_ribbon(home_tab)
        self.tab_widget.addTab(home_tab, "Home")

        share_tab = QWidget()
        self.tab_widget.addTab(share_tab, "Share")

        view_tab = QWidget()
        self.setup_view_ribbon(view_tab)
        self.tab_widget.addTab(view_tab, "View")

        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

    def setup_file_ribbon(self, tab: QWidget):
        # Implement file ribbon layout here
        pass

    def setup_home_ribbon(self, tab: QWidget):
        layout = QHBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        layout.addWidget(self.create_clipboard_group())
        layout.addWidget(self.create_organize_group())
        layout.addWidget(self.create_new_group())
        layout.addWidget(self.create_open_group())
        layout.addWidget(self.create_select_group())
        layout.addStretch()

        tab.setLayout(layout)

    def setup_view_ribbon(self, tab: QWidget):
        layout = QHBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        layout.addWidget(self.create_panes_group())
        layout.addWidget(self.create_layout_group())
        layout.addWidget(self.create_current_view_group())
        layout.addWidget(self.create_show_hide_group())
        layout.addWidget(self.create_columns_group())
        layout.addStretch()

        tab.setLayout(layout)

    def create_clipboard_group(self) -> QGroupBox:
        group = QGroupBox("Clipboard")
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        top_row = QHBoxLayout()
        top_row.addWidget(self.create_large_button("Pin to\nQuick access", self.actions_definitions.actionPinToQuickAccess))
        top_row.addWidget(self.create_large_button("Copy", self.actions_definitions.actionCopy))
        top_row.addWidget(self.create_large_button("Paste", self.actions_definitions.actionPaste))

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self.create_small_button("Cut", self.actions_definitions.actionCut))
        bottom_row.addWidget(self.create_small_button("Copy path", self.actions_definitions.actionCopyPath))
        bottom_row.addWidget(self.create_small_button("Paste shortcut", self.actions_definitions.actionPasteShortcut))

        layout.addLayout(top_row)
        layout.addLayout(bottom_row)
        group.setLayout(layout)
        return group

    def create_organize_group(self) -> QGroupBox:
        group = QGroupBox("Organize")
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        top_row = QHBoxLayout()
        move_to_button = self.create_large_button("Move to", self.actions_definitions.actionMoveTo)
        move_to_button.setMenu(QMenu())
        top_row.addWidget(move_to_button)

        copy_to_button = self.create_large_button("Copy to", self.actions_definitions.actionCopyTo)
        copy_to_button.setMenu(QMenu())
        top_row.addWidget(copy_to_button)

        bottom_row = QHBoxLayout()
        delete_button = self.create_small_button("Delete", self.actions_definitions.actionDelete)
        delete_button.setMenu(QMenu())
        bottom_row.addWidget(delete_button)
        bottom_row.addWidget(self.create_small_button("Rename", self.actions_definitions.actionRename))

        layout.addLayout(top_row)
        layout.addLayout(bottom_row)
        group.setLayout(layout)
        return group

    def create_new_group(self) -> QGroupBox:
        group = QGroupBox("New")
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        new_folder_button = self.create_large_button("New\nfolder", self.actions_definitions.actionCreateNewFolder)
        layout.addWidget(new_folder_button)

        new_item_button = self.create_small_button("New item", self.actions_definitions.actionNewBlankFile)
        new_item_button.setMenu(QMenu())
        layout.addWidget(new_item_button)

        group.setLayout(layout)
        return group

    def create_open_group(self) -> QGroupBox:
        group = QGroupBox("Open")
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        top_row = QHBoxLayout()
        properties_button = self.create_large_button("Properties", self.actions_definitions.actionProperties)
        top_row.addWidget(properties_button)

        bottom_row = QHBoxLayout()
        open_button = self.create_small_button("Open", self.actions_definitions.actionOpen)
        open_button.setMenu(QMenu())
        bottom_row.addWidget(open_button)
        bottom_row.addWidget(self.create_small_button("Edit", self.actions_definitions.actionEdit))

        easy_access_button = self.create_small_button("Easy access", QAction())
        easy_access_button.setMenu(QMenu())
        bottom_row.addWidget(easy_access_button)

        bottom_row.addWidget(self.create_small_button("History", QAction()))

        layout.addLayout(top_row)
        layout.addLayout(bottom_row)
        group.setLayout(layout)
        return group

    def create_select_group(self) -> QGroupBox:
        group = QGroupBox("Select")
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        layout.addWidget(self.create_small_button("Select all", self.actions_definitions.actionSelectAll))
        layout.addWidget(self.create_small_button("Select none", self.actions_definitions.actionSelectNone))
        layout.addWidget(self.create_small_button("Invert selection", self.actions_definitions.actionInvertSelection))

        group.setLayout(layout)
        return group

    def create_panes_group(self) -> QGroupBox:
        group = QGroupBox("Panes")
        layout = QHBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        navigation_pane_button = self.create_large_button("Navigation\npane", self.actions_definitions.actionNavigationPane)
        navigation_pane_button.setMenu(QMenu())
        layout.addWidget(navigation_pane_button)
        layout.addWidget(self.create_large_button("Preview\npane", self.actions_definitions.actionPreviewPane))
        layout.addWidget(self.create_large_button("Details\npane", self.actions_definitions.actionDetailsPane))

        group.setLayout(layout)
        return group

    def create_layout_group(self) -> QGroupBox:
        group = QGroupBox("Layout")
        layout = QGridLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        layout.addWidget(self.create_small_button("Extra large\nicons", self.actions_definitions.actionExtraLargeIcons), 0, 0)
        layout.addWidget(self.create_small_button("Large\nicons", self.actions_definitions.actionLargeIcons), 0, 1)
        layout.addWidget(self.create_small_button("Medium\nicons", self.actions_definitions.actionMediumIcons), 0, 2)
        layout.addWidget(self.create_small_button("Small\nicons", self.actions_definitions.actionSmallIcons), 1, 0)
        layout.addWidget(self.create_small_button("List", self.actions_definitions.actionListView), 1, 1)
        layout.addWidget(self.create_small_button("Details", self.actions_definitions.actionDetailView), 1, 2)
        layout.addWidget(self.create_small_button("Tiles", self.actions_definitions.actionTiles), 2, 0)
        layout.addWidget(self.create_small_button("Content", self.actions_definitions.actionContent), 2, 1)

        group.setLayout(layout)
        return group

    def create_current_view_group(self) -> QGroupBox:
        group = QGroupBox("Current view")
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        top_row = QHBoxLayout()
        sort_by_button = self.create_small_button("Sort by", QAction())
        sort_by_menu = QMenu()
        sort_by_menu.addAction("Name")
        sort_by_menu.addAction("Date modified")
        sort_by_menu.addAction("Type")
        sort_by_menu.addAction("Size")
        sort_by_button.setMenu(sort_by_menu)
        top_row.addWidget(sort_by_button)

        group_by_button = self.create_small_button("Group by", QAction())
        group_by_menu = QMenu()
        group_by_menu.addAction("None")
        group_by_menu.addAction("Name")
        group_by_menu.addAction("Date modified")
        group_by_menu.addAction("Type")
        group_by_menu.addAction("Size")
        group_by_button.setMenu(group_by_menu)
        top_row.addWidget(group_by_button)

        bottom_row = QHBoxLayout()
        add_columns_button = self.create_small_button("Add columns", QAction())
        add_columns_button.clicked.connect(self.show_set_default_columns_dialog)
        bottom_row.addWidget(add_columns_button)
        bottom_row.addWidget(self.create_small_button("Size all\ncolumns to fit", QAction()))

        layout.addLayout(top_row)
        layout.addLayout(bottom_row)
        group.setLayout(layout)
        return group

    def show_set_default_columns_dialog(self):
        dialog = SetDefaultColumnsDialog(self)
        dialog.exec()

    def create_show_hide_group(self) -> QGroupBox:
        group = QGroupBox("Show/hide")
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        layout.addWidget(self.create_checkbox_button("Item check boxes", QAction()))
        layout.addWidget(self.create_checkbox_button("File name extensions", QAction()))
        layout.addWidget(self.create_checkbox_button("Hidden items", QAction()))

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self.create_small_button("Hide selected\nitems", QAction()))
        bottom_row.addWidget(self.create_small_button("Options", self.actions_definitions.actionOptions))

        layout.addLayout(bottom_row)
        group.setLayout(layout)
        return group

    def create_columns_group(self) -> QGroupBox:
        group = QGroupBox("Columns")
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        choose_columns_action = QAction("Columns", self)
        if self.columns_callback:
            choose_columns_action.triggered.connect(self.columns_callback)
        else:
            choose_columns_action.triggered.connect(self._show_columns_dialog_default)

        layout.addWidget(self.create_small_button("Columns...", choose_columns_action))
        group.setLayout(layout)
        return group

    def _show_columns_dialog_default(self):
        dialog = SetDefaultColumnsDialog(self)
        dialog.exec()

    def create_large_button(self, text: str, action: QAction) -> QToolButton:
        button = QToolButton()
        button.setDefaultAction(action)
        button.setText(text)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        button.setFixedSize(80, 70)
        button.setIconSize(QSize(32, 32))
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        return button

    def create_small_button(self, text: str, action: QAction) -> QToolButton:
        button = QToolButton()
        button.setDefaultAction(action)
        button.setText(text)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        button.setFixedSize(80, 22)
        button.setIconSize(QSize(16, 16))
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        return button

    def create_checkbox_button(self, text: str, action: QAction) -> QToolButton:
        button = QToolButton()
        button.setDefaultAction(action)
        button.setText(text)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        button.setFixedSize(120, 22)
        button.setIconSize(QSize(16, 16))
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        button.setCheckable(True)
        return button

    def set_stylesheet(self):
        from qtpy.QtWidgets import QApplication
        from qtpy.QtGui import QPalette

        app = QApplication.instance()
        assert isinstance(app, QApplication), "QApplication.instance() is not a QApplication"
        palette = app.palette()

        # Fallback colors if running out-of-context or for headless tests
        def color_hex(
            role: str,
            group: str = "Active",
            default: str = "#C0C0C0",
        ) -> str:
            if palette is not None:
                try:
                    color_role = getattr(QPalette, role, None)
                    color_group = getattr(QPalette, group, QPalette.ColorGroup.Active)
                    if color_role is not None:
                        return palette.color(color_group, color_role).name()
                except Exception:
                    pass
            return default

        # Replace hardcoded colors beneath with palette-based ones
        border_color        = color_hex("Mid",       default="#C0C0C0")
        groupbox_border     = color_hex("Midlight",  default="#C0C0C0")
        tab_bg              = color_hex("Base",      default="#F0F0F0")
        tab_border          = color_hex("Midlight",  default="#C4C4C3")
        tab_selected_border = color_hex("Shadow",    default="#9B9B9B")
        tab_selected_bg     = color_hex("Light",     default="#fafafa")
        button_hover_bg     = color_hex("Highlight", default="#E5F3FF")
        button_checked_bg   = color_hex("Button",    default="#CCE8FF")
        button_focus_border = color_hex("Highlight", default="#0078D7")
        
        tab_bar0_4 = color_hex("AlternateBase", default="#DEDEDE")
        tab_bar0_5 = color_hex("Window",        default="#D8D8D8")
        tab_bar1_0 = color_hex("Light",         default="#D3D3D3")
        tab_hover_0_4 = color_hex("AlternateBase", default="#f4f4f4")
        tab_hover_0_5 = color_hex("Window",        default="#e7e7e7")
        tab_hover_1_0 = color_hex("Base",          default="#e0e0e0")
        tab_selected_btm = color_hex("Dark",       default="#C2C7CB")

        stylesheet = f"""
            QTabWidget::pane {{
                border-top: 1px solid {border_color};
                position: absolute;
                top: -1px;
            }}
            QTabBar::tab {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                            stop: 0 {tab_bg}, stop: 0.4 {tab_bar0_4},
                                            stop: 0.5 {tab_bar0_5}, stop: 1.0 {tab_bar1_0});
                border: 1px solid {tab_border};
                border-bottom-color: {tab_selected_btm};
                min-width: 8ex;
                padding: 2px 8px;
            }}
            QTabBar::tab:selected, QTabBar::tab:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                            stop: 0 {tab_selected_bg}, stop: 0.4 {tab_hover_0_4},
                                            stop: 0.5 {tab_hover_0_5}, stop: 1.0 {tab_hover_1_0});
            }}
            QTabBar::tab:selected {{
                border-color: {tab_selected_border};
                border-bottom-color: {tab_selected_btm};
            }}
            QGroupBox {{
                border: 1px solid {groupbox_border};
                border-radius: 4px;
                margin-top: 0.5em;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 7px;
                padding: 0 3px 0 3px;
            }}
            QToolButton {{
                border: 1px solid transparent;
                border-radius: 2px;
                background-color: transparent;
            }}
            QToolButton:hover {{
                border: 1px solid {border_color};
                background-color: {button_hover_bg};
            }}
            QToolButton:pressed, QToolButton:checked {{
                border: 1px solid {button_focus_border};
                background-color: {button_checked_bg};
            }}
        """
        self.setStyleSheet(stylesheet)


if __name__ == "__main__":
    import sys

    from qtpy.QtWidgets import QApplication

    app = QApplication(sys.argv)

    window = QWidget()
    layout = QVBoxLayout(window)

    ribbons_widget = RibbonsWidget()
    layout.addWidget(ribbons_widget)

    window.setWindowTitle("Explorer Ribbon Test")
    window.setGeometry(100, 100, 1200, 200)
    window.show()

    sys.exit(app.exec())
