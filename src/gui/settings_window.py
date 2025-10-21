"""
Einstellungsfenster für den Registry Manager
===========================================

Konfiguration der Anwendungseinstellungen wie Popup-Zeiten, Backup-Verhalten, etc.
"""

import tkinter as tk
from tkinter import ttk
import json
from pathlib import Path
from typing import Dict, Any
import logging


class SettingsWindow:
    """Einstellungsfenster für Anwendungseinstellungen"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self.settings_file = Path(__file__).parent.parent.parent / "config" / "settings.json"
        self.settings = self._load_settings()
        
        self.window = None
        self._create_window()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Einstellungen aus Datei laden"""
        default_settings = {
            'popup_timeout_success': 0.5,
            'popup_timeout_error': 2.0,
            'popup_timeout_info': 1.0,
            'auto_backup': True,
            'backup_retention_days': 30,
            'auto_status_check': True,
            'debug_mode': False
        }
        
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                # Merge mit defaults
                default_settings.update(loaded_settings)
                return default_settings
            else:
                # Erstelle Standardeinstellungen
                self._save_settings(default_settings)
                return default_settings
                
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Einstellungen: {e}")
            return default_settings
    
    def _save_settings(self, settings: Dict[str, Any] = None):
        """Einstellungen in Datei speichern"""
        if settings is None:
            settings = self.settings
            
        try:
            # Verzeichnis erstellen falls nicht vorhanden
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Einstellungen gespeichert: {self.settings_file}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Einstellungen: {e}")
    
    def _create_window(self):
        """Einstellungsfenster erstellen"""
        self.window = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        self.window.title("Registry Manager - Einstellungen")
        self.window.geometry("500x400")
        self.window.resizable(True, True)
        
        # Icon übernehmen falls Parent vorhanden
        if self.parent:
            try:
                self.window.iconbitmap(self.parent.iconbitmap())
            except:
                pass
        
        # Hauptframe
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Notebook für Kategorien
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Popup-Einstellungen
        self._create_popup_tab(notebook)
        
        # Tab 2: Backup-Einstellungen
        self._create_backup_tab(notebook)
        
        # Tab 3: Allgemeine Einstellungen
        self._create_general_tab(notebook)
        
        # Button-Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Übernehmen", command=self._apply_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="OK", command=self._ok_clicked).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Abbrechen", command=self._cancel_clicked).pack(side=tk.RIGHT, padx=(0, 5))
        ttk.Button(button_frame, text="Standard wiederherstellen", command=self._reset_to_defaults).pack(side=tk.LEFT)
    
    def _create_popup_tab(self, notebook):
        """Tab für Popup-Einstellungen erstellen"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Popup-Fenster")
        
        # Scrollable Frame
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Popup-Zeiten Sektion
        popup_frame = ttk.LabelFrame(scrollable_frame, text="Automatisches Schließen von Popup-Fenstern")
        popup_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Erfolgs-Popups
        ttk.Label(popup_frame, text="Erfolgs-Meldungen (Sekunden):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.success_timeout_var = tk.DoubleVar(value=self.settings.get('popup_timeout_success', 0.5))
        success_spinbox = ttk.Spinbox(popup_frame, from_=0.1, to=10.0, increment=0.1, 
                                    textvariable=self.success_timeout_var, width=10)
        success_spinbox.grid(row=0, column=1, padx=5, pady=2)
        
        # Fehler-Popups
        ttk.Label(popup_frame, text="Fehler-Meldungen (Sekunden):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.error_timeout_var = tk.DoubleVar(value=self.settings.get('popup_timeout_error', 2.0))
        error_spinbox = ttk.Spinbox(popup_frame, from_=0.1, to=10.0, increment=0.1, 
                                  textvariable=self.error_timeout_var, width=10)
        error_spinbox.grid(row=1, column=1, padx=5, pady=2)
        
        # Info-Popups
        ttk.Label(popup_frame, text="Info-Meldungen (Sekunden):").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.info_timeout_var = tk.DoubleVar(value=self.settings.get('popup_timeout_info', 1.0))
        info_spinbox = ttk.Spinbox(popup_frame, from_=0.1, to=10.0, increment=0.1, 
                                 textvariable=self.info_timeout_var, width=10)
        info_spinbox.grid(row=2, column=1, padx=5, pady=2)
        
        # Hinweis
        hint_frame = ttk.Frame(scrollable_frame)
        hint_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(hint_frame, text="💡 Tipp:", font=("", 9, "bold")).pack(anchor="w")
        ttk.Label(hint_frame, text="• Niedrige Werte (0.5s) für schnelle Bedienung\n"
                               "• Höhere Werte (2s+) um Meldungen zu lesen\n"
                               "• 0.1s = minimale Zeit", 
                 font=("", 8)).pack(anchor="w", padx=20)
        
        # Test-Buttons
        test_frame = ttk.LabelFrame(scrollable_frame, text="Popup-Zeiten testen")
        test_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(test_frame, text="Erfolg testen", 
                  command=self._test_success_popup).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(test_frame, text="Fehler testen", 
                  command=self._test_error_popup).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(test_frame, text="Info testen", 
                  command=self._test_info_popup).pack(side=tk.LEFT, padx=5, pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_backup_tab(self, notebook):
        """Tab für Backup-Einstellungen erstellen"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Backups")
        
        backup_frame = ttk.LabelFrame(tab, text="Automatische Backups")
        backup_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.auto_backup_var = tk.BooleanVar(value=self.settings.get('auto_backup', True))
        ttk.Checkbutton(backup_frame, text="Automatische Backups vor Registry-Änderungen", 
                       variable=self.auto_backup_var).pack(anchor="w", padx=5, pady=2)
        
        ttk.Label(backup_frame, text="Backup-Aufbewahrung (Tage):").pack(anchor="w", padx=5, pady=(5, 2))
        self.backup_retention_var = tk.IntVar(value=self.settings.get('backup_retention_days', 30))
        ttk.Spinbox(backup_frame, from_=1, to=365, textvariable=self.backup_retention_var, 
                   width=10).pack(anchor="w", padx=20, pady=2)
    
    def _create_general_tab(self, notebook):
        """Tab für allgemeine Einstellungen erstellen"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Allgemein")
        
        general_frame = ttk.LabelFrame(tab, text="Status-Prüfung")
        general_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.auto_status_check_var = tk.BooleanVar(value=self.settings.get('auto_status_check', True))
        ttk.Checkbutton(general_frame, text="Automatische Status-Prüfung beim Start", 
                       variable=self.auto_status_check_var).pack(anchor="w", padx=5, pady=2)
        
        debug_frame = ttk.LabelFrame(tab, text="Entwicklung")
        debug_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.debug_mode_var = tk.BooleanVar(value=self.settings.get('debug_mode', False))
        ttk.Checkbutton(debug_frame, text="Debug-Modus aktivieren", 
                       variable=self.debug_mode_var).pack(anchor="w", padx=5, pady=2)
    
    def _test_success_popup(self):
        """Erfolgs-Popup testen"""
        from src.gui.main_window import AutoCloseMessageBox
        timeout = self.success_timeout_var.get()
        AutoCloseMessageBox.showinfo("Test", f"Erfolgs-Popup ({timeout}s)", timeout)
    
    def _test_error_popup(self):
        """Fehler-Popup testen"""
        from src.gui.main_window import AutoCloseMessageBox
        timeout = self.error_timeout_var.get()
        AutoCloseMessageBox.showerror("Test", f"Fehler-Popup ({timeout}s)", timeout)
    
    def _test_info_popup(self):
        """Info-Popup testen"""
        from src.gui.main_window import AutoCloseMessageBox
        timeout = self.info_timeout_var.get()
        AutoCloseMessageBox.showinfo("Test", f"Info-Popup ({timeout}s)", timeout)
    
    def _apply_settings(self):
        """Einstellungen anwenden"""
        self.settings.update({
            'popup_timeout_success': self.success_timeout_var.get(),
            'popup_timeout_error': self.error_timeout_var.get(),
            'popup_timeout_info': self.info_timeout_var.get(),
            'auto_backup': self.auto_backup_var.get(),
            'backup_retention_days': self.backup_retention_var.get(),
            'auto_status_check': self.auto_status_check_var.get(),
            'debug_mode': self.debug_mode_var.get()
        })
        
        self._save_settings()
        
        # Parent über Änderungen informieren
        if hasattr(self.parent, '_reload_settings'):
            self.parent._reload_settings()
    
    def _ok_clicked(self):
        """OK-Button geklickt"""
        self._apply_settings()
        self.window.destroy()
    
    def _cancel_clicked(self):
        """Abbrechen-Button geklickt"""
        self.window.destroy()
    
    def _reset_to_defaults(self):
        """Auf Standardeinstellungen zurücksetzen"""
        self.success_timeout_var.set(0.5)
        self.error_timeout_var.set(2.0)
        self.info_timeout_var.set(1.0)
        self.auto_backup_var.set(True)
        self.backup_retention_var.set(30)
        self.auto_status_check_var.set(True)
        self.debug_mode_var.set(False)
    
    def get_setting(self, key: str, default=None):
        """Einzelne Einstellung abrufen"""
        return self.settings.get(key, default)
    
    @classmethod
    def get_popup_timeouts(cls):
        """Popup-Zeiten für andere Module bereitstellen"""
        settings_file = Path(__file__).parent.parent.parent / "config" / "settings.json"
        try:
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                return {
                    'success': settings.get('popup_timeout_success', 0.5),
                    'error': settings.get('popup_timeout_error', 2.0),
                    'info': settings.get('popup_timeout_info', 1.0)
                }
        except:
            pass
        
        # Fallback zu Standardwerten
        return {'success': 0.5, 'error': 2.0, 'info': 1.0}


if __name__ == "__main__":
    # Test des Einstellungsfensters
    root = tk.Tk()
    root.withdraw()  # Hauptfenster verstecken
    
    settings_window = SettingsWindow()
    settings_window.window.mainloop()