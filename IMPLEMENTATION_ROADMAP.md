# PyKotor Holocron Toolset - Full Implementation Roadmap

**Date Created:** February 2, 2026  
**Current Status:** 70% Complete  
**Focus:** SDK-style GUI enhancements and completion of core features

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Implementation Status](#current-implementation-status)
3. [Phase Breakdown](#phase-breakdown)
4. [Detailed Task List](#detailed-task-list)
5. [Technical Integration Points](#technical-integration-points)
6. [Risk Assessment](#risk-assessment)
7. [Success Criteria](#success-criteria)

---

## Executive Summary

The Holocron Toolset main window is a professionally-architected SDK-style file browser with 70% feature completion. The remaining work involves:

- **6 incomplete features** totaling ~150 lines of code
- **3 quick-win improvements** (<50 lines each)
- **Clear implementation patterns** already established in codebase
- **All necessary utilities and dialogs** already built and operational

**Estimated completion:** 8–12 hours of focused development  
**Risk level:** Low (incremental improvements on stable foundation)

---

## Current Implementation Status

### ✅ Fully Completed Features (70%)

| Feature | Status | Evidence |
|---------|--------|----------|
| **UI Layout** | 100% | Three-panel SDK-style interface (Project Tree \| Asset Views \| Inspector) |
| **Asset Views** | 100% | Tree, List, Grid, Table modes with proxy filtering |
| **Search/Filter** | 100% | Advanced query parsing (ext:, type:, name:, path:) |
| **File Operations** | 90% | Extract, Duplicate, Delete, Copy/Cut, Show in Explorer, Copy Path |
| **Asset Preview** | 100% | TPC/TGA image preview with real-time scaling, dependency viewer for MDL/MDX |
| **Reference Search** | 100% | Async reference finder with options dialog and results window |
| **Command Palette** | 100% | SDK-style action search with 20+ commands |
| **Drag & Drop** | 100% | Import external files into asset browser with target directory resolution |
| **Thumbnails** | 100% | TPC/TGA thumbnail icons in file system model with LRU cache |
| **File Watcher** | 100% | Detects installation changes with debounced refresh |
| **Status Bar** | 100% | Selection counter and status messages |
| **Context Menus** | 100% | Tree and asset view context menus with keyboard shortcut indicators |
| **Localization** | 100% | Full tr() support for internationalization |

### ⚠️ Partially Completed Features (20%)

| Feature | Completion | Missing Piece | File:Line |
|---------|-----------|---------------|-----------|
| **Favorites/Bookmarks** | 50% | "Go To" navigation (find and select resource) | main.py:2154 |
| **Batch Operations** | 60% | Execute loop implementations for Extract/Duplicate/Delete | main.py:2289–2301 |
| **Paste Operation** | 50% | Move operation for Cut/Paste workflow | main.py:1636 |

### ❌ Not Started Features (10%)

| Feature | Purpose | File:Line | Complexity |
|---------|---------|-----------|-----------|
| **Asset Rename** | Rename resources in Override folder | main.py:1666 | Low |
| **Open With Dialog** | Show associated editors/handlers for resource type | main.py:2100 | Medium |
| **Resource Creation** | Create new resources (new 2DA, TPC, NCS, etc.) | main.py:1297 | High |
| **Save Current Asset** | Write changes from external editor back to installation | main.py:1593 | High |

---

## Phase Breakdown

### Phase 1: Quick Wins (30 minutes total)
**Goal:** Implement 3 small features to establish momentum

- [ ] **Favorites Navigation** (15 min)
  - Locate bookmarked resource by name
  - Scroll asset view to selected resource
  - Clear status "No matching favorite found" message

- [ ] **Signal Emission Refactor** (5 min)
  - kotor_filesystem_model.py:901: Emit signal instead of direct method call
  - Minor architectural improvement (low priority)

- [ ] **Status Bar Favorite Indicator** (10 min)
  - Show current resource favorite status in status bar
  - Update when selection changes

### Phase 2: Core Functionality (4–5 hours total)
**Goal:** Complete essential file operations and batch workflows

- [ ] **Asset Rename** (30 min)
  - Validate new name (no duplicates in same directory)
  - Handle file extension preservation
  - Update model after rename

- [ ] **Move Operation (Cut/Paste)** (60 min)
  - Implement move file logic
  - Handle collision detection
  - Update model and UI
  - Constraint: Override folder only

- [ ] **Batch Operations Execution** (90 min)
  - Extract All: Loop through selected, reuse extract progress dialog
  - Duplicate All to Override: Loop duplicate logic, handle collisions
  - Delete All: Loop delete logic with confirmation
  - Progress tracking for each batch operation
  - Summary dialog showing results

- [ ] **Batch Rename with Pattern** (60 min)
  - Show pattern dialog (e.g., "old_*.tpc" → "new_*.tpc")
  - Validate pattern matches resources
  - Execute renames with collision handling
  - Preview before executing

### Phase 3: Advanced Features (4–6 hours total)
**Goal:** Implement remaining SDK-style features

- [ ] **Open With Dialog** (120 min)
  - Build editor registry (map resource type → list of editors)
  - Show dialog with available editors for selected resource
  - Launch chosen editor via `open_resource_editor()`
  - Handle custom/user-defined editors

- [ ] **Resource Creation** (180+ min)
  - Type selector dialog (2DA, TPC, NCS, GFX, UTI, UTE, etc.)
  - Template selector (if applicable, e.g., 2DA layouts)
  - Resource builder/generator per type
  - Place in Override folder with naming collision handling
  - Open in associated editor after creation

- [ ] **Save Current Asset** (Variable, architecture-dependent)
  - Implement editor state tracking system
  - Listen for editor close/save signals
  - Write changed resource back to installation
  - Update model and preview
  - **Prerequisite:** Resolve editor integration architecture

- [ ] **Advanced Batch Operations** (60 min)
  - Convert Format (e.g., all TGA → TPC)
  - Export to Directory with structure preservation
  - Copy with pattern (e.g., copy matching files to new folder)

---

## Detailed Task List

### PHASE 1: Quick Wins

#### Task 1.1: Favorites Navigation
**File:** `Tools/HolocronToolset/src/toolset/gui/windows/main.py:2154`  
**Current Code:** `_show_bookmarks()` shows dialog with bookmarked resources but TODO on navigation  

**Steps:**
1. Get selected item from bookmarks dialog (already shows list)
2. Call `_navigate_to_resource(resource_path)` helper
3. Scroll asset view to show resource
4. Highlight/select the resource in current view
5. Update status bar: "Navigated to: <resource_name>"

**Reuse:** Navigation pattern exists in `_update_breadcrumb()` (lines 1068–1093)

**Test:** 
- Create 3 bookmarks
- Select one from bookmarks dialog
- Verify asset view navigates to it
- Verify status bar shows navigation message

---

#### Task 1.2: Emit Signal for Address Bar
**File:** `Tools/HolocronToolset/src/toolset/gui/widgets/kotor_filesystem_model.py:901`  
**Current Code:** Directly updates address bar via `self.parent()._update_breadcrumb()`

**Steps:**
1. Define `address_changed` signal in `KotorFileSystemModel`
2. Emit signal instead of direct parent call
3. Connect signal in main window
4. Remove direct parent reference

**Rationale:** Architectural cleanliness; emit signal instead of tight coupling

---

#### Task 1.3: Status Bar Favorite Indicator
**File:** `Tools/HolocronToolset/src/toolset/gui/windows/main.py` (in selection update handler)  
**Current Code:** Selection updates call `_update_status_bar()` with item count

**Steps:**
1. In `_update_status_bar()`, check if selected resource is in favorites
2. Append star icon or "★ Bookmarked" label if true
3. Show in status bar alongside item count
4. Update on selection change

---

### PHASE 2: Core Functionality

#### Task 2.1: Asset Rename
**File:** `Tools/HolocronToolset/src/toolset/gui/windows/main.py:1666`  
**Current Code:** Gets user input, shows confirmation, but has `pass` statement

**Steps:**
1. Get old name and new name (from dialog already in code)
2. Determine resource path (file system path or capsule entry)
3. **Validation:**
   - Check no duplicate with new name in same directory
   - Preserve file extension
   - Check writable location (Override only)
4. **Execute rename:**
   - File operations: `shutil.move()` or `resource.rename()`
   - For capsule entries: use `HTInstallation.rename_file()`
5. **Update model:**
   - Refresh tree node or full refresh
   - Re-select renamed resource
6. **Status bar:** Show "Renamed X to Y"

**Reuse:** 
- File operations pattern from extract/duplicate
- Collision handling from `_duplicate_assets()` (lines 987–1054)

**Error handling:**
- File already exists → prompt overwrite or new name
- Permission denied → show error dialog
- Read-only location → prevent and show warning

---

#### Task 2.2: Move Operation (Cut/Paste)
**File:** `Tools/HolocronToolset/src/toolset/gui/windows/main.py:1636`  
**Current Code:** Cut operation fills clipboard, paste has `pass` statement for move

**Steps:**
1. In `_paste_assets()`, detect move vs copy (clipboard operation type)
2. **For move operation:**
   - Source must be in Override (constraint)
   - Destination must be valid (folder or default override)
   - Call move helper: `self._move_resources(sources, destination)`
3. **Implement move helper:**
   - Loop through resources
   - Check collision (file exists at destination)
   - Move file: `shutil.move(src, dst)`
   - Update internal capsule if needed
   - Track success/fail
4. **Update model:**
   - Remove from source in tree
   - Add to destination in tree
   - Refresh both parent nodes
5. **Clear clipboard after successful move**
6. **Status bar:** "Moved N items to <location>"

**Reuse:** 
- Duplicate logic (lines 1017–1054) as template
- Delete logic (lines 1124–1175) for source removal
- Collision handling (lines 1033–1040)

**Constraint:** Only allow move from Override folder (add validation)

**Test:**
- Move resource within Override
- Move resource to different Override subfolder
- Try move from Core → fail with error
- Try move to read-only location → fail with error

---

#### Task 2.3: Batch Operations Execution
**File:** `Tools/HolocronToolset/src/toolset/gui/windows/main.py:2289–2301`  
**Current Code:** Operation selection dropdown and progress dialog, but execute loop has `pass` stubs

**Steps:**
1. **For Extract All:**
   - Loop through selected resources
   - Call `_extract_assets([resource])` for each
   - Accumulate progress (count extracted)
   - Show progress dialog with cancel button
   - On completion: "Extracted N items to C:\..."

2. **For Duplicate All to Override:**
   - Loop through selected resources
   - Call `_duplicate_assets([resource])` for each
   - Handle collision prompt once (apply to all / per item)
   - Track duplicated count
   - Final status: "Duplicated N items"

3. **For Delete All:**
   - Show confirmation: "Delete N items permanently?"
   - Loop through selected resources
   - Call `_delete_assets([resource])` for each
   - Track deleted count
   - Status: "Deleted N items"

4. **Progress tracking:**
   - Reuse existing progress dialog (lines 2237–2261)
   - Update with current item: "Extracting... (5/15)"
   - Show cancel button for long operations
   - Show summary on completion

**Reuse:**
- `_extract_assets()` method body (lines 890–955)
- `_duplicate_assets()` method body (lines 987–1054)
- `_delete_assets()` method body (lines 1124–1175)
- Progress dialog pattern (lines 2237–2261)

**Error handling:**
- Skip errors but continue batch (log to result summary)
- Final dialog shows: "Successfully processed N, errors: M"
- If all fail: show error instead

---

#### Task 2.4: Batch Rename with Pattern
**File:** `Tools/HolocronToolset/src/toolset/gui/windows/main.py` (add new method + wire to batch ops)  
**Current Code:** None (new feature)

**Steps:**
1. **Create pattern dialog:**
   - Show 2 fields: "Find pattern", "Replace pattern"
   - Support wildcards: `*` (any text), `?` (any char)
   - Example: `old_*.tpc` → `new_*.tpc`
   - Preview: "5 items will be renamed"

2. **Implement pattern matching:**
   - Parse patterns (convert glob to regex)
   - Match against resource names
   - Generate new names (replace matched groups)
   - Build rename pairs list

3. **Validation:**
   - Check no collisions (2 resources → same new name)
   - Check all matches valid (no duplicates)
   - Warn if no matches found

4. **Execute renames:**
   - Loop through pairs
   - Call rename operation per item
   - Track success/fail
   - Show summary: "Renamed N items"

5. **Add to batch operations dropdown:**
   - Add "Rename with Pattern" option
   - Show pattern dialog when selected

**Test:**
- Rename all `texture_*.tpc` → `char_*.tpc`
- Rename all `old_?.nss` → `new_?.nss`
- Verify collision detection
- Verify status message

---

### PHASE 3: Advanced Features

#### Task 3.1: Open With Dialog
**File:** `Tools/HolocronToolset/src/toolset/gui/windows/main.py:2100`  
**Current Code:** TODO comment, placeholder message

**Steps:**
1. **Build editor registry:**
   - Map resource type (2DA, NCS, TPC, etc.) → list of editor classes
   - Hardcoded mappings:
     - `ResourceType.TPC` → [TextureEditor, ExternalViewer]
     - `ResourceType.NCS` → [ScriptEditor, HexEditor]
     - `ResourceType.TWO_DA` → [TableEditor, TextEditor]
     - `ResourceType.DLG` → [DialogEditor, TextEditor]
     - Etc. (see existing `open_resource_editor()` for all types)

2. **Create "Open With" dialog:**
   - Show selected resource name
   - List available editors as radio buttons or dropdown
   - Show description per editor (e.g., "Texture Editor - Full editing", "External Viewer - Read-only preview")
   - Options: "Always use this editor" checkbox (save preference)
   - Buttons: Open, Cancel

3. **Execute open:**
   - Get selected editor
   - Call `open_resource_editor(resource, editor_type)`
   - Close dialog
   - Status bar: "Opened in <EditorName>"

4. **Wire to UI:**
   - Add "Open With..." to context menu (when resource type has multiple editors)
   - Add to command palette
   - Add keyboard shortcut (e.g., Ctrl+Alt+O)

5. **Preference persistence:**
   - Store "last used editor per type" in settings
   - Default to most-recently-used if available

**Reuse:**
- Dialog pattern from `_show_dependencies()` (lines 2075–2100)
- Editor invocation from `open_resource_editor()` (already hardcoded)
- Settings persistence: `SettingsProvider`

**Test:**
- Right-click TPC → "Open With..." → shows texture editor + external viewer
- Right-click NCS → "Open With..." → shows script + hex editor
- Select editor → opens correctly
- Check that preference is saved and reused

---

#### Task 3.2: Resource Creation
**File:** `Tools/HolocronToolset/src/toolset/gui/windows/main.py:1297`  
**Current Code:** Shows info dialog only, TODO comment

**Steps:**
1. **Create resource type selector dialog:**
   - List all supported types:
     - 2DA (table)
     - NCS (script)
     - TPC (texture)
     - TGA (texture)
     - MDL/MDX (model)
     - DLG (dialog)
     - GFX (flash)
     - UTI/UTE/UTS/etc. (game object templates)
   - Show icon + description per type
   - Allow search/filter by type

2. **Template/Configuration per type:**
   - **2DA:** Show layout selector (columns, default values)
   - **NCS:** Show script template (empty, function skeleton, etc.)
   - **TPC:** Show color/dimensions dialog
   - **TGA:** Import image or create blank
   - **MDL/MDX:** Show skeleton dialog (humanoid, creature, etc.)
   - **DLG:** Show dialog structure template
   - **UTI/UTE/etc:** Show property defaults

3. **Name and location:**
   - Prompt for resource name (validate: no duplicates in Override)
   - Default location: Override folder
   - Show full path before creating

4. **Create resource:**
   - Use PyKotor resource builders/empty constructors
   - Write to Override folder
   - Add to file system model
   - Optional: Open in associated editor immediately

5. **Wire to UI:**
   - Context menu on Override folder → "Create New..."
   - Command palette: "Create New Resource"
   - Keyboard shortcut (e.g., Ctrl+N)

**Reuse:**
- Dialog patterns from existing feature dialogs
- File writing from extract/duplicate operations
- Model refresh from `_refresh_tree()` (lines 687–693)

**Blockers:**
- Need resource builder classes (check if PyKotor has them, else create minimal wrappers)
- Need template system for each type

**Test:**
- Create 2DA in Override → verify appears in tree
- Create NCS → open in script editor → verify blank script
- Create TPC → open in texture editor
- Try create in Core → should prevent or warn

---

#### Task 3.3: Save Current Asset
**File:** `Tools/HolocronToolset/src/toolset/gui/windows/main.py:1593`  
**Current Code:** `pass` statement only

**Steps:**
1. **Architecture decision:** How to track active editor?
   - Option A: Central editor registry (dict: resource → editor widget)
   - Option B: Editor signals back to main window on save
   - Option C: Main window polls open windows for changes
   - **Recommended:** Option B (least invasive)

2. **Implement editor tracking:**
   - Define `resource_modified(resource, data)` signal in editor classes
   - Connect all opened editors to main window's `_on_resource_modified()`
   - Main window maintains dict: `{resource_id: (resource, data, editor)}`

3. **Implement save operation:**
   - Get current/selected resource (track which editor is "active")
   - Retrieve data from editor
   - Write to installation: `self.installation.write_resource(resource, data)`
   - Update model (mark resource modified in UI)
   - Status bar: "Saved <ResourceName>"

4. **Handle conflicts:**
   - If resource changed externally → prompt overwrite or reload
   - If save fails → show error dialog

5. **Wire to UI:**
   - Make "Save Current Asset" functional (currently shows placeholder)
   - Add keyboard shortcut: Ctrl+S
   - Context menu option on edited resources

**Blockers:**
- Need to understand how editors are opened (external process? Qt widget embedded?)
- May require significant refactoring if editors are external processes
- **Prerequisite:** Determine editor architecture (check if already tracked)

**Test:**
- Open resource in editor
- Modify it
- Press Ctrl+S
- Verify changes saved to installation
- Reload installation → changes persist

---

### PHASE 4: Polish & Validation (Not in main implementation)

#### Optional Enhancements:
- [ ] Recent files list in File menu
- [ ] Undo/Redo for operations (low priority)
- [ ] Drag-and-drop reordering in batch operations
- [ ] Favorites quick-access toolbar buttons
- [ ] Search history in filter box
- [ ] Keyboard shortcut customization dialog
- [ ] Backup before delete (with retention settings)
- [ ] Performance profiling for large installations

---

## Technical Integration Points

### Model & View Synchronization
**Pattern:** Whenever model is modified (rename, delete, create):
1. Update internal model data structure
2. Call `self._refresh_tree()` (full) or targeted refresh (efficient)
3. Re-select resource if needed
4. Update breadcrumb/status bar

### File System Changes
**Pattern:** File watcher detects changes → queues refresh → 500ms debounce → refresh tree

### Error Handling
**Pattern:** All file operations in try/except:
```python
try:
    # operation
except FileExistsError:
    # collision handling
except PermissionError:
    # show error dialog
except Exception as e:
    logger.error(...); show_error_dialog(...)
```

### Status Bar Updates
**Pattern:** All operations end with `self.ui.statusbar.showMessage(f"Status: {summary}")`

### Async Operations
**Pattern:** Long-running ops use `AsyncLoader`:
```python
self.async_loader.load(function, (args,), finished_callback)
```

### Resource Paths
**Internal:** `HTInstallation.get_file(resref, res_type)` → bytes  
**External:** File system path from `self._extract_path(resource)`  
**Capsule:** `CapsuleResource` references with internal paths

---

## Risk Assessment

### LOW RISK (Can implement immediately)
- ✅ Favorites navigation
- ✅ Batch operations execution (reuse existing logic)
- ✅ Asset rename (straightforward file op)
- ✅ Signal emission refactor
- ✅ Status bar enhancements

**Risk Factors:** None significant  
**Fallback:** Revert to previous behavior if issues arise

### MEDIUM RISK (Validate architecture first)
- ⚠️ Move operation (requires constraint enforcement)
- ⚠️ Open With dialog (need editor registry design)
- ⚠️ Batch rename pattern (regex/glob complexity)

**Risk Factors:**
- Move: Could corrupt installation if constraints fail
- Open With: Editor list might be incomplete
- Batch rename: Pattern matching edge cases

**Mitigation:** 
- Add comprehensive validation before any file operation
- Test with small dataset first
- Log all operations for audit trail

### HIGH RISK (Requires upfront research)
- 🔴 Resource creation (depends on PyKotor resource builders)
- 🔴 Save current asset (depends on editor architecture)

**Risk Factors:**
- Resource builders might not exist in PyKotor
- Editor architecture undefined (external processes vs embedded)
- Potential major refactoring needed

**Mitigation:**
- Research PyKotor resource building capabilities first
- Spike on editor integration architecture
- May defer to future release if blockers found

---

## Success Criteria

### Phase 1 Success (Quick Wins)
- [ ] Favorites navigation works end-to-end
- [ ] Status bar shows favorite indicator
- [ ] All 3 features have passing manual tests
- [ ] No compile errors or warnings

### Phase 2 Success (Core Functionality)
- [ ] Asset rename works with collision detection
- [ ] Move operation restricted to Override, no data loss
- [ ] Batch operations show progress and complete successfully
- [ ] Batch rename with pattern handles edge cases
- [ ] All operations update UI and status bar correctly
- [ ] No regressions in existing features

### Phase 3 Success (Advanced Features)
- [ ] Open With dialog shows appropriate editors
- [ ] Resource creation produces valid resources in Override
- [ ] Save Current Asset writes data correctly back to installation
- [ ] All features persist preferences
- [ ] Comprehensive error messages for all failure modes

### Overall Success Criteria
- [ ] **No compile errors:** `ruff check`, `mypy`, `pylint` all pass
- [ ] **Manual testing:** All 10+ features tested with both happy and error paths
- [ ] **Regression testing:** Existing features still work (5-10 spot checks)
- [ ] **Documentation:** Code comments explain any non-obvious logic
- [ ] **Git hygiene:** One commit per feature with clear messages

---

## Implementation Timeline Estimate

| Phase | Tasks | Estimated Time | Actual |
|-------|-------|-----------------|--------|
| Phase 1 | Quick wins (3 features) | 30 min | — |
| Phase 2 | Core functionality (4 features) | 4–5 hours | — |
| Phase 3 | Advanced features (3 features) | 6–8 hours | — |
| Testing | Manual validation + debugging | 1–2 hours | — |
| **TOTAL** | **10 features** | **11.5–15.5 hours** | — |

**Parallelization:** Some tasks can overlap (e.g., researching resource builders while implementing Phase 1).

---

## Notes for Implementation

### Code Quality Expectations
1. **Follow existing patterns:** All new code should match established style in main.py
2. **Type hints:** Use type hints for method signatures
3. **Docstrings:** Add docstrings explaining intent and non-obvious logic
4. **Comments:** Explain why, not what (code is self-documenting)
5. **Error messages:** User-friendly, actionable messages for all errors

### Testing Strategy
1. **Per-task testing:** Manual test after each task before moving to next
2. **Regression spots:** After each phase, check 2-3 existing features still work
3. **Edge cases:** Test collision detection, empty selections, read-only constraints
4. **Error paths:** Intentionally trigger errors (missing files, permission denied, etc.)

### Git Commit Strategy
Per PyKotor conventions:
- **One file at a time** (or tightly-related small group)
- **Clear message:** "Implement favorites navigation in main window"
- **Reference file changed:** `Tools/HolocronToolset/src/toolset/gui/windows/main.py`
- **Never use `git add .` or `-A` flags**

### Reference Materials
- Existing patterns in main.py (extract, duplicate, delete operations)
- kotor_filesystem_model.py for model refresh patterns
- PyKotor resource API (ResourceType, HTInstallation, file operations)
- Qt documentation for dialogs, signals, and event handling

---

## Future Enhancements (Post-Completion)

After Phase 3 completes, consider:

1. **Advanced Search** (v2.0)
   - Search resource contents (2DA column values, NCS function names, etc.)
   - Save searches as filters
   - Full-text indexing for large installations

2. **Batch Conversion Tools**
   - Convert all TGA → TPC with settings
   - Convert all NCS → decompiled text
   - Bulk export with directory structure preservation

3. **Installation Compare**
   - Compare two installations side-by-side
   - Show differences (missing files, modified files)
   - Merge installations

4. **Resource Viewer Enhancements**
   - 3D model preview (use PyGLM)
   - Audio playback
   - Dialog tree visualization
   - Script decompilation with syntax highlighting

5. **Performance Optimization**
   - Lazy-load large installations
   - Parallel file extraction/batch operations
   - Incremental model updates instead of full refresh

---

## Document Metadata

**Version:** 1.0  
**Last Updated:** February 2, 2026  
**Author:** AI Coding Agent  
**Status:** Ready for Implementation  
**Approval:** Pending User Review

---

## Appendix: Code References

### Key Files
- **Main Implementation:** `Tools/HolocronToolset/src/toolset/gui/windows/main.py` (2,572 lines)
- **Model:** `Tools/HolocronToolset/src/toolset/gui/widgets/kotor_filesystem_model.py` (1,329 lines)
- **Backend:** `Libraries/PyKotor/src/pykotor/tools/model.py`, `reference_finder.py`

### Method Cross-References

#### File Operations (Reusable Templates)
- `_extract_assets()` - lines 890–955
- `_duplicate_assets()` - lines 987–1054
- `_delete_assets()` - lines 1124–1175

#### UI Patterns (Reusable)
- Progress dialog - lines 2237–2261
- Dialog creation - multiple examples
- Context menu building - lines 1196–1295

#### Navigation (Reusable)
- `_navigate_to_directory()` - lines 689–710
- `_update_breadcrumb()` - lines 1068–1093
- `_sync_tree_with_asset_view()` - lines 734–770

---

**End of Roadmap**
