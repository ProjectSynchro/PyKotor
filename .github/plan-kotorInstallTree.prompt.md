## Plan: Tree-based KOTOR installations explorer

Draft plan to replace the install combobox with a tree-driven explorer backed by `KotorFileSystemModel`, using existing robust views. This focuses on mapping the current UI/model touchpoints, redesigning the model for multi-root + archive expansion, then rewiring the UI and tests to the new tree navigation, while preserving zoom/icon behaviors and path-based display.

### Steps 4

1. Review `RobustTreeView` and `RobustTableView` capabilities and zoom/icon behaviors in [Libraries/Utility/src/utility/gui/qt/widgets/itemviews/treeview.py](Libraries/Utility/src/utility/gui/qt/widgets/itemviews/treeview.py) and [Libraries/Utility/src/utility/gui/qt/widgets/itemviews/tableview.py](Libraries/Utility/src/utility/gui/qt/widgets/itemviews/tableview.py) to confirm integration expectations for `RobustTreeView` and `RobustTableView`.
2. Locate and redesign `KotorFileSystemModel` to support multiple root installations, archive-as-folder nodes, and stable indexes; align its API to `QAbstractItemModel`/`QFileSystemModel` contracts and ensure path round‑tripping (file location to be confirmed, model must expose `index()`, `parent()`, `rowCount()`, `data()`).
3. Replace the installation combobox with a tree-based primary navigator using `RobustTreeView` and wire selection/expansion to detail panes, taking cues from existing tree UI patterns in [Tools/HolocronToolset/src/toolset/gui/common/widgets/tree.py](Tools/HolocronToolset/src/toolset/gui/common/widgets/tree.py) and ensuring path-based display in the “Core” view.
4. Update tests: create exhaustive `KotorFileSystemModel` unit tests mirroring Qt file model behavior, and rewrite UI tests to verify top-level installation nodes, archive expansion, and zoom/icon sizing with `RobustTreeView`/`RobustTableView` (test file locations to be confirmed once identified).

### Further Considerations 2

1. Which existing tabs should remain as contextual views vs fully integrated into the tree? Option A: keep “Core” as a right‑hand detail pane; Option B: convert tabs to filters; Option C: remove tabs entirely.
2. Please confirm the exact location of `KotorFileSystemModel` and the current installation combobox UI file so the plan can cite concrete files and symbols.

Share any corrections (especially file locations) and preferred tab strategy, and I’ll refine the plan.
