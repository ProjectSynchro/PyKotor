"""Editor for module info (IFO) files."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QMessageBox

from pykotor.common.misc import ResRef
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.ifo import IFO, dismantle_ifo, read_ifo
from pykotor.resource.type import ResourceType
from toolset.gui.common.filters import NoScrollEventFilter
from toolset.gui.common.localization import translate as tr
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from toolset.data.installation import HTInstallation


class IFOEditor(Editor):
    """Editor for module info (IFO) files."""

    def __init__(self, parent=None, installation: HTInstallation | None = None):
        """Initialize the IFO editor."""
        supported = [ResourceType.IFO]
        super().__init__(parent, "Module Info Editor", "ifo", supported, supported, installation)

        self.ifo: IFO | None = None

        # Load UI from .ui file
        from toolset.uic.qtpy.editors.ifo import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._setup_menus()
        self._add_help_action()
        self._setup_signals()

        # Setup event filter to prevent scroll wheel interaction with controls
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        # Setup reference search for script fields
        if installation is not None:
            self._setup_installation(installation)

        # Convert entry direction from radians (as stored) to degrees (as displayed)
        self.ui.entryDirectionSpin.setRange(0.0, 360.0)

    def _setup_signals(self):
        """Connect UI signals to handler methods."""
        # Basic info fields
        self.ui.tagEdit.textChanged.connect(self.on_value_changed)
        self.ui.tagGenerateButton.clicked.connect(self.generate_tag)
        self.ui.voIdEdit.textChanged.connect(self.on_value_changed)
        self.ui.hakEdit.textChanged.connect(self.on_value_changed)
        self.ui.creatorIdSpin.valueChanged.connect(self.on_value_changed)
        self.ui.versionSpin.valueChanged.connect(self.on_value_changed)

        # Module name and description - connect to editing finished signal
        if hasattr(self.ui, "modNameEdit"):
            self.ui.modNameEdit.sig_editing_finished.connect(self.on_mod_name_changed)
        if hasattr(self.ui, "descriptionEdit"):
            self.ui.descriptionEdit.sig_editing_finished.connect(self.on_description_changed)

        # Entry point fields
        self.ui.entryAreaEdit.textChanged.connect(self.on_value_changed)
        self.ui.entryXSpin.valueChanged.connect(self.on_value_changed)
        self.ui.entryYSpin.valueChanged.connect(self.on_value_changed)
        self.ui.entryZSpin.valueChanged.connect(self.on_value_changed)
        self.ui.entryDirectionSpin.valueChanged.connect(self.on_entry_direction_changed)

        # Time settings (deprecated but still supported)
        self.ui.dawnHourSpin.valueChanged.connect(self.on_value_changed)
        self.ui.duskHourSpin.valueChanged.connect(self.on_value_changed)
        self.ui.timeScaleSpin.valueChanged.connect(self.on_value_changed)
        self.ui.startMonthSpin.valueChanged.connect(self.on_value_changed)
        self.ui.startDaySpin.valueChanged.connect(self.on_value_changed)
        self.ui.startHourSpin.valueChanged.connect(self.on_value_changed)
        self.ui.startYearSpin.valueChanged.connect(self.on_value_changed)
        self.ui.xpScaleSpin.valueChanged.connect(self.on_value_changed)

        # Script fields - map UI names to IFO attribute names
        self._script_field_mapping = {
            "onHeartbeatEdit": "on_heartbeat",
            "onLoadEdit": "on_load",
            "onStartEdit": "on_start",
            "onEnterEdit": "on_enter",
            "onLeaveEdit": "on_leave",
            "onActivateItemEdit": "on_activate_item",
            "onAcquireItemEdit": "on_acquire_item",
            "onUnacquireItemEdit": "on_unacquire_item",
            "onPlayerDeathEdit": "on_player_death",
            "onPlayerDyingEdit": "on_player_dying",
            "onPlayerLevelupEdit": "on_player_levelup",
            "onPlayerRespawnEdit": "on_player_respawn",
            "onUserDefinedEdit": "on_user_defined",
            "onPlayerRestEdit": "on_player_rest",
            "startMovieEdit": "start_movie",
        }

        for ui_name, ifo_attr in self._script_field_mapping.items():
            if hasattr(self.ui, ui_name):
                widget = getattr(self.ui, ui_name)
                if hasattr(widget, "currentTextChanged"):
                    widget.currentTextChanged.connect(self.on_value_changed)
                elif hasattr(widget, "textChanged"):
                    widget.textChanged.connect(self.on_value_changed)

        # Advanced settings
        if hasattr(self.ui, "expansionPackSpin"):
            self.ui.expansionPackSpin.valueChanged.connect(self.on_value_changed)
        if hasattr(self.ui, "minGameVerEdit"):
            self.ui.minGameVerEdit.textChanged.connect(self.on_value_changed)
        if hasattr(self.ui, "cacheNSSDataCheck"):
            self.ui.cacheNSSDataCheck.stateChanged.connect(self.on_value_changed)

        # Area list management (if implemented)
        if hasattr(self.ui, "addAreaButton"):
            self.ui.addAreaButton.clicked.connect(self.add_area)
        if hasattr(self.ui, "removeAreaButton"):
            self.ui.removeAreaButton.clicked.connect(self.remove_area)

    def _setup_installation(self, installation: HTInstallation):
        """Setup installation-specific features."""
        # Setup localized string editors
        if hasattr(self.ui, "modNameEdit"):
            self.ui.modNameEdit.set_installation(installation)
        if hasattr(self.ui, "descriptionEdit"):
            self.ui.descriptionEdit.set_installation(installation)

        # Setup script field context menus and reference search
        script_field_names = [
            "onHeartbeatEdit",
            "onLoadEdit",
            "onStartEdit",
            "onEnterEdit",
            "onLeaveEdit",
            "onActivateItemEdit",
            "onAcquireItemEdit",
            "onUnacquireItemEdit",
            "onPlayerDeathEdit",
            "onPlayerDyingEdit",
            "onPlayerLevelupEdit",
            "onPlayerRespawnEdit",
            "onUserDefinedEdit",
            "onPlayerRestEdit",
            "startMovieEdit",
        ]
        
        script_fields = [getattr(self.ui, name, None) for name in script_field_names]
        
        for field in script_fields:
            if field is not None:
                installation.setup_file_context_menu(
                    field,
                    [ResourceType.NSS, ResourceType.NCS],
                    enable_reference_search=True,
                    reference_search_type="script",
                )
                tooltip = field.toolTip() or ""
                if "Right-click" not in tooltip:
                    field.setToolTip(
                        tr("Right-click to find references to this script in the installation.")
                        if not tooltip
                        else f"{tooltip}\n\n{tr('Right-click to find references to this script in the installation.')}",
                    )
                # Set maxLength for FilterComboBox script fields (ResRefs are max 16 characters)
                line_edit = field.lineEdit() if hasattr(field, "lineEdit") else None
                if line_edit is not None:
                    line_edit.setMaxLength(16)

        # Populate script combo boxes with available scripts
        relevant_scripts = sorted(
            iter(
                {
                    res.resname().lower()
                    for res in installation.get_relevant_resources(ResourceType.NCS, self._filepath)
                },
            ),
        )

        for ui_name in self._script_field_mapping.keys():
            if hasattr(self.ui, ui_name):
                widget = getattr(self.ui, ui_name)
                if hasattr(widget, "populate_combo_box"):
                    widget.populate_combo_box(relevant_scripts)
                elif hasattr(widget, "addItems"):
                    widget.clear()
                    widget.addItems([""] + relevant_scripts)

    def generate_tag(self):
        """Generate tag from module name/resref."""
        if not self.ifo:
            return

        # Try to generate tag from module name or resref
        if hasattr(self.ui, "modNameEdit"):
            locstring = self.ui.modNameEdit.locstring()
            if locstring and locstring.stringref != -1:
                # Try to get English text
                from pykotor.common.language import Language, Gender
                name = locstring.get(Language.ENGLISH, Gender.MALE) or ""
                if not name and self._installation:
                    name = self._installation.string(locstring) or ""
                if name:
                    # Generate tag from name (remove spaces, special chars)
                    tag = "".join(c.lower() if c.isalnum() else "_" for c in name[:32])
                    tag = tag.strip("_")
                    if tag and hasattr(self.ui, "tagEdit"):
                        self.ui.tagEdit.setText(tag)
                        return

        # Fallback to resref
        resref = self._resname
        if resref and hasattr(self.ui, "tagEdit"):
            self.ui.tagEdit.setText(resref.lower())

    def on_entry_direction_changed(self):
        """Handle entry direction changes, converting degrees to radians."""
        if not self.ifo:
            return

        # Convert degrees to radians
        degrees = self.ui.entryDirectionSpin.value()
        radians = degrees * 3.141592653589793 / 180.0
        self.ifo.entry_direction = radians
        self.on_value_changed()



    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes) -> None:
        """Load an IFO file."""
        super().load(filepath, resref, restype, data)
        self.ifo = read_ifo(data)
        self.update_ui_from_ifo()

    def build(self) -> tuple[bytes, bytes]:
        """Build IFO file data."""
        if not self.ifo:
            return b"", b""

        data = bytearray()
        write_gff(dismantle_ifo(self.ifo), data)
        return bytes(data), b""

    def new(self) -> None:
        """Create new IFO file."""
        super().new()
        self.ifo = IFO()
        self.update_ui_from_ifo()

    def update_ui_from_ifo(self) -> None:
        """Update UI elements from IFO data."""
        if not self.ifo or not self._installation:
            return

        # Basic Info
        if hasattr(self.ui, "modNameEdit"):
            self.ui.modNameEdit.set_locstring(self.ifo.mod_name)
        if hasattr(self.ui, "tagEdit"):
            self.ui.tagEdit.setText(self.ifo.tag)
        if hasattr(self.ui, "voIdEdit"):
            self.ui.voIdEdit.setText(self.ifo.vo_id)
        if hasattr(self.ui, "hakEdit"):
            self.ui.hakEdit.setText(self.ifo.hak)
        if hasattr(self.ui, "descriptionEdit"):
            self.ui.descriptionEdit.set_locstring(self.ifo.description)

        # Module ID (read-only, display as hex)
        if hasattr(self.ui, "modIdEdit"):
            mod_id_str = " ".join(f"{b:02x}" for b in self.ifo.mod_id[:16]) if self.ifo.mod_id else ""
            self.ui.modIdEdit.setText(mod_id_str)

        # Creator ID and Version (deprecated)
        if hasattr(self.ui, "creatorIdSpin"):
            self.ui.creatorIdSpin.setValue(self.ifo.creator_id)
        if hasattr(self.ui, "versionSpin"):
            self.ui.versionSpin.setValue(self.ifo.version)

        # Entry Point
        if hasattr(self.ui, "entryAreaEdit"):
            self.ui.entryAreaEdit.setText(str(self.ifo.resref))
        if hasattr(self.ui, "entryXSpin"):
            self.ui.entryXSpin.setValue(self.ifo.entry_position.x)
        if hasattr(self.ui, "entryYSpin"):
            self.ui.entryYSpin.setValue(self.ifo.entry_position.y)
        if hasattr(self.ui, "entryZSpin"):
            self.ui.entryZSpin.setValue(self.ifo.entry_position.z)

        # Convert radians to degrees for display
        if hasattr(self.ui, "entryDirectionSpin"):
            degrees = self.ifo.entry_direction * 180.0 / 3.141592653589793
            if degrees < 0:
                degrees += 360.0
            degrees = degrees % 360.0
            self.ui.entryDirectionSpin.setValue(degrees)

        # Area name (first area from list, read-only)
        if hasattr(self.ui, "areaNameEdit"):
            area_name = str(self.ifo.area_name) if hasattr(self.ifo, "area_name") else ""
            self.ui.areaNameEdit.setText(area_name)

        # Time Settings (deprecated)
        if hasattr(self.ui, "dawnHourSpin"):
            self.ui.dawnHourSpin.setValue(self.ifo.dawn_hour)
        if hasattr(self.ui, "duskHourSpin"):
            self.ui.duskHourSpin.setValue(self.ifo.dusk_hour)
        if hasattr(self.ui, "timeScaleSpin"):
            self.ui.timeScaleSpin.setValue(self.ifo.time_scale)
        if hasattr(self.ui, "startMonthSpin"):
            self.ui.startMonthSpin.setValue(self.ifo.start_month)
        if hasattr(self.ui, "startDaySpin"):
            self.ui.startDaySpin.setValue(self.ifo.start_day)
        if hasattr(self.ui, "startHourSpin"):
            self.ui.startHourSpin.setValue(self.ifo.start_hour)
        if hasattr(self.ui, "startYearSpin"):
            self.ui.startYearSpin.setValue(self.ifo.start_year)
        if hasattr(self.ui, "xpScaleSpin"):
            self.ui.xpScaleSpin.setValue(self.ifo.xp_scale)

        # Scripts - update from IFO attributes to UI widgets
        for ui_name, ifo_attr in self._script_field_mapping.items():
            if hasattr(self.ui, ui_name):
                widget = getattr(self.ui, ui_name)
                script_value = str(getattr(self.ifo, ifo_attr))
                if hasattr(widget, "setCurrentText"):
                    widget.setCurrentText(script_value)
                elif hasattr(widget, "setText"):
                    widget.setText(script_value)

        # Advanced settings
        if hasattr(self.ui, "expansionPackSpin"):
            self.ui.expansionPackSpin.setValue(self.ifo.expansion_id)
        if hasattr(self.ui, "minGameVerEdit"):
            # MinGameVer is not directly exposed in IFO class, may need to add it
            pass
        if hasattr(self.ui, "cacheNSSDataCheck"):
            # CacheNSSData is not directly exposed in IFO class, may need to add it
            pass
        if hasattr(self.ui, "isSaveGameCheck"):
            # IsSaveGame is read-only and managed by engine
            pass

    def on_value_changed(self) -> None:
        """Handle UI value changes."""
        if not self.ifo:
            return

        # Basic Info
        self.ifo.tag = self.ui.tagEdit.text()
        self.ifo.vo_id = self.ui.voIdEdit.text()
        self.ifo.hak = self.ui.hakEdit.text()

        # Creator ID and Version (deprecated)
        if hasattr(self.ui, "creatorIdSpin"):
            self.ifo.creator_id = self.ui.creatorIdSpin.value()
        if hasattr(self.ui, "versionSpin"):
            self.ifo.version = self.ui.versionSpin.value()

        # Entry Point
        try:
            self.ifo.resref = ResRef(self.ui.entryAreaEdit.text())
        except ResRef.ExceedsMaxLengthError:
            # Skip invalid ResRef values to prevent teardown errors
            pass

        self.ifo.entry_position.x = self.ui.entryXSpin.value()
        self.ifo.entry_position.y = self.ui.entryYSpin.value()
        self.ifo.entry_position.z = self.ui.entryZSpin.value()

        # Entry direction is handled by on_entry_direction_changed (degrees to radians conversion)

        # Time Settings (deprecated)
        self.ifo.dawn_hour = self.ui.dawnHourSpin.value()
        self.ifo.dusk_hour = self.ui.duskHourSpin.value()
        self.ifo.time_scale = self.ui.timeScaleSpin.value()
        self.ifo.start_month = self.ui.startMonthSpin.value()
        self.ifo.start_day = self.ui.startDaySpin.value()
        self.ifo.start_hour = self.ui.startHourSpin.value()
        self.ifo.start_year = self.ui.startYearSpin.value()
        self.ifo.xp_scale = self.ui.xpScaleSpin.value()

        # Scripts - update from UI widgets to IFO attributes
        for ui_name, ifo_attr in self._script_field_mapping.items():
            if hasattr(self.ui, ui_name):
                widget = getattr(self.ui, ui_name)
                try:
                    if hasattr(widget, "currentText"):
                        script_text = widget.currentText()
                    elif hasattr(widget, "text"):
                        script_text = widget.text()
                    else:
                        continue

                    if script_text:
                        setattr(self.ifo, ifo_attr, ResRef(script_text))
                    else:
                        setattr(self.ifo, ifo_attr, ResRef.from_blank())
                except ResRef.ExceedsMaxLengthError:
                    # Skip invalid ResRef values to prevent teardown errors
                    pass

        # Advanced settings
        if hasattr(self.ui, "expansionPackSpin"):
            self.ifo.expansion_id = self.ui.expansionPackSpin.value()

        self.signal_modified.emit()