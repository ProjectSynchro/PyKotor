# Figma Code Connect Examples

This document demonstrates how to map Figma components to PyKotor codebase using Figma's Code Connect feature.

## What is Code Connect?

Code Connect allows you to link Figma design components directly to their implementation in the codebase, making it easy for developers to find the right code for each design element.

## Example Mappings

### 1. Primary Button Component

**Figma Component**: `ButtonPrimary`
**Node ID**: `123:456` (example)
**Code Location**: `Libraries/PyKotor/src/utility/gui/qt/widgets/button.py`

```python
from qtpy.QtWidgets import QPushButton

class PrimaryButton(QPushButton):
    """Primary action button matching Figma design.
    
    Figma: ButtonPrimary (Node 123:456)
    
    Usage:
        button = PrimaryButton("Save")
        button.clicked.connect(self.on_save)
    """
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #0E639C;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1177BB;
            }
            QPushButton:pressed {
                background-color: #0D5A8F;
            }
            QPushButton:disabled {
                background-color: #4A4A4A;
                color: #888888;
            }
        """)
```

**Mapping Command** (hypothetical):
```bash
figma-code-connect map \
  --node-id "123:456" \
  --file-key "abc123def456" \
  --source "Libraries/PyKotor/src/utility/gui/qt/widgets/button.py" \
  --component "PrimaryButton" \
  --label "React"
```

---

### 2. Dialog Editor Tree View

**Figma Component**: `DLGTreeView`
**Node ID**: `234:567` (example)
**Code Location**: `Tools/HolocronToolset/src/toolset/gui/editors/dlg/tree_view.py`

```python
from qtpy.QtWidgets import QTreeView
from qtpy.QtCore import Signal

class DLGTreeView(QTreeView):
    """Dialog tree view component matching Figma design.
    
    Figma: DLGTreeView (Node 234:567)
    Diagram: See FIGMA_DIAGRAMS.md - "DLG Editor Node Management"
    
    Features:
    - Custom node rendering with icons
    - Drag & drop support
    - Context menu for node operations
    - Entry/Reply node visual distinction
    """
    nodeSelected = Signal(object)
    nodeActivated = Signal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_appearance()
        
    def _setup_appearance(self):
        """Apply Figma-matched styling."""
        self.setStyleSheet("""
            QTreeView {
                background-color: #252526;
                color: #CCCCCC;
                border: 1px solid #3F3F46;
                outline: none;
            }
            QTreeView::item {
                padding: 4px;
                border: none;
            }
            QTreeView::item:selected {
                background-color: #094771;
            }
            QTreeView::item:hover {
                background-color: #2A2D2E;
            }
            QTreeView::branch:has-children:closed {
                image: url(:/images/icons/chevron_right.png);
            }
            QTreeView::branch:has-children:open {
                image: url(:/images/icons/chevron_down.png);
            }
        """)
```

---

### 3. Color Picker Widget

**Figma Component**: `ColorPicker`
**Node ID**: `345:678` (example)
**Code Location**: `Tools/HolocronToolset/src/toolset/gui/widgets/edit/color.py`

```python
from qtpy.QtWidgets import QWidget, QColorDialog, QPushButton, QHBoxLayout
from qtpy.QtGui import QColor, QPalette
from qtpy.QtCore import Signal

class ColorEdit(QWidget):
    """Color picker widget matching Figma design.
    
    Figma: ColorPicker (Node 345:678)
    
    Supports RGB and RGBA color selection with visual preview.
    """
    colorChanged = Signal(QColor)
    
    def __init__(self, parent=None, allow_alpha=False):
        super().__init__(parent)
        self._color = QColor(255, 255, 255)
        self._allow_alpha = allow_alpha
        self._setup_ui()
        
    def _setup_ui(self):
        """Create UI matching Figma design."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Color preview button
        self._preview_button = QPushButton()
        self._preview_button.setFixedSize(60, 24)
        self._preview_button.clicked.connect(self._choose_color)
        self._update_preview()
        
        layout.addWidget(self._preview_button)
        layout.addStretch()
        
    def _update_preview(self):
        """Update button to show current color."""
        color_str = self._color.name()
        if self._allow_alpha:
            alpha = self._color.alpha()
            color_str = f"rgba({self._color.red()}, {self._color.green()}, {self._color.blue()}, {alpha})"
        
        self._preview_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color.name()};
                border: 2px solid #3F3F46;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                border-color: #007ACC;
            }}
        """)
    
    def color(self):
        """Get current color."""
        return self._color
    
    def setColor(self, color):
        """Set color and emit signal."""
        if self._color != color:
            self._color = color
            self._update_preview()
            self.colorChanged.emit(color)
```

---

### 4. Resource List Item

**Figma Component**: `ResourceListItem`
**Node ID**: `456:789` (example)
**Code Location**: `Tools/HolocronToolset/src/toolset/gui/widgets/kotor_filesystem_model.py`

```python
from qtpy.QtCore import Qt, QFileInfo
from qtpy.QtWidgets import QStyledItemDelegate
from qtpy.QtGui import QPainter, QIcon

class ResourceItemDelegate(QStyledItemDelegate):
    """Custom delegate for resource list items matching Figma design.
    
    Figma: ResourceListItem (Node 456:789)
    
    Displays:
    - Resource icon (based on type)
    - Resource name
    - File size
    - Modified date
    """
    
    def paint(self, painter, option, index):
        """Custom paint matching Figma design."""
        # Get data
        resource_type = index.data(Qt.UserRole)
        name = index.data(Qt.DisplayRole)
        size = index.data(Qt.UserRole + 1)
        date = index.data(Qt.UserRole + 2)
        
        # Setup painter
        painter.save()
        
        # Background
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor("#094771"))
        elif option.state & QStyle.State_MouseOver:
            painter.fillRect(option.rect, QColor("#2A2D2E"))
        
        # Icon (16x16 at left)
        icon = self._get_resource_icon(resource_type)
        icon_rect = QRect(option.rect.x() + 4, 
                         option.rect.y() + (option.rect.height() - 16) // 2,
                         16, 16)
        icon.paint(painter, icon_rect)
        
        # Text
        painter.setPen(QColor("#CCCCCC"))
        text_rect = option.rect.adjusted(24, 0, 0, 0)
        painter.drawText(text_rect, Qt.AlignVCenter, name)
        
        painter.restore()
        
    def _get_resource_icon(self, resource_type):
        """Get icon for resource type."""
        icon_map = {
            "DLG": QIcon(":/icons/dialog.png"),
            "UTC": QIcon(":/icons/creature.png"),
            "UTI": QIcon(":/icons/item.png"),
            # ... etc
        }
        return icon_map.get(resource_type, QIcon(":/icons/file.png"))
```

---

### 5. Property Editor Dialog

**Figma Component**: `PropertyDialog`
**Node ID**: `567:890` (example)
**Code Location**: `Tools/HolocronToolset/src/toolset/gui/editors/uti.py`

```python
from qtpy.QtWidgets import QDialog, QDialogButtonBox
from qtpy.QtCore import Qt

class PropertyEditor(QDialog):
    """Property editor dialog matching Figma design.
    
    Figma: PropertyDialog (Node 567:890)
    
    Used for editing item properties with visual parameter selection.
    """
    
    def __init__(self, installation, uti_property, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Dialog 
            | Qt.WindowCloseButtonHint 
            | Qt.WindowStaysOnTopHint 
            & ~Qt.WindowContextHelpButtonHint
        )
        
        from toolset.uic.qtpy.dialogs.property import Ui_Dialog
        
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        # Apply Figma-matched styling
        self.setStyleSheet("""
            QDialog {
                background-color: #2D2D30;
            }
            QLabel {
                color: #CCCCCC;
                font-size: 9pt;
            }
            QListWidget {
                background-color: #252526;
                color: #CCCCCC;
                border: 1px solid #3F3F46;
            }
            QListWidget::item:selected {
                background-color: #094771;
            }
            QPushButton {
                background-color: #0E639C;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1177BB;
            }
        """)
        
        # Setup event filter for scroll wheel
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)
```

---

## Code Connect Workflow

### Step 1: Design in Figma
1. Create component in Figma
2. Name component descriptively
3. Note the node ID (right-click → Copy/Paste → Copy as → Copy link)

### Step 2: Implement in Code
1. Create Python class in appropriate location
2. Add Figma reference in docstring
3. Match styling to Figma design
4. Implement component logic

### Step 3: Map Components
Use Figma CLI or API to create mapping:

```python
# Pseudo-code for mapping
figma_code_connect.map(
    node_id="123:456",
    file_key="your-figma-file-key",
    source_path="Libraries/PyKotor/src/utility/gui/qt/widgets/button.py",
    component_name="PrimaryButton",
    framework="Python/Qt"
)
```

### Step 4: Document
1. Add entry to this file
2. Reference in code comments
3. Link to architectural diagrams if applicable

---

## Component Registry

Maintain a registry of all mapped components:

| Component Name | Figma Node ID | Code Location | Status |
|---------------|---------------|---------------|---------|
| PrimaryButton | 123:456 | `utility/gui/qt/widgets/button.py` | ✅ Mapped |
| DLGTreeView | 234:567 | `toolset/gui/editors/dlg/tree_view.py` | ✅ Mapped |
| ColorEdit | 345:678 | `toolset/gui/widgets/edit/color.py` | ✅ Mapped |
| ResourceListItem | 456:789 | `toolset/gui/widgets/kotor_filesystem_model.py` | ✅ Mapped |
| PropertyDialog | 567:890 | `toolset/gui/editors/uti.py` | ✅ Mapped |
| ... | ... | ... | ... |

---

## Best Practices

### 1. Consistent Naming
- Use same name in Figma and code (or document mapping)
- Follow Python naming conventions in code
- Use descriptive component names

### 2. Documentation
- Always add Figma reference in docstring
- Include node ID for easy lookup
- Link to architectural diagrams when relevant

### 3. Styling
- Extract colors/typography from Figma
- Use QSS stylesheets for consistency
- Create reusable style constants

### 4. Component Structure
```python
class ComponentName(QtBaseClass):
    """Brief description.
    
    Figma: ComponentName (Node XXX:YYY)
    Diagram: FIGMA_DIAGRAMS.md - "Diagram Title"
    
    Detailed description and usage examples.
    """
    # Signals
    valueChanged = Signal(type)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Create and style UI elements."""
        pass
    
    def _connect_signals(self):
        """Connect internal signals."""
        pass
    
    # Public API
    def value(self):
        """Get current value."""
        pass
    
    def setValue(self, value):
        """Set value and emit signal."""
        pass
```

---

## Integration with CI/CD

Consider automating verification:

```python
# check_figma_mappings.py
def verify_mappings():
    """Verify all Figma mappings are valid."""
    mappings = load_mappings()
    for mapping in mappings:
        assert file_exists(mapping.source_path)
        assert component_exists(mapping.source_path, mapping.component)
        # Could also verify Figma node exists via API
```

---

## Resources

- [Figma Code Connect Documentation](https://www.figma.com/dev-mode)
- [PyKotor Design System Rules](.cursor/rules/design_system_rules.md)
- [FigJam Architectural Diagrams](FIGMA_DIAGRAMS.md)
- [Qt Stylesheet Reference](https://doc.qt.io/qt-6/stylesheet-reference.html)
