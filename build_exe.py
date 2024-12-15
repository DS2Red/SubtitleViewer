import PyInstaller.__main__
import sys
import os
from PyQt6 import QtCore

# Get the directory containing the script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Get PyQt6 directory for additional binaries
qt_path = os.path.dirname(QtCore.__file__)

PyInstaller.__main__.run([
    'subtitle_reader.py',
    '--onefile',
    '--windowed',
    '--name=SubtitleViewer',
    '--icon=app_icon.ico',  # Optional: Add this line if you have an icon
    '--add-data=LICENSE;.',  # Optional: Include license file
    '--clean',
    f'--workpath={os.path.join(script_dir, "build")}',
    f'--distpath={os.path.join(script_dir, "dist")}',
    '--hidden-import=PyQt6.QtCore',
    '--hidden-import=PyQt6.QtGui',
    '--hidden-import=PyQt6.QtWidgets',
    f'--paths={qt_path}',
    '--collect-all=PyQt6',
]) 