#!/usr/bin/env python3
"""
Registry File Manager - Hauptanwendung
======================================

Ein umfassendes Tool zur Verwaltung von Windows Registry-Files (.reg).
Ermöglicht das Erstellen, Sammeln, Dokumentieren und Überprüfen von Registry-Einträgen.

Autor: Registry Manager Team
Version: 1.0.0
Datum: Oktober 2025
"""

import sys
import os
import logging
from pathlib import Path

# Pfad zur src-Verzeichnis hinzufügen
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui.main_window import RegistryManagerGUI
from utils.logger import setup_logging

def main():
    """Hauptfunktion der Anwendung"""
    
    # Basis-Pfad ermitteln (funktioniert für Skript und EXE)
    if getattr(sys, 'frozen', False):
        # Running as compiled EXE
        base_path = Path(sys.executable).parent
    else:
        # Running as script
        base_path = Path(__file__).parent
    
    # Logging einrichten
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Registry Manager wird gestartet...")
        logger.info(f"Basis-Pfad: {base_path}")
        
        # Sicherstellen, dass erforderliche Verzeichnisse existieren
        required_dirs = ['reg_files', 'config', 'docs', 'backups', 'logs']
        for dir_name in required_dirs:
            dir_path = base_path / dir_name
            dir_path.mkdir(exist_ok=True)
            logger.info(f"Verzeichnis erstellt/geprüft: {dir_path}")
        
        # GUI starten
        app = RegistryManagerGUI()
        app.run()
        
        logger.info("Registry Manager wurde erfolgreich beendet.")
        
    except Exception as e:
        logger.error(f"Fehler beim Starten der Anwendung: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()