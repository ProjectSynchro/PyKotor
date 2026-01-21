from __future__ import annotations

from pathlib import Path
import sys
import traceback

from enum import Enum
from typing import TYPE_CHECKING, cast, overload
from collections.abc import Iterable

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import (
    QAbstractItemModel,
    QByteArray,
    QDir,
    QEvent,
    QUrl,
    Qt,
)
from qtpy.QtWidgets import QApplication, QFileDialog, QFileSystemModel, QLayoutItem, QMessageBox, QWidget

from utility.ui_libraries.qt.adapters.filesystem.qfiledialog.qfiledialog import QFileDialog as AdapterQFileDialog
from utility.ui_libraries.qt.common.actions_dispatcher import ActionsDispatcher
from utility.ui_libraries.qt.common.tasks.actions_executor import FileActionsExecutor
from utility.ui_libraries.qt.common.ribbons_widget import RibbonsWidget
from utility.ui_libraries.qt.filesystem.qfiledialogextended.ui_qfiledialogextended import Ui_QFileDialogExtended
from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTreeView
from utility.ui_libraries.qt.widgets.widgets.stacked_view import DynamicStackedView

if TYPE_CHECKING:
    from qtpy.QtCore import QAbstractItemModel, QModelIndex, QObject, QPoint
    from qtpy.QtGui import QMouseEvent
    from qtpy.QtWidgets import QAbstractItemView, QListView, QTreeView



class ReplaceStrategy(Enum):
    RECREATION_EXTENDED = "recreation_extended"
    RECREATION = "recreation"
    CLASS_REASSIGN = "class_reassign"


class QFileDialogExtended(AdapterQFileDialog):
    @overload
    def __init__(self, parent: QWidget | None = None, f: Qt.WindowType | None = None) -> None: ...
    @overload
    def __init__(self, parent: QWidget | None = None, caption: str | None = None, directory: str | None = None, filter: str | None = None) -> None: ...
    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.setOption(AdapterQFileDialog.Option.DontUseNativeDialog, True)  # noqa: FBT003
        self.setFileMode(AdapterQFileDialog.FileMode.Directory)
        self.setOption(AdapterQFileDialog.Option.ShowDirsOnly, False)  # noqa: FBT003
        self.ui: Ui_QFileDialogExtended = Ui_QFileDialogExtended()
        self.ui.setupUi(self)
        self.model_setup()
        self.executor: FileActionsExecutor = FileActionsExecutor()
        self.dispatcher: ActionsDispatcher = ActionsDispatcher(self.model, self, self.executor)
        self._setup_ribbons()
        self._setup_address_bar()
        self._setup_search_filter()
        self._insert_extended_rows()
        self._setup_proxy_model()
        self.connect_signals()
        self._connect_extended_signals()
        self.setMouseTracking(True)
        #self.installEventFilter(self)
        #self.ui.listView.installEventFilter(self)
        #self.ui.listView.setMouseTracking(True)
        #self.ui.listView.viewport().installEventFilter(self)
        #self.ui.listView.viewport().setMouseTracking(True)
        #self.ui.treeView.installEventFilter(self)
        #self.ui.treeView.setMouseTracking(True)
        #self.ui.treeView.viewport().installEventFilter(self)
        #self.ui.treeView.viewport().setMouseTracking(True)
        #self.ui.stackedWidget.installEventFilter(self)
        #self.ui.sidebar.installEventFilter(self)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        return super().eventFilter(obj, event)

    def print_widget_info(self, widget: QWidget) -> None:
        parent = widget.parent()
        assert parent is not None, f"{self.__class__.__name__}.print_widget_info: parent is None"
        RobustLogger().debug(
            "Widget info",
            extra={
                "class": widget.__class__.__name__,
                "objectName": widget.objectName(),
                "parentClass": None if parent is None else parent.__class__.__name__,
                "parentObjectName": None if parent is None else parent.objectName(),
            },
        )

    def _q_showListView(self) -> None:
        """Changes the current view to list mode.

        This provides users with a different way to visualize the file system contents.

        If this function is removed, users would lose the ability to switch to list view,
        limiting the flexibility of the file dialog's interface.
        """
        assert self.ui is not None, f"{self.__class__.__name__}._q_showListView: No UI setup."
        self.ui.listModeButton.setDown(True)
        self.ui.detailModeButton.setDown(False)
        self.ui.treeView.hide()
        self.ui.listView.show()
        parent = self.ui.listView.parent()
        assert parent is self.ui.page, f"{self.__class__.__name__}._q_showListView: parent is not self.ui.page"
        self.ui.stackedWidget.setCurrentWidget(cast("QWidget", parent))
        self.setViewMode(AdapterQFileDialog.ViewMode.List)

    def _q_showDetailsView(self) -> None:
        """Changes the current view to details mode.

        This provides users with a more detailed view of file system contents.

        If this function is removed, users would lose the ability to switch to details view,
        limiting the flexibility of the file dialog's interface.
        """
        self.ui.listModeButton.setDown(False)
        self.ui.detailModeButton.setDown(True)
        self.ui.listView.hide()
        self.ui.treeView.show()
        parent = cast("QWidget", self.ui.treeView.parent())
        assert parent is self.ui.page_2, f"{self.__class__.__name__}._q_showDetailsView: parent is not self.ui.page"
        self.ui.stackedWidget.setCurrentWidget(cast("QWidget", parent))
        self.setViewMode(AdapterQFileDialog.ViewMode.Detail)

    def override_ui(self):

        # Replace treeView
        self.ui.stackedWidget.__class__ = DynamicStackedView
        DynamicStackedView.__init__(
            cast("DynamicStackedView", self.ui.stackedWidget),
            self.ui.frame,
            [self.ui.page, self.ui.page_2],
            should_call_qt_init=False,
        )
        self.ui.treeView.__class__ = RobustTreeView
        assert isinstance(self.ui.treeView, RobustTreeView)
        RobustTreeView.__init__(self.ui.treeView, self.ui.page_2, should_call_qt_init=False)
        cast("RobustTreeView", self.ui.treeView).setParent(self.ui.page_2)
        cast("RobustTreeView", self.ui.treeView).setObjectName("treeView")
        cast("RobustTreeView", self.ui.treeView).setModel(self.model)
        self.ui.vboxlayout2.update()

        self.ui.listModeButton.clicked.connect(self._q_showListView)
        self.ui.detailModeButton.clicked.connect(self._q_showDetailsView)

    def currentView(self) -> QAbstractItemView | None:
        assert self.ui is not None, f"{self.__class__.__name__}.currentView: UI is None"
        assert self.ui.stackedWidget is not None, f"{self.__class__.__name__}.currentView: stackedWidget is None"
        if isinstance(self.ui.stackedWidget, DynamicStackedView):
            return self.ui.stackedWidget.current_view()
        # vanilla logic.
        if self.ui.stackedWidget.currentWidget() == self.ui.listView.parent():
            return self.ui.listView
        return self.ui.treeView

    def mapToSource(self, index: QModelIndex) -> QModelIndex:
        proxy_model_lookup = self.proxyModel()
        assert proxy_model_lookup is not None, f"{self.__class__.__name__}.mapToSource: proxy_model_lookup is None"
        return index if proxy_model_lookup is None else proxy_model_lookup.mapToSource(index)

    def _q_showContextMenu(self, position: QPoint) -> None:
        assert self.ui is not None, f"{self.__class__.__name__}._q_showContextMenu: No UI setup."
        assert self.model is not None, f"{self.__class__.__name__}._q_showContextMenu: No file system model setup."

        view: QAbstractItemView | None = self.currentView()
        assert view is not None, f"{self.__class__.__name__}._q_showContextMenu: No view found."

        index = view.indexAt(position)
        index = self.mapToSource(index.sibling(index.row(), 0))

        index = view.indexAt(position)
        if not index.isValid():
            view.clearSelection()
        menu = self.dispatcher.get_context_menu(view, position)
        menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)  # noqa: FBT003
        viewport = view.viewport()
        assert viewport is not None, f"{self.__class__.__name__}._q_showContextMenu: viewport is None"
        menu.exec(viewport.mapToGlobal(position))

    def model_setup(self):
        fs_model: QAbstractItemModel | None = self.ui.treeView.model()  # same as self.listView.model()
        assert fs_model is not None, f"{self.__class__.__name__}.model_setup: fs_model is None"
        assert isinstance(fs_model, QFileSystemModel), f"{self.__class__.__name__}.model_setup: fs_model is not a QFileSystemModel"
        assert fs_model is self.ui.listView.model(), f"{self.__class__.__name__}.model_setup: QFileSystemModel in treeView differs from listView's model?"
        self.model: QFileSystemModel = cast("QFileSystemModel", fs_model)

    def connect_signals(self):
        self.ui.treeView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.listView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        def show_context_menu(pos: QPoint, view: QListView | QTreeView):
            index = view.indexAt(pos)
            if not index.isValid():
                view.clearSelection()
            menu = self.dispatcher.get_context_menu(view, pos)
            if menu is not None:
                viewport = view.viewport()
                assert viewport is not None, f"{self.__class__.__name__}._q_showContextMenu: viewport is None"
                menu.exec(viewport.mapToGlobal(pos))

        self.ui.treeView.customContextMenuRequested.disconnect()
        self.ui.listView.customContextMenuRequested.disconnect()
        self.ui.treeView.customContextMenuRequested.connect(lambda pos: show_context_menu(pos, self.ui.treeView))
        self.ui.listView.customContextMenuRequested.connect(lambda pos: show_context_menu(pos, self.ui.listView))
        self.ui.treeView.doubleClicked.connect(self.dispatcher.on_open)

    def on_task_failed(self, task_id: str, error: Exception):
        RobustLogger().exception(f"Task {task_id} failed", exc_info=error)
        error_msg = QMessageBox()
        error_msg.setIcon(QMessageBox.Icon.Critical)
        error_msg.setText(f"Task {task_id} failed")
        error_msg.setInformativeText(str(error))
        error_msg.setDetailedText("".join(traceback.format_exception(type(error), error, None)))
        error_msg.setWindowTitle("Task Failed")
        error_msg.exec()

    def _setup_address_bar(self) -> None:
        from utility.ui_libraries.qt.common.filesystem.address_bar import RobustAddressBar

        self.address_bar: RobustAddressBar = RobustAddressBar(self)
        self.address_bar.setObjectName("addressBar")
        self.address_bar.pathChanged.connect(self._on_address_bar_path_changed)
        self.address_bar.returnPressed.connect(self._on_address_bar_return_pressed)
        self.address_bar.update_path(Path(self.directory().absolutePath()))

    def _setup_search_filter(self) -> None:
        from utility.ui_libraries.qt.widgets.widgets.search_filter import SearchFilterWidget

        self.search_filter: SearchFilterWidget = SearchFilterWidget(self)
        self.search_filter.setObjectName("searchFilter")
        self.search_filter.textChanged.connect(self._on_search_text_changed)
        self.search_filter.searchRequested.connect(self._on_search_requested)

    def _setup_ribbons(self) -> None:
        """Set up ribbons UI, sharing the same actions/menus as the dispatcher."""
        self.ribbons: RibbonsWidget = RibbonsWidget(
            self,
            menus=self.dispatcher.menus,
            columns_callback=self.dispatcher.show_set_default_columns_dialog,
        )
        self.ribbons.setObjectName("ribbonsWidget")

    def _insert_extended_rows(self) -> None:
        """Insert address bar + search above existing grid content."""
        grid = self.ui.gridlayout
        if grid is None:
            return

        # Store all existing items with their positions
        items_data: list[tuple[int, int, int, int, object]] = []
        for i in range(grid.count()):
            item = grid.itemAt(i)
            if item is None:
                continue
            row, col, row_span, col_span = grid.getItemPosition(i)
            assert row is not None, f"{self.__class__.__name__}._insert_extended_rows: row is None"
            assert col is not None, f"{self.__class__.__name__}._insert_extended_rows: col is None"
            assert row_span is not None, f"{self.__class__.__name__}._insert_extended_rows: row_span is None"
            assert col_span is not None, f"{self.__class__.__name__}._insert_extended_rows: col_span is None"
            items_data.append((row, col, row_span, col_span, item))

        # Remove all items from grid (but keep widgets as children)
        while grid.count() > 0:
            item = grid.takeAt(0)
            if item is None:
                break

        # Add extended components first: ribbon, address bar, search
        grid.addWidget(self.ribbons, 0, 0, 1, 3)
        grid.addWidget(self.address_bar, 1, 0, 1, 3)
        grid.addWidget(self.search_filter, 2, 0, 1, 3)

        # Re-add all original items with row offset +3
        for row, col, row_span, col_span, item in items_data:
            assert item is not None, f"{self.__class__.__name__}._insert_extended_rows: item is None"
            assert isinstance(item, QLayoutItem), f"{self.__class__.__name__}._insert_extended_rows: item is not a QLayoutItem"
            widget = item.widget()
            if widget is not None:
                grid.addWidget(widget, row + 3, col, row_span, col_span)
            else:
                layout = item.layout()
                if layout is not None:
                    grid.addLayout(layout, row + 3, col, row_span, col_span)

    def _setup_proxy_model(self) -> None:
        from qtpy.QtCore import QSortFilterProxyModel

        self.proxy_model: QSortFilterProxyModel = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(0)
        self.proxy_model.setRecursiveFilteringEnabled(True)

        self.ui.listView.setModel(self.proxy_model)
        self.ui.treeView.setModel(self.proxy_model)

    def _on_address_bar_path_changed(self, path: Path) -> None:
        self.setDirectory(str(path))

    def _on_address_bar_return_pressed(self) -> None:
        pass

    def _on_search_text_changed(self, text: str) -> None:
        self.proxy_model.setFilterFixedString(text)

    def _on_search_requested(self, text: str) -> None:
        self.proxy_model.setFilterFixedString(text)

    def _on_directory_changed(self, directory: str) -> None:
        self.address_bar.update_path(Path(directory))

    def _connect_extended_signals(self) -> None:
        self.directoryEntered.connect(self._on_directory_changed)

    @overload
    def setDirectory(self, directory: str | None) -> None: ...
    @overload
    def setDirectory(self, adirectory: QDir) -> None: ...
    def setDirectory(self, directory) -> None:  # type: ignore[override]
        super().setDirectory(directory)
        if hasattr(self, "address_bar"):
            self.address_bar.update_path(Path(self.directory().absolutePath()))

    def setDirectoryUrl(self, directory: QUrl) -> None:
        super().setDirectoryUrl(directory)
        if hasattr(self, "address_bar"):
            self.address_bar.update_path(Path(self.directory().absolutePath()))

    # 1:1 wrappers matching QtWidgets.pyi (2645-2771)
    @staticmethod
    def saveFileContent(fileContent, fileNameHint: str | None = None, parent: QWidget | None = None) -> None:  # noqa: N803
        if parent is None:
            AdapterQFileDialog.saveFileContent(fileContent, fileNameHint)
        else:
            AdapterQFileDialog.saveFileContent(fileContent, fileNameHint, parent)

    def selectedMimeTypeFilter(self) -> str:
        return super().selectedMimeTypeFilter()

    def supportedSchemes(self) -> list[str]:
        return list(super().supportedSchemes())

    def setSupportedSchemes(self, schemes: Iterable[str | None]) -> None:
        super().setSupportedSchemes(schemes)

    @staticmethod
    def getSaveFileUrl(parent: QWidget | None = None, caption: str | None = None, directory: QUrl = QUrl(), filter: str | None = None, initialFilter: str | None = None, options: AdapterQFileDialog.Option = AdapterQFileDialog.Option.DontUseNativeDialog, supportedSchemes: Iterable[str | None] = ()) -> tuple[QUrl, str]:  # noqa: E501
        return AdapterQFileDialog.getSaveFileUrl(parent, caption, directory, filter, initialFilter, options, supportedSchemes)

    @staticmethod
    def getOpenFileUrls(parent: QWidget | None = None, caption: str | None = None, directory: QUrl = QUrl(), filter: str | None = None, initialFilter: str | None = None, options: AdapterQFileDialog.Option = AdapterQFileDialog.Option.DontUseNativeDialog, supportedSchemes: Iterable[str | None] = ()) -> tuple[list[QUrl], str]:  # noqa: E501
        return AdapterQFileDialog.getOpenFileUrls(parent, caption, directory, filter, initialFilter, options, supportedSchemes)

    @staticmethod
    def getOpenFileUrl(parent: QWidget | None = None, caption: str | None = None, directory: QUrl = QUrl(), filter: str | None = None, initialFilter: str | None = None, options: AdapterQFileDialog.Option = AdapterQFileDialog.Option.DontUseNativeDialog, supportedSchemes: Iterable[str | None] = ()) -> tuple[QUrl, str]:  # noqa: E501
        return AdapterQFileDialog.getOpenFileUrl(parent, caption, directory, filter, initialFilter, options, supportedSchemes)

    def selectMimeTypeFilter(self, filter: str | None) -> None:  # noqa: A002
        super().selectMimeTypeFilter(filter)

    def mimeTypeFilters(self) -> list[str]:
        return list(super().mimeTypeFilters())

    def setMimeTypeFilters(self, filters: Iterable[str | None]) -> None:
        super().setMimeTypeFilters(filters)

    def selectedUrls(self) -> list[QUrl]:
        return list(super().selectedUrls())

    def selectUrl(self, url: QUrl) -> None:
        super().selectUrl(url)

    def directoryUrl(self) -> QUrl:
        return super().directoryUrl()

    def setVisible(self, visible: bool) -> None:
        super().setVisible(visible)

    def open(self, slot=None) -> None:  # noqa: ANN001
        if slot is None:
            super().open()
        else:
            super().open(slot)

    def options(self) -> AdapterQFileDialog.Option:
        return super().options()

    def setOptions(self, options: AdapterQFileDialog.Option) -> None:
        super().setOptions(options)

    def testOption(self, option: AdapterQFileDialog.Option) -> bool:
        return super().testOption(option)

    def setOption(self, option: AdapterQFileDialog.Option, on: bool = True) -> None:
        super().setOption(option, on)

    def setFilter(self, filters: QDir.Filters) -> None:
        super().setFilter(filters)

    def filter(self) -> QDir.Filters:
        return super().filter()

    def selectedNameFilter(self) -> str:
        return super().selectedNameFilter()

    def selectNameFilter(self, filter: str | None) -> None:  # noqa: A002
        super().selectNameFilter(filter)

    def nameFilters(self) -> list[str]:
        return list(super().nameFilters())

    def setNameFilters(self, filters: Iterable[str | None]) -> None:
        super().setNameFilters(filters)

    def setNameFilter(self, filter: str | None) -> None:  # noqa: A002
        super().setNameFilter(filter)

    def proxyModel(self):  # type: ignore[override]
        return super().proxyModel()

    def setProxyModel(self, model) -> None:  # type: ignore[override]
        super().setProxyModel(model)

    def restoreState(self, state: QByteArray | bytes | bytearray | memoryview) -> bool:
        return super().restoreState(state)

    def saveState(self) -> QByteArray:
        return super().saveState()

    def sidebarUrls(self) -> list[QUrl]:
        return list(super().sidebarUrls())

    def setSidebarUrls(self, urls: Iterable[QUrl]) -> None:
        super().setSidebarUrls(urls)

    def changeEvent(self, e: QEvent | None) -> None:  # noqa: N803
        super().changeEvent(e)

    def accept(self) -> None:
        super().accept()

    def done(self, result: int) -> None:
        super().done(result)

    @staticmethod
    def getSaveFileName(parent: QWidget | None = None, caption: str | None = None, directory: str | None = None, filter: str | None = None, initialFilter: str | None = None, options: AdapterQFileDialog.Option = AdapterQFileDialog.Option.DontUseNativeDialog) -> tuple[str, str]:  # noqa: E501
        return AdapterQFileDialog.getSaveFileName(parent, caption, directory, filter, initialFilter, options)

    @staticmethod
    def getOpenFileNames(parent: QWidget | None = None, caption: str | None = None, directory: str | None = None, filter: str | None = None, initialFilter: str | None = None, options: AdapterQFileDialog.Option = AdapterQFileDialog.Option.DontUseNativeDialog) -> tuple[list[str], str]:  # noqa: E501
        return AdapterQFileDialog.getOpenFileNames(parent, caption, directory, filter, initialFilter, options)

    @staticmethod
    def getOpenFileName(parent: QWidget | None = None, caption: str | None = None, directory: str | None = None, filter: str | None = None, initialFilter: str | None = None, options: AdapterQFileDialog.Option = AdapterQFileDialog.Option.DontUseNativeDialog) -> tuple[str, str]:  # noqa: E501
        return AdapterQFileDialog.getOpenFileName(parent, caption, directory, filter, initialFilter, options)

    @staticmethod
    def getExistingDirectoryUrl(parent: QWidget | None = None, caption: str | None = None, directory: QUrl = QUrl(), options: AdapterQFileDialog.Option = AdapterQFileDialog.Option.DontUseNativeDialog, supportedSchemes: Iterable[str | None] = ()) -> QUrl:  # noqa: E501
        return AdapterQFileDialog.getExistingDirectoryUrl(parent, caption, directory, options, supportedSchemes)

    @staticmethod
    def getExistingDirectory(parent: QWidget | None = None, caption: str | None = None, directory: str | None = None, options: AdapterQFileDialog.Option = AdapterQFileDialog.Option.DontUseNativeDialog) -> str:  # noqa: E501
        return AdapterQFileDialog.getExistingDirectory(parent, caption, directory, options)

    def labelText(self, label: AdapterQFileDialog.DialogLabel) -> str:
        return super().labelText(label)

    def setLabelText(self, label: AdapterQFileDialog.DialogLabel, text: str | None) -> None:
        super().setLabelText(label, text)

    def iconProvider(self):
        return super().iconProvider()

    def setIconProvider(self, provider) -> None:
        super().setIconProvider(provider)

    def itemDelegate(self):
        return super().itemDelegate()

    def setItemDelegate(self, delegate) -> None:
        super().setItemDelegate(delegate)

    def history(self) -> list[str]:
        return list(super().history())

    def setHistory(self, paths: Iterable[str | None]) -> None:
        super().setHistory(paths)

    def defaultSuffix(self) -> str:
        return super().defaultSuffix()

    def setDefaultSuffix(self, suffix: str | None) -> None:
        super().setDefaultSuffix(suffix)

    def acceptMode(self) -> AdapterQFileDialog.AcceptMode:
        return super().acceptMode()

    def setAcceptMode(self, mode: AdapterQFileDialog.AcceptMode) -> None:
        super().setAcceptMode(mode)

    def fileMode(self) -> AdapterQFileDialog.FileMode:
        return super().fileMode()

    def setFileMode(self, mode: AdapterQFileDialog.FileMode) -> None:
        super().setFileMode(mode)

    def viewMode(self) -> AdapterQFileDialog.ViewMode:
        return super().viewMode()

    def setViewMode(self, mode: AdapterQFileDialog.ViewMode) -> None:
        super().setViewMode(mode)

    def selectedFiles(self) -> list[str]:
        return list(super().selectedFiles())

    def selectFile(self, filename: str | None) -> None:
        super().selectFile(filename)

    def directory(self) -> QDir:
        return super().directory()



if __name__ == "__main__":
    import faulthandler
    import sys
    import traceback
    faulthandler.enable()

    app = QApplication(sys.argv)

    file_dialog = QFileDialogExtended(None, Qt.WindowType.Window)
    file_dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)  # noqa: FBT003
    file_dialog.setFileMode(QFileDialog.FileMode.Directory)
    file_dialog.setOption(QFileDialog.Option.ShowDirsOnly, False)  # noqa: FBT003
    file_dialog.override_ui()

    file_dialog.resize(800, 600)
    file_dialog.show()

    sys.exit(app.exec())
