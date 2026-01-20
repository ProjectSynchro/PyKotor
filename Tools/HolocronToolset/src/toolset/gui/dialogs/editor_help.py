from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import markdown

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog  # , QTextBrowser, QVBoxLayout

from pykotor.tools.encoding import decode_bytes_with_fallbacks
from toolset.gui.common.palette_helpers import wrap_html_with_palette_styles
from utility.system.os_helper import is_frozen

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


def get_wiki_path() -> tuple[Path, Path | None]:
    """Get the path to the wiki directory.

    Returns:
        Path to wiki directory, checking both frozen and development locations.
    """
    if is_frozen():
        # When frozen, wiki should be bundled in the same directory as the executable
        import sys

        exe_path = Path(sys.executable).parent
        wiki_path = exe_path / "wiki"
        if wiki_path.exists():
            return wiki_path, None

    # Development mode: check toolset/wiki first, then root wiki
    path1 = Path("./wiki")
    toolset_wiki = Path(__file__).parents[2] / "wiki"
    if toolset_wiki.exists():
        path1 = toolset_wiki

    path2 = None
    root_wiki = Path(__file__).parents[6] / "wiki"
    if root_wiki.exists():
        path2 = root_wiki

    # Fallback
    return path1, path2


class EditorHelpDialog(QDialog):
    """Non-blocking dialog for displaying editor help documentation from wiki markdown files."""

    def __init__(self, parent: QWidget | None, wiki_filename: str):
        """Initialize the help dialog.

        Args:
            parent: Parent widget
            wiki_filename: Name of the markdown file in the wiki directory (e.g., "GFF-File-Format.md")
        """
        super().__init__(parent)
        from toolset.gui.common.localization import trf

        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowMinMaxButtonsHint & ~Qt.WindowType.WindowContextHelpButtonHint)
        from toolset.uic.qtpy.dialogs.editor_help import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle(trf("Help - {filename}", filename=wiki_filename))

        # Set search paths for relative links
        toolset_wiki_path, root_wiki_path = get_wiki_path()
        search_paths = [str(toolset_wiki_path)]
        if root_wiki_path is not None:
            search_paths.append(str(root_wiki_path))
        self.ui.textBrowser.setSearchPaths(search_paths)

        # Load and display the markdown file
        self.load_wiki_file(wiki_filename)

        # Setup event filter to prevent scroll wheel interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter

        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

    def load_wiki_file(self, wiki_filename: str) -> None:
        """Load and render a markdown file from the wiki directory.

        Args:
            wiki_filename: Name of the markdown file (e.g., "GFF-File-Format.md")
        """
        toolset_wiki_path, root_wiki_path = get_wiki_path()
        file_path = toolset_wiki_path / wiki_filename
        if not file_path.exists():
            assert root_wiki_path is not None
            file_path = root_wiki_path / wiki_filename

        if not file_path.exists():
            from toolset.gui.common.localization import translate as tr, trf

            error_body = f"""
            <h1>{tr("Help File Not Found")}</h1>
            <p>{trf("Could not find help file: <code>{filename}</code>", filename=wiki_filename)}</p>
            <p>{trf("Expected location: <code>{path}</code>", path=str(file_path))}</p>
            <p>{trf("Wiki path: <code>{path}</code>", path=str(toolset_wiki_path))}</p>
            <p>{trf("Root wiki path: <code>{path}</code>", path=str(root_wiki_path))}</p>
            <p>{trf("Expected file: <code>{path}</code>", path=str(file_path))}</p>
            """
            error_html = wrap_html_with_palette_styles(error_body, self)
            self.ui.textBrowser.setHtml(error_html)
            return

        try:
            text: str = decode_bytes_with_fallbacks(file_path.read_bytes())
            html_body: str = markdown.markdown(text, extensions=["tables", "fenced_code", "codehilite", "toc"])
            html: str = wrap_html_with_palette_styles(html_body, self)
            self.ui.textBrowser.setHtml(html)
        except Exception as e:
            error_body = f"""
            <h1>Error Loading Help File</h1>
            <p>Could not load help file: <code>{wiki_filename}</code></p>
            <p>Error: {e.__class__.__name__}: {str(e)}</p>
            """
            error_html = wrap_html_with_palette_styles(error_body, self)
            self.ui.textBrowser.setHtml(error_html)
