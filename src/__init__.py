"""
Registry Manager - Hauptpaket
============================

Ein umfassendes Tool zur Verwaltung von Windows Registry-Files (.reg).
"""

__version__ = "1.0.0"
__author__ = "Registry Manager Team"
__description__ = "Tool zur Verwaltung von Windows Registry-Files"

# Haupt-Imports für einfache Nutzung
from .gui.main_window import RegistryManagerGUI
from .registry.reg_creator import RegFileCreator
from .registry.reg_parser import RegFileParser
from .registry.status_checker import RegistryStatusChecker
from .database.registry_db import RegistryDatabase

__all__ = [
    'RegistryManagerGUI',
    'RegFileCreator', 
    'RegFileParser',
    'RegistryStatusChecker',
    'RegistryDatabase'
]