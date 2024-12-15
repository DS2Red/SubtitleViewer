import PyInstaller.__main__
import sys
import os

# Get the directory containing the script
script_dir = os.path.dirname(os.path.abspath(__file__))

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
]) 