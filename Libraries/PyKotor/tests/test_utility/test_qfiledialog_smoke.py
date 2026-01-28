"""Quick smoke test to verify basic QFileDialogExtended functionality."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ["QT_API"] = "PyQt5"
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["PYKOTOR_DISABLE_MULTIPROCESSING"] = "1"

from qtpy.QtWidgets import QApplication
from qtpy.QtTest import QTest

from utility.ui_libraries.qt.filesystem.qfiledialogextended.qfiledialogextended import QFileDialogExtended
from utility.ui_libraries.qt.adapters.filesystem.qfiledialog.qfiledialog import QFileDialog as AdapterQFileDialog


def test_basic_creation():
    """Test that we can create and destroy a dialog quickly."""
    app = QApplication.instance() or QApplication([])
    
    print("Creating dialog...")
    dialog = QFileDialogExtended()
    print("Dialog created")
    
    assert dialog is not None
    assert dialog.testOption(AdapterQFileDialog.Option.DontUseNativeDialog)
    
    print("Closing dialog...")
    dialog.close()
    dialog.deleteLater()
    print("Dialog closed")
    
    QTest.qWait(10)
    print("Test passed!")


if __name__ == "__main__":
    test_basic_creation()
