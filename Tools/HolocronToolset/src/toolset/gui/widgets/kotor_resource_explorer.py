"""KOTOR Resource Explorer Widget.

A file explorer-style widget for browsing KOTOR game installations and resources.
Integrates KotorFileSystemModel with a modern explorer UI.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, cast

from qtpy.QtCore import QModelIndex, QItemSelectionModel, Qt, Signal
from qtpy.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QHeaderView,
    QListView,
    QStackedWidget,
    QTreeView,
    QTableView,
    QWidget,
)
from qtpy.QtCore import QSize

from loggerplus import RobustLogger
from toolset.gui.widgets.kotor_filesystem_model import KotorFileSystemModel, CategoryItem, ResourceItem
from toolset.utils.window import open_resource_editor
from utility.gui.qt.widgets.itemviews.treeview import RobustTreeView
from utility.gui.qt.widgets.itemviews.listview import RobustListView
from utility.gui.qt.widgets.itemviews.tableview import RobustTableView

if TYPE_CHECKING:
    from qtpy.QtCore import QPoint
    from qtpy.QtGui import QContextMenuEvent
    from qtpy.QtWidgets import QMenu
    
    from toolset.data.installation import HTInstallation
    from toolset.gui.widgets.settings.installations import InstallationConfig


class KotorResourceExplorer(QWidget):
    """A file explorer widget for KOTOR game resources.
    
    Provides a unified tree-based interface for browsing installations,
    categories (Core/Modules/Override/Textures/Saves), and resource files.
    
    Features:
    - Multiple view modes (Tree, List, Icon, Table)
    - Context menus
    - Double-click to open resources
    - Selection tracking
    - Integration with KotorFileSystemModel
    """
    
    file_selected = Signal(str)
    directory_changed = Signal(str)
    resource_double_clicked = Signal(object)  # FileResource
    selection_changed = Signal(list)  # List of FileResource objects
    
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        view_stack: QStackedWidget | None = None,
        view_mode_buttons: tuple | None = None,
    ):
        """Initialize the KOTOR Resource Explorer.
        
        Args:
        ----
            parent: Parent widget
            view_stack: QStackedWidget containing the view pages (tree/list/icon/table)
            view_mode_buttons: Tuple of (treeBtn, listBtn, iconBtn, tableBtn) for view mode switching
        """
        super().__init__(parent)
        
        self.active_installation: HTInstallation | None = None
        
        # Initialize the model
        self.model = KotorFileSystemModel(self)
        
        # Setup view stack and views
        self.view_stack = view_stack
        if self.view_stack is not None:
            # Get views from the stack
            self.tree_view = self._setup_tree_view()
            self.list_view = self._setup_list_view()
            self.icon_view = self._setup_icon_view()
            self.table_view = self._setup_table_view()
            
            # Set the same model on all views
            self.tree_view.setModel(self.model)
            self.list_view.setModel(self.model)
            self.icon_view.setModel(self.model)
            self.table_view.setModel(self.model)
            
            # Setup view mode buttons
            if view_mode_buttons is not None:
                self._setup_view_mode_buttons(view_mode_buttons)
        
        # Setup connections
        self._setup_signals()
        
        RobustLogger().debug("KotorResourceExplorer initialized")
    
    def _setup_tree_view(self) -> RobustTreeView:
        """Setup the tree view from the stacked widget."""
        # Get the tree view page
        tree_page = self.view_stack.widget(0)  # treeViewPage
        tree_view = tree_page.findChild(QTreeView, "resourceTree")
        
        if tree_view is None:
            raise RuntimeError("resourceTree not found in view stack")
        
        # Replace with RobustTreeView if needed
        if not isinstance(tree_view, RobustTreeView):
            layout = tree_page.layout()
            parent_widget = tree_view.parent()
            
            robust_tree = RobustTreeView(parent_widget, use_columns=True)
            robust_tree.setObjectName("resourceTree")
            
            if layout is not None:
                layout.removeWidget(tree_view)
                tree_view.deleteLater()
                layout.addWidget(robust_tree)
                tree_view = robust_tree
        
        tree_view.setUniformRowHeights(True)
        tree_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        tree_view.setSortingEnabled(True)
        tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tree_view.setAlternatingRowColors(True)
        
        header = tree_view.header()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            header.setStretchLastSection(True)
            header.setSortIndicatorShown(True)
        
        return tree_view
    
    def _setup_list_view(self) -> RobustListView:
        """Setup the list view from the stacked widget."""
        list_page = self.view_stack.widget(1)  # listViewPage
        list_view = list_page.findChild(QListView, "resourceList")
        
        if list_view is None:
            raise RuntimeError("resourceList not found in view stack")
        
        # Replace with RobustListView if needed
        if not isinstance(list_view, RobustListView):
            layout = list_page.layout()
            parent_widget = list_view.parent()
            
            robust_list = RobustListView(parent_widget)
            robust_list.setObjectName("resourceList")
            
            if layout is not None:
                layout.removeWidget(list_view)
                list_view.deleteLater()
                layout.addWidget(robust_list)
                list_view = robust_list
        
        list_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        list_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        list_view.setAlternatingRowColors(True)
        list_view.setViewMode(QListView.ViewMode.ListMode)
        
        return list_view
    
    def _setup_icon_view(self) -> QListView:
        """Setup the icon view from the stacked widget."""
        icon_page: QWidget | None = self.view_stack.widget(2)  # iconViewPage
        assert icon_page is not None, "icon_page is somehow None"
        icon_view = icon_page.findChild(QListView, "resourceIconView")
        
        if icon_view is None:
            raise RuntimeError("resourceIconView not found in view stack")
        
        icon_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        icon_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        icon_view.setViewMode(QListView.ViewMode.IconMode)
        icon_view.setResizeMode(QListView.ResizeMode.Adjust)
        icon_view.setGridSize(QSize(100, 100))
        
        return icon_view
    
    def _setup_table_view(self) -> RobustTableView:
        """Setup the table view from the stacked widget."""
        table_page: QWidget | None = self.view_stack.widget(3)  # tableViewPage
        assert table_page is not None, "table_page is somehow None"
        table_view = table_page.findChild(QTableView, "resourceTable")
        
        if table_view is None:
            raise RuntimeError("resourceTable not found in view stack")
        
        # Replace with RobustTableView if needed
        if not isinstance(table_view, RobustTableView):
            layout = table_page.layout()
            parent_widget = table_view.parent()
            
            robust_table = RobustTableView(parent_widget)
            robust_table.setObjectName("resourceTable")
            
            if layout is not None:
                layout.removeWidget(table_view)
                table_view.deleteLater()
                layout.addWidget(robust_table)
                table_view = robust_table
        
        table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table_view.setAlternatingRowColors(True)
        table_view.setSortingEnabled(True)
        
        h_header = table_view.horizontalHeader()
        if h_header is not None:
            h_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            h_header.setStretchLastSection(True)
        
        return table_view
    
    def _setup_view_mode_buttons(self, buttons: tuple):
        """Setup view mode button group and connections."""
        tree_btn, list_btn, icon_btn, table_btn = buttons
        
        # Create exclusive button group
        self.view_mode_group = QButtonGroup(self)
        self.view_mode_group.addButton(tree_btn, 0)
        self.view_mode_group.addButton(list_btn, 1)
        self.view_mode_group.addButton(icon_btn, 2)
        self.view_mode_group.addButton(table_btn, 3)
        
        # Connect to switch views
        tree_btn.clicked.connect(lambda: self.set_view_mode(0))
        list_btn.clicked.connect(lambda: self.set_view_mode(1))
        icon_btn.clicked.connect(lambda: self.set_view_mode(2))
        table_btn.clicked.connect(lambda: self.set_view_mode(3))
    
    def _setup_signals(self):
        """Setup signal connections for all views."""
        if self.view_stack is None:
            return
        
        # Double-click handlers
        self.tree_view.doubleClicked.connect(self.on_item_double_clicked)
        self.list_view.doubleClicked.connect(self.on_item_double_clicked)
        self.icon_view.doubleClicked.connect(self.on_item_double_clicked)
        self.table_view.doubleClicked.connect(self.on_item_double_clicked)
        
        # Context menu handlers
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        self.list_view.customContextMenuRequested.connect(self.show_context_menu)
        self.icon_view.customContextMenuRequested.connect(self.show_context_menu)
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)
        
        # Selection changed
        self.tree_view.selectionModel().selectionChanged.connect(self.on_selection_changed)
    
    def set_view_mode(self, mode: int):
        """Switch to a different view mode.
        
        Args:
        ----
            mode: 0=Tree, 1=List, 2=Icon, 3=Table
        """
        if self.view_stack is None:
            return
        
        self.view_stack.setCurrentIndex(mode)
        RobustLogger().debug(f"Switched to view mode {mode}")
    
    def current_view(self) -> QAbstractItemView:
        """Get the currently active view."""
        if self.view_stack is None or self.view_stack.currentIndex() == 0:
            return self.tree_view
        if self.view_stack.currentIndex() == 1:
            return self.list_view
        if self.view_stack.currentIndex() == 2:
            return self.icon_view
        return self.table_view
    
    def set_installations(self, installations: dict[str, InstallationConfig]):
        """Load installations into the model.
        
        Args:
        ----
            installations: Dictionary of installation configs
        """
        self.model.set_installations(installations)
        RobustLogger().info(f"Loaded {len(installations)} installations into explorer")
    
    def on_item_double_clicked(self, index: QModelIndex):
        """Handle double-click on an item."""
        if not index.isValid():
            return
        
        item = self.model.itemFromIndex(index)
        RobustLogger().debug(f"Double-clicked: {item.__class__.__name__}")
        
        # Expand/collapse directory items
        if isinstance(item, (CategoryItem,)):
            current_view = self.current_view()
            if isinstance(current_view, QTreeView):
                if current_view.isExpanded(index):
                    current_view.collapse(index)
                else:
                    current_view.expand(index)
            return
        
        # Open resource files
        if isinstance(item, ResourceItem):
            self.open_resource_item(item)
    
    def open_resource_item(self, item: ResourceItem):
        """Open a resource item in an editor.
        
        Args:
        ----
            item: ResourceItem to open
        """
        if not item.path.exists() or not item.path.is_file():
            RobustLogger().warning(f"Cannot open non-existent file: {item.path}")
            return
        
        # Get main window to access active installation
        main_window = None
        for widget in QApplication.topLevelWidgets():
            if widget.__class__.__name__ == "ToolWindow":
                main_window = widget
                break
        
        if main_window is None:
            RobustLogger().error("Could not find ToolWindow for opening resource")
            return
        
        open_resource_editor(
            item.path,
            item.resource.resname(),
            item.resource.restype(),
            item.resource.data(),
            installation=getattr(main_window, "active", None),
            parentWindow=main_window,
        )
        
        self.resource_double_clicked.emit(item.resource)
    
    def show_context_menu(self, point: QPoint):
        """Show context menu at the given point."""
        current_view = self.current_view()
        index = current_view.indexAt(point)
        
        if not index.isValid():
            return
        
        item = self.model.itemFromIndex(index)
        menu = current_view.build_context_menu() if hasattr(current_view, "build_context_menu") else QMenu(self)
        
        # Add resource-specific actions
        if isinstance(item, ResourceItem):
            menu.addSeparator()
            open_action = menu.addAction("Open")
            open_action.triggered.connect(lambda: self.open_resource_item(item))
            
            extract_action = menu.addAction("Extract...")
            extract_action.triggered.connect(lambda: self.extract_resource_item(item))
        
        menu.exec_(current_view.viewport().mapToGlobal(point))
    
    def extract_resource_item(self, item: ResourceItem):
        """Extract a resource item to disk.
        
        Args:
        ----
            item: ResourceItem to extract
        """
        from qtpy.QtWidgets import QFileDialog
        
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Extract Resource",
            item.resource.filename(),
            "All Files (*.*)",
        )
        
        if not save_path:
            return
        
        try:
            Path(save_path).write_bytes(item.resource.data())
            RobustLogger().info(f"Extracted {item.resource.filename()} to {save_path}")
        except Exception as e:
            RobustLogger().exception(f"Failed to extract resource: {e}")
    
    def on_selection_changed(self):
        """Handle selection changes in views."""
        current_view = self.current_view()
        selection_model = current_view.selectionModel()
        
        if selection_model is None:
            return
        
        selected_indexes = selection_model.selectedIndexes()
        selected_resources = []
        
        for index in selected_indexes:
            if index.column() != 0:  # Only process first column
                continue
            
            item = self.model.itemFromIndex(index)
            if isinstance(item, ResourceItem):
                selected_resources.append(item.resource)
        
        self.selection_changed.emit(selected_resources)
        RobustLogger().debug(f"Selection changed: {len(selected_resources)} resources selected")
    
    def selected_resources(self) -> list:
        """Get currently selected resources.
        
        Returns:
        -------
            List of FileResource objects
        """
        current_view = self.current_view()
        selection_model = current_view.selectionModel()
        
        if selection_model is None:
            return []
        
        resources = []
        for index in selection_model.selectedIndexes():
            if index.column() != 0:
                continue
            
            item = self.model.itemFromIndex(index)
            if isinstance(item, ResourceItem):
                resources.append(item.resource)
        
        return resources
