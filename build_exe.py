"""
Registry File Manager - EXE Build Script
========================================

Erstellt eine ausführbare EXE-Datei mit PyInstaller
"""

import PyInstaller.__main__
import os
import shutil

# Projekt-Verzeichnis
project_dir = os.path.dirname(os.path.abspath(__file__))

# Aufräumen vorheriger Builds
for cleanup_dir in ['build', 'dist']:
    cleanup_path = os.path.join(project_dir, cleanup_dir)
    if os.path.exists(cleanup_path):
        print(f"Lösche alten Build-Ordner: {cleanup_path}")
        shutil.rmtree(cleanup_path)

# PyInstaller Argumente
pyinstaller_args = [
    'main.py',                                    # Hauptdatei
    '--name=RegistryManager',                      # Name der EXE
    '--onefile',                                   # Eine einzelne EXE-Datei
    '--windowed',                                  # Kein Konsolen-Fenster
    '--clean',                                     # Build-Cache löschen
    
    # Daten einbinden
    '--add-data=config;config',
    '--add-data=src;src',
    
    # Python-Module explizit einbinden
    '--hidden-import=tkinter',
    '--hidden-import=tkinter.ttk',
    '--hidden-import=tkinter.messagebox',
    '--hidden-import=tkinter.filedialog',
    '--hidden-import=winreg',
    '--hidden-import=logging',
    '--hidden-import=logging.handlers',
    '--hidden-import=json',
    '--hidden-import=pathlib',
    '--hidden-import=datetime',
    '--hidden-import=threading',
    '--hidden-import=subprocess',
    '--hidden-import=tempfile',
    '--hidden-import=shutil',
    '--hidden-import=re',
    '--hidden-import=sqlite3',
    '--hidden-import=_sqlite3',
    
    # Optimierungen
    '--optimize=2',                                # Python-Code optimieren
    
    # Arbeitsverzeichnis
    f'--workpath={os.path.join(project_dir, "build")}',
    f'--distpath={os.path.join(project_dir, "dist")}',
]

print("=" * 60)
print("Registry File Manager - EXE-Erstellung")
print("=" * 60)
print(f"Projekt-Verzeichnis: {project_dir}")
print(f"Build startet...")
print("=" * 60)

# PyInstaller ausführen
PyInstaller.__main__.run(pyinstaller_args)

print("=" * 60)
print("✅ Build abgeschlossen!")
print(f"📦 EXE-Datei: {os.path.join(project_dir, 'dist', 'RegistryManager.exe')}")
print("=" * 60)
