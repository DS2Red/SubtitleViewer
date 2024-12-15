import PyInstaller.__main__
import sys
import os
from PyQt6 import QtCore
from PyQt6.QtCore import QLibraryInfo

# Get the directory containing the script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Get PyQt6 directory for additional binaries
qt_path = os.path.dirname(QtCore.__file__)
qt_binaries = QLibraryInfo.path(QLibraryInfo.LibraryPath.BinariesPath)

# Remove icon if it doesn't exist
icon_path = os.path.join(script_dir, 'app_icon.ico')
icon_option = ['--icon=' + icon_path] if os.path.exists(icon_path) else []

# Basic command
command = [
    'subtitle_reader.py',
    '--onedir',
    '--windowed',
    '--name=SubtitleViewer',
    '--clean',
    f'--workpath={os.path.join(script_dir, "build")}',
    f'--distpath={os.path.join(script_dir, "dist")}',
    '--hidden-import=PyQt6.QtCore',
    '--hidden-import=PyQt6.QtGui',
    '--hidden-import=PyQt6.QtWidgets',
    '--hidden-import=_ctypes',
    '--hidden-import=win32api',
    f'--paths={qt_path}',
    f'--path={qt_binaries}',
    '--collect-all=PyQt6',
    # Add specific Qt plugins we need
    '--add-data=%s;.' % os.path.join(qt_binaries, '*'),
]

# Add icon if it exists
command.extend(icon_option)

# Add license if it exists
if os.path.exists('LICENSE'):
    command.append('--add-data=LICENSE;.')

# Run PyInstaller
PyInstaller.__main__.run(command) 