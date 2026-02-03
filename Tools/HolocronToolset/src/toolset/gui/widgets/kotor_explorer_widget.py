"""
KOTOR Explorer Widget - File explorer interface for KOTOR installations.

Extends FileSystemExplorerWidget to work with KOTOR file systems and installations.
Provides a unified tree-based interface for browsing game resources.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from qtpy.QtCore import (
    QAbstractItemModel,
    QDir,
    QFile,
    QIODevice,
    QItemSelectionModel,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
    Signal,
)
from qtpy.QtGui import QFileIconProvider, QIcon, QPixmap, QStandardItemModel
from qtpy.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCompleter,
    QFileSystemModel,
    QListView,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from utility.gui.qt.filesystem.qfileexplorer.explorer_ui import Ui_QFileExplorer
from utility.gui.qt.tools.image import IconLoader

if TYPE_CHECKING:
    from types import TracebackType


class KotorExplorerWidget(QMainWindow):
    """Explorer widget specialized for KOTOR installations and resources.
    
    Provides a file explorer-like interface with:
    - Tree view of installations and categories
    - Multiple view modes (list, tree, icons, table)
    - Resource extraction and opening
    - Search functionality
    """

    file_selected = Signal(str)
    directory_changed = Signal(str)
    open_in_new_tab = Signal(str)

    def __init__(
        self,
        initial_path: Path | str | None = None,
        parent: QWidget | None = None,
    ):
        """Initialize KOTOR Explorer Widget.
        
        Args:
            initial_path: Initial path to display (home directory if None)
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Setup UI from explorer template
        self.ui = Ui_QFileExplorer()
        self.ui.setupUi(self)
        
        # Initialize basic attributes
        self.current_path = Path.home() if initial_path is None else Path(initial_path)
        self.cut_files: list[Path] | None = None
        self.icon_loader = IconLoader()
        
        # Setup file system model
        self.fs_model = QFileSystemModel()
        self.fs_model.setOption(QFileSystemModel.Option.DontWatchForChanges, False)
        self.fs_model.setOption(QFileSystemModel.Option.DontResolveSymlinks, True)
        self.fs_model.setRootPath(str(self.current_path.root))
        self.fs_model.setReadOnly(False)
        self.fs_model.setIconProvider(QFileIconProvider())
        
        # Setup proxy model for sorting/filtering
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.fs_model)
        
        # Setup completer
        self.completer = QCompleter(self)
        self.completer.setModel(self.fs_model)
        
        # Setup bookmarks
        self.bookmarks_model = QStandardItemModel()
        self.ui.bookmarksListView.setModel(self.bookmarks_model)
        self.ui.bookmarksListView.clicked.connect(self.on_bookmark_clicked)
        
        # Setup tree view
        self.ui.fileSystemTreeView.setModel(self.fs_model)
        self.ui.fileSystemTreeView.setRootIndex(self.fs_model.index(QDir.rootPath()))
        self.ui.fileSystemTreeView.clicked.connect(self.on_sidepanel_treeview_clicked)
        self.ui.fileSystemTreeView.expanded.connect(self.on_treeview_expanded)
        self.ui.fileSystemTreeView.collapsed.connect(self.on_treeview_collapsed)
        
        # Hide non-name columns in tree view
        for i in range(1, self.fs_model.columnCount()):
            self.ui.fileSystemTreeView.hideColumn(i)
        
        # Setup dynamic view (multi-view)
        self.ui.dynamicView.setModel(self.proxy_model)
        root_idx = self.proxy_model.mapFromSource(self.fs_model.index(str(self.current_path)))
        self.ui.dynamicView.setRootIndex(root_idx)
        self.ui.dynamicView.show()
        
        # Connect view signals
        for view in self.ui.dynamicView.all_views():
            view.clicked.connect(self.on_file_list_view_clicked)
            view.doubleClicked.connect(self.on_item_double_clicked)
        
        self.ui.dynamicView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.dynamicView.customContextMenuRequested.connect(self.show_context_menu)
        self.ui.dynamicView.selectionModel().selectionChanged.connect(self.update_preview)
        
        # Setup address bar
        self.ui.addressBar.refreshButton.clicked.connect(lambda: self.refresh())
        self.ui.addressBar.pathChanged.connect(self.on_address_bar_path_changed)
        self.ui.addressBar.returnPressed.connect(self.on_address_bar_return)
        
        # Setup zoom
        self.ui.zoom_slider.valueChanged.connect(self.on_zoom_slider_changed)
        
        # Setup drive buttons
        drive_layout = self.ui.horizontalLayout_2
        for drive in QDir.drives():
            drive_path = drive.path()
            drive_button = QPushButton(drive_path)
            drive_button.clicked.connect(lambda _, path=drive_path: self.set_current_path(path))
            drive_layout.addWidget(drive_button)
        
        # Setup search
        if self.ui.searchBar.isVisible():
            self.ui.searchBar.hide()
        self.ui.searchBar.textChanged.connect(self.on_search_text_changed)
        self.ui.searchBar.setPlaceholderText("Search...")
        
        # Final setup
        self.resize(1000, 600)
        self.ui.mainSplitter.setSizes([200, 800])
        self.ui.sidebarToolBox.setMinimumWidth(150)
        self.ui.dynamicView.setMinimumWidth(400)
        self.ui.searchAndAddressWidget.setFixedHeight(30)
        self.ui.previewWidget.setVisible(False)
        
        # Update UI
        self.update_ui()
        self.ui.addressBar.update_path(self.current_path)

    def on_sidepanel_treeview_clicked(self, index: QModelIndex) -> None:
        """Handle tree view item click."""
        path = self.fs_model.filePath(index)
        self.set_current_path(path)

    def on_treeview_expanded(self, index: QModelIndex) -> None:
        """Handle tree view expansion."""
        pass

    def on_treeview_collapsed(self, index: QModelIndex) -> None:
        """Handle tree view collapse."""
        pass

    def on_file_list_view_clicked(self, index: QModelIndex) -> None:
        """Handle file list view click."""
        proxy_index = cast(QModelIndex, index)
        source_index = self.proxy_model.mapToSource(proxy_index)
        path = self.fs_model.filePath(source_index)
        self.file_selected.emit(path)

    def on_item_double_clicked(self, index: QModelIndex) -> None:
        """Handle double-click on item."""
        proxy_index = cast(QModelIndex, index)
        source_index = self.proxy_model.mapToSource(proxy_index)
        path = self.fs_model.filePath(source_index)
        
        if self.fs_model.isDir(source_index):
            self.set_current_path(path)
        else:
            # Emit signal for resource opening
            self.file_selected.emit(path)

    def on_bookmark_clicked(self, index: QModelIndex) -> None:
        """Handle bookmark click."""
        item = self.bookmarks_model.itemFromIndex(index)
        if item:
            path = item.data(Qt.ItemDataRole.UserRole)
            self.set_current_path(path)

    def on_address_bar_path_changed(self, path: str) -> None:
        """Handle address bar path change."""
        self.set_current_path(path)

    def on_address_bar_return(self) -> None:
        """Handle address bar return key."""
        path = self.ui.addressBar.text()
        self.set_current_path(path)

    def on_search_text_changed(self, text: str) -> None:
        """Handle search text change."""
        self.proxy_model.setFilterWildcard(text)

    def on_zoom_slider_changed(self, value: int) -> None:
        """Handle zoom slider change."""
        # Scale icon size based on slider value
        icon_size = 32 + (value - 50) // 5
        if icon_size > 0:
            self.ui.dynamicView.list_view().setIconSize(icon_size, icon_size)

    def update_preview(self, selected,  deselected) -> None:
        """Update preview panel based on selection."""
        # Placeholder for preview update logic
        pass

    def show_context_menu(self, position) -> None:
        """Show context menu for resources."""
        # Placeholder for context menu logic
        pass

    def set_current_path(self, path: str | Path) -> None:
        """Set the current path and update views.
        
        Args:
            path: Path to navigate to
        """
        path = Path(path) if isinstance(path, str) else path
        if not path.exists():
            return
            
        self.current_path = path
        self.directory_changed.emit(str(path))
        
        # Update tree view
        tree_index = self.fs_model.index(str(path))
        self.ui.fileSystemTreeView.setCurrentIndex(tree_index)
        self.ui.fileSystemTreeView.scrollTo(tree_index, QAbstractItemView.ScrollHint.PositionAtCenter)
        
        # Update dynamic view
        proxy_index = self.proxy_model.mapFromSource(tree_index)
        self.ui.dynamicView.setRootIndex(proxy_index)
        
        # Update address bar
        self.ui.addressBar.update_path(path)

    def refresh(self) -> None:
        """Refresh the current view."""
        self.set_current_path(self.current_path)

    def update_ui(self) -> None:
        """Update UI elements like status bar."""
        # Count items
        root_index = self.fs_model.index(str(self.current_path))
        item_count = self.fs_model.rowCount(root_index)
        self.ui.itemCountLabel.setText(f"Items: {item_count}")

    def closeEvent(self, event) -> None:
        """Handle widget close."""
        event.accept()
