"""
Hauptfenster der Registry Manager GUI
====================================

Dieses Modul enthält die Hauptklasse für die grafische Benutzeroberfläche
des Registry File Managers.
"""

import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog
import logging
from typing import Optional
import os
from pathlib import Path
from datetime import datetime
import threading

from src.registry.reg_parser import RegFileParser
from src.registry.reg_creator import RegFileCreator
from src.registry.status_checker import RegistryStatusChecker
from src.database.sqlite_db import SQLiteRegistryDB
from src.gui.reg_editor import RegFileEditor
from src.utils.backup_manager import RegistryBackupManager
from src.utils.content_analyzer import RegistryContentAnalyzer
from src.gui.status_display import StatusDisplay
from src.utils.system_restart import SystemRestart

class AutoCloseMessageBox:
    """MessageBox die sich automatisch nach bestimmter Zeit schließt"""
    
    @staticmethod
    def _get_timeout(message_type: str) -> float:
        """Timeout aus Einstellungen laden"""
        try:
            from src.gui.settings_window import SettingsWindow
            timeouts = SettingsWindow.get_popup_timeouts()
            return timeouts.get(message_type, 0.5)
        except:
            # Fallback zu Standardwerten
            defaults = {'success': 0.5, 'error': 2.0, 'info': 1.0}
            return defaults.get(message_type, 0.5)
    
    @staticmethod
    def showinfo(title, message, timeout=None):
        """Info-Dialog mit Auto-Close"""
        if timeout is None:
            timeout = AutoCloseMessageBox._get_timeout('info')
            
        def close_after_timeout():
            threading.Timer(timeout, lambda: dialog.destroy()).start()
        
        dialog = tk.Toplevel()
        dialog.title(title)
        dialog.geometry("300x120")
        dialog.resizable(False, False)
        
        # Zentrieren
        dialog.transient()
        dialog.grab_set()
        
        # Nachricht anzeigen
        ttk.Label(dialog, text=message, wraplength=280).pack(pady=20, padx=20)
        
        # OK Button (optional)
        ttk.Button(dialog, text="OK", command=dialog.destroy).pack(pady=10)
        
        # Auto-Close Timer starten
        close_after_timeout()
        
        return dialog
    
    @staticmethod
    def showsuccess(title, message, timeout=None):
        """Erfolgs-Dialog mit Auto-Close"""
        if timeout is None:
            timeout = AutoCloseMessageBox._get_timeout('success')
        return AutoCloseMessageBox.showinfo(title, message, timeout)

    @staticmethod
    def showerror(title, message, timeout=None):
        """Error-Dialog mit Auto-Close"""
        if timeout is None:
            timeout = AutoCloseMessageBox._get_timeout('error')
            
        def close_after_timeout():
            threading.Timer(timeout, lambda: dialog.destroy()).start()
        
        dialog = tk.Toplevel()
        dialog.title(title)
        dialog.geometry("300x120")
        dialog.resizable(False, False)
        
        # Zentrieren
        dialog.transient()
        dialog.grab_set()
        
        # Nachricht anzeigen (rot)
        label = ttk.Label(dialog, text=message, wraplength=280)
        label.pack(pady=20, padx=20)
        
        # OK Button
        ttk.Button(dialog, text="OK", command=dialog.destroy).pack(pady=10)
        
        # Auto-Close Timer starten
        close_after_timeout()
        
        return dialog

class RegistryManagerGUI:
    """Hauptfenster der Registry Manager Anwendung"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Basis-Pfad ermitteln (funktioniert für Skript und EXE)
        import sys
        if getattr(sys, 'frozen', False):
            # Running as compiled EXE
            self.base_path = Path(sys.executable).parent
        else:
            # Running as script
            self.base_path = Path(__file__).parent.parent.parent
        
        self.root = None
        self.db = SQLiteRegistryDB()
        self.reg_parser = RegFileParser()
        self.reg_creator = RegFileCreator()
        self.status_checker = RegistryStatusChecker()
        self.backup_manager = RegistryBackupManager(str(self.base_path / "backups"))
        self.content_analyzer = RegistryContentAnalyzer()
        self.current_file = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Benutzeroberfläche einrichten"""
        self.root = tk.Tk()
        self.root.title("Registry File Manager v1.0")
        self.root.geometry("1200x800")
        
        # Icon setzen (falls vorhanden)
        try:
            icon_path = Path(__file__).parent.parent.parent / "docs" / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception:
            pass
        
        self._create_menu()
        self._create_toolbar()
        self._create_main_area()
        self._create_status_bar()
        self._setup_keyboard_shortcuts()
        
        # Event-Handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_menu(self):
        """Menüleiste erstellen"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Datei-Menü
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="Neue REG-Datei erstellen", command=self._create_new_reg_file)
        file_menu.add_command(label="REG-Datei öffnen", command=self._open_reg_file)
        file_menu.add_separator()
        file_menu.add_command(label="Importieren", command=self._import_reg_files)
        file_menu.add_command(label="Exportieren", command=self._export_collection)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self._on_closing)
        
        # Registry-Menü
        registry_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Registry", menu=registry_menu)
        registry_menu.add_command(label="Status prüfen", command=self._check_registry_status)
        registry_menu.add_command(label="Registry anwenden", command=self._apply_registry_file)
        registry_menu.add_separator()
        registry_menu.add_command(label="Backup erstellen", command=self._create_registry_backup)
        registry_menu.add_command(label="Backups verwalten", command=self._show_backup_manager)
        registry_menu.add_command(label="Backup wiederherstellen", command=self._restore_backup)
        
        # Extras-Menü
        extras_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Extras", menu=extras_menu)
        extras_menu.add_command(label="Einstellungen...", command=self._show_settings)
        
        # Hilfe-Menü
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hilfe", menu=help_menu)
        help_menu.add_command(label="Dokumentation", command=self._show_documentation)
        help_menu.add_command(label="Über", command=self._show_about)
    
    def _create_toolbar(self):
        """Toolbar erstellen"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Buttons
        ttk.Button(toolbar, text="Neue REG-Datei", command=self._create_new_reg_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Öffnen", command=self._open_reg_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="REG einbetten", command=self._embed_reg_file).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Gruppen-Button
        ttk.Button(toolbar, text="📁 Gruppe erstellen", command=self._create_group).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Löschen Button
        ttk.Button(toolbar, text="🗑️ Löschen", command=self._delete_entry).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(toolbar, text="Status prüfen", command=self._check_registry_status).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Anwenden", command=self._apply_registry_file).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Neustart-Buttons
        ttk.Button(toolbar, text="🔄 Explorer neu starten", command=self._restart_explorer).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔄 PC neu starten", command=self._restart_windows).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(toolbar, text="Sammlung aktualisieren", command=self._refresh_collection).pack(side=tk.LEFT, padx=2)
    
    def _create_main_area(self):
        """Hauptbereich erstellen"""
        # Hauptcontainer mit Paned Window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Linker Bereich: REG-Datei Sammlung
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="REG-Datei Sammlung", font=("Arial", 12, "bold")).pack(pady=(0, 5))
        
        # Filter- und Suchbereich
        filter_frame = ttk.Frame(left_frame)
        filter_frame.pack(fill='x', pady=(0, 5))
        
        # Suchfeld
        search_frame = ttk.Frame(filter_frame)
        search_frame.pack(fill='x', pady=(0, 3))
        
        ttk.Label(search_frame, text="Suche:").pack(side='left')
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side='left', fill='x', expand=True, padx=(5, 0))
        
        # Filter-Optionen
        filter_options_frame = ttk.Frame(filter_frame)
        filter_options_frame.pack(fill='x', pady=(0, 3))
        
        # Kategorie-Filter
        ttk.Label(filter_options_frame, text="Kategorie:").pack(side='left')
        self.category_filter = ttk.Combobox(filter_options_frame, width=15, state='readonly')
        self.category_filter.pack(side='left', padx=(5, 10))
        self.category_filter.bind('<<ComboboxSelected>>', self._on_filter_change)
        
        # Status-Filter
        ttk.Label(filter_options_frame, text="Status:").pack(side='left')
        self.status_filter = ttk.Combobox(filter_options_frame, 
                                        values=['Alle', 'Aktiv', 'Inaktiv', 'Unbekannt'], 
                                        width=10, state='readonly')
        self.status_filter.set('Alle')
        self.status_filter.pack(side='left', padx=(5, 10))
        self.status_filter.bind('<<ComboboxSelected>>', self._on_filter_change)
        
        # Filter zurücksetzen Button
        ttk.Button(filter_options_frame, text="Reset", width=8, 
                  command=self._reset_filters).pack(side='right', padx=(5, 0))
        
        # Status-Prüfung Button
        ttk.Button(filter_options_frame, text="Alle Status prüfen", width=15,
                  command=self._check_all_status).pack(side='right', padx=(5, 5))
        
        # Treeview für Sammlung
        self.collection_tree = ttk.Treeview(left_frame, columns=("status", "category", "description"), show="tree headings")
        self.collection_tree.heading("#0", text="Name")
        self.collection_tree.heading("status", text="Status")
        self.collection_tree.heading("category", text="Kategorie")
        self.collection_tree.heading("description", text="Beschreibung")
        
        self.collection_tree.column("#0", width=200)
        self.collection_tree.column("status", width=80)
        self.collection_tree.column("description", width=300)
        
        # Scrollbars für Treeview
        tree_scrollbar_v = ttk.Scrollbar(left_frame, orient="vertical", command=self.collection_tree.yview)
        tree_scrollbar_h = ttk.Scrollbar(left_frame, orient="horizontal", command=self.collection_tree.xview)
        self.collection_tree.configure(yscrollcommand=tree_scrollbar_v.set, xscrollcommand=tree_scrollbar_h.set)
        
        self.collection_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Event-Handler für Treeview
        self.collection_tree.bind("<<TreeviewSelect>>", self._on_collection_select)
        # Doppelklick für Aktivieren/Deaktivieren
        self.collection_tree.bind("<Double-1>", self._on_collection_double_click_toggle)
        # Rechtsklick für Kontextmenü
        self.collection_tree.bind("<Button-3>", self._show_context_menu)
        
        # Rechter Bereich: Details und Editor
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)
        
        # Notebook für Tabs
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Datei-Details
        self.details_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.details_frame, text="Details")
        
        # Tab 2: Registry-Inhalt
        self.content_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.content_frame, text="Inhalt")
        
        # Tab 3: Status-Anzeige
        self.status_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.status_frame, text="Status")
        
        self._setup_details_tab()
        self._setup_content_tab()
        self._setup_status_tab()
    
    def _setup_details_tab(self):
        """Details-Tab einrichten"""
        # Scrollable Frame
        details_canvas = tk.Canvas(self.details_frame)
        details_scrollbar = ttk.Scrollbar(self.details_frame, orient="vertical", command=details_canvas.yview)
        scrollable_frame = ttk.Frame(details_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: details_canvas.configure(scrollregion=details_canvas.bbox("all"))
        )
        
        details_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        details_canvas.configure(yscrollcommand=details_scrollbar.set)
        
        # Datei-Informationen
        info_group = ttk.LabelFrame(scrollable_frame, text="Datei-Informationen")
        info_group.pack(fill=tk.X, padx=10, pady=5)
        
        self.file_name_var = tk.StringVar()
        self.file_path_var = tk.StringVar()
        self.file_size_var = tk.StringVar()
        self.file_modified_var = tk.StringVar()
        
        ttk.Label(info_group, text="Name:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(info_group, textvariable=self.file_name_var).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(info_group, text="Pfad:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(info_group, textvariable=self.file_path_var, wraplength=400).grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(info_group, text="Größe:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(info_group, textvariable=self.file_size_var).grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(info_group, text="Geändert:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(info_group, textvariable=self.file_modified_var).grid(row=3, column=1, sticky="w", padx=5, pady=2)
        
        # Dokumentation
        doc_group = ttk.LabelFrame(scrollable_frame, text="Dokumentation")
        doc_group.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Label(doc_group, text="Titel:").pack(anchor="w", padx=5, pady=(5, 0))
        self.title_entry = ttk.Entry(doc_group, width=50)
        self.title_entry.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(doc_group, text="Kategorie:").pack(anchor="w", padx=5, pady=(5, 0))
        self.category_combo = ttk.Combobox(doc_group, values=[
            "System", "Registry-Tweaks", "Sicherheit", "Performance", 
            "UI-Anpassungen", "Netzwerk", "Software", "Sonstiges"
        ])
        self.category_combo.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(doc_group, text="Beschreibung:").pack(anchor="w", padx=5, pady=(5, 0))
        self.description_text = tk.Text(doc_group, height=8, wrap=tk.WORD)
        desc_scrollbar = ttk.Scrollbar(doc_group, orient="vertical", command=self.description_text.yview)
        self.description_text.configure(yscrollcommand=desc_scrollbar.set)
        self.description_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        desc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 5))
        
        # Speichern-Button
        ttk.Button(scrollable_frame, text="Dokumentation speichern", 
                  command=self._save_documentation).pack(pady=10)
        
        details_canvas.pack(side="left", fill="both", expand=True)
        details_scrollbar.pack(side="right", fill="y")
    
    def _setup_content_tab(self):
        """Inhalt-Tab einrichten"""
        # Text-Widget für Registry-Inhalt
        self.content_text = tk.Text(self.content_frame, wrap=tk.NONE, font=("Consolas", 10))
        
        # Scrollbars
        content_scrollbar_v = ttk.Scrollbar(self.content_frame, orient="vertical", command=self.content_text.yview)
        content_scrollbar_h = ttk.Scrollbar(self.content_frame, orient="horizontal", command=self.content_text.xview)
        self.content_text.configure(yscrollcommand=content_scrollbar_v.set, xscrollcommand=content_scrollbar_h.set)
        
        self.content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        content_scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        content_scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Syntax-Highlighting für .reg-Dateien könnte hier hinzugefügt werden
    
    def _setup_status_tab(self):
        """Status-Tab einrichten"""
        self.status_display = StatusDisplay(self.status_frame)
    
    def _create_status_bar(self):
        """Status-Leiste erstellen"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_text = tk.StringVar()
        self.status_text.set("Bereit")
        ttk.Label(self.status_bar, textvariable=self.status_text).pack(side=tk.LEFT, padx=5)
        
        # Fortschrittsbalken
        self.progress = ttk.Progressbar(self.status_bar, mode='indeterminate')
        self.progress.pack(side=tk.RIGHT, padx=5)
    
    def _create_new_reg_file(self):
        """Neue REG-Datei erstellen"""
        self.logger.info("Erstelle neue REG-Datei...")
        try:
            editor = RegFileEditor(self.root, self.reg_creator)
            self.root.wait_window(editor.window)
            
            if hasattr(editor, 'result_file') and editor.result_file:
                self._refresh_collection()
                self._load_reg_file(editor.result_file)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen einer neuen REG-Datei: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Fehler beim Erstellen der REG-Datei: {e}", 0.5)
    
    def _open_reg_file(self):
        """REG-Datei öffnen"""
        filetypes = [
            ("Registry-Dateien", "*.reg"),
            ("Alle Dateien", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="REG-Datei öffnen",
            filetypes=filetypes,
            initialdir=Path(__file__).parent.parent.parent / "reg_files"
        )
        
        if filename:
            self._load_reg_file(filename)
    
    def _load_reg_file(self, filepath: str):
        """REG-Datei laden und anzeigen"""
        try:
            # Ignoriere Gruppen-Tags
            if filepath.startswith('group:') or filepath == 'ungrouped':
                return
            
            self.current_file = filepath
            
            # Prüfung für embedded REG files
            if filepath.startswith("embedded:"):
                reg_id = filepath.replace("embedded:", "")
                reg_data = self.db.get_embedded_reg(reg_id)
                if not reg_data:
                    raise FileNotFoundError(f"Embedded REG {reg_id} not found")
                
                content = reg_data['content']
                metadata = reg_data['metadata']
                
                # Datei-Informationen für embedded REG
                self.file_name_var.set(metadata.get('name', reg_id))
                self.file_path_var.set(f"embedded:{reg_id}")
                self.file_size_var.set(f"{len(content)} Bytes")
                self.file_modified_var.set(metadata.get('embedded_date', 'Unbekannt'))
                
                # Inhalt anzeigen
                self.content_text.delete(1.0, tk.END)
                self.content_text.insert(1.0, content)
                
                # Embedded Dokumentation laden
                self.title_entry.delete(0, tk.END)
                self.title_entry.insert(0, metadata.get('name', reg_id))
                
                self.category_combo.set(metadata.get('category', ''))
                
                self.description_text.delete(1.0, tk.END)
                self.description_text.insert(1.0, metadata.get('description', ''))
                
                self.status_text.set(f"Embedded REG geladen: {metadata.get('name', reg_id)}")
                return
            
            # Normale Datei-basierte REG files
            # Datei-Informationen aktualisieren
            file_path = Path(filepath)
            stat = file_path.stat()
            
            self.file_name_var.set(file_path.name)
            self.file_path_var.set(str(file_path))
            self.file_size_var.set(f"{stat.st_size} Bytes")
            self.file_modified_var.set(datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M:%S"))
            
            # Inhalt laden
            encodings = ['utf-8-sig', 'utf-16', 'utf-8', 'cp1252', 'latin1']
            content = None
            
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                # Als letzte Option binär lesen
                with open(filepath, 'rb') as f:
                    raw_content = f.read()
                try:
                    content = raw_content.decode('utf-8-sig')
                except:
                    content = raw_content.decode('utf-8', errors='replace')
            
            self.content_text.delete(1.0, tk.END)
            self.content_text.insert(1.0, content)
            
            # Dokumentation laden (falls vorhanden)
            doc_data = self.db.get_documentation(filepath)
            if doc_data:
                self.title_entry.delete(0, tk.END)
                self.title_entry.insert(0, doc_data.get('title', ''))
                
                self.category_combo.set(doc_data.get('category', ''))
                
                self.description_text.delete(1.0, tk.END)
                self.description_text.insert(1.0, doc_data.get('description', ''))
            
            self.status_text.set(f"Geladen: {file_path.name}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der REG-Datei: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Fehler beim Laden der Datei: {e}", 5.0)
    
    def _check_registry_status(self):
        """Registry-Status prüfen"""
        if not self.current_file:
            AutoCloseMessageBox.showerror("Warnung", "Bitte wählen Sie zuerst eine REG-Datei aus.", 0.5)
            return
        
        # Ignoriere Gruppen
        if self.current_file.startswith('group:') or self.current_file == 'ungrouped':
            return
        
        try:
            self.status_text.set("Prüfe Registry-Status...")
            self.progress.start()
            
            # Status in separatem Thread prüfen (vereinfacht hier synchron)
            status_results = self.status_checker.check_file_status(self.current_file, self.db)
            self.status_display.update_status(status_results)
            
            # Zu Status-Tab wechseln
            self.notebook.select(self.status_frame)
            
            self.status_text.set("Status-Prüfung abgeschlossen")
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Status-Prüfung: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Fehler bei der Status-Prüfung: {e}", 0.5)
        finally:
            self.progress.stop()
    
    def _apply_registry_file(self):
        """Registry-Datei anwenden"""
        if not self.current_file:
            AutoCloseMessageBox.showerror("Warnung", "Bitte wählen Sie zuerst eine REG-Datei aus.", 0.5)
            return
        
        # Ignoriere Gruppen
        if self.current_file.startswith('group:') or self.current_file == 'ungrouped':
            return
        
        # Sicherheitswarnung
        result = messagebox.askyesno(
            "Warnung", 
            "Das Anwenden von Registry-Änderungen kann Ihr System beeinträchtigen.\n\n"
            "Sind Sie sicher, dass Sie fortfahren möchten?",
            icon="warning"
        )
        
        if result:
            try:
                # Registry-Datei anwenden
                os.system(f'regedit /s "{self.current_file}"')
                AutoCloseMessageBox.showinfo("Erfolg", "Registry-Datei wurde erfolgreich angewendet.", 0.5)
                
                # Status neu prüfen
                self._check_registry_status()
                
            except Exception as e:
                self.logger.error(f"Fehler beim Anwenden der Registry-Datei: {e}")
                AutoCloseMessageBox.showerror("Fehler", f"Fehler beim Anwenden: {e}", 0.5)
    
    def _save_documentation(self):
        """Dokumentation speichern"""
        if not self.current_file:
            AutoCloseMessageBox.showerror("Warnung", "Keine Datei ausgewählt.", 0.5)
            return
        
        try:
            doc_data = {
                'title': self.title_entry.get(),
                'category': self.category_combo.get(),
                'description': self.description_text.get(1.0, tk.END).strip()
            }
            
            self.db.save_documentation(self.current_file, doc_data)
            self.status_text.set("Dokumentation gespeichert")
            AutoCloseMessageBox.showinfo("Erfolg", "Dokumentation wurde gespeichert.", 0.5)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Dokumentation: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Fehler beim Speichern: {e}", 0.5)
    
    def _refresh_collection(self):
        """Sammlung aktualisieren - jetzt mit eingebetteten REGs"""
        try:
            # Registry-Files laden und in Datenbank aktualisieren
            reg_files_dir = Path(__file__).parent.parent.parent / "reg_files"
            file_count = 0
            
            for reg_file in reg_files_dir.glob("*.reg"):
                # Datei zur Datenbank hinzufügen falls nicht vorhanden
                if not self.db.has_file(str(reg_file)):
                    # Automatische Analyse für neue Dateien
                    analysis = self.content_analyzer.analyze_file(str(reg_file))
                    analysis['status'] = 'Unbekannt'  # Status wird später geprüft
                    self.db.save_documentation(str(reg_file), analysis)
                file_count += 1
            
            # Eingebettete REGs dazuzählen
            embedded_regs = self.db.list_embedded_regs()
            embedded_count = len(embedded_regs)
            total_count = file_count + embedded_count
            
            # Kategorie-Filter aktualisieren
            self._update_category_filter()
            
            # Sammlung mit aktuellen Filtern anzeigen
            self._apply_filters()
            
            # Status aktualisieren
            status_msg = f"Sammlung aktualisiert - {total_count} Einträge"
            if embedded_count > 0:
                status_msg += f" ({file_count} Dateien, {embedded_count} eingebettet)"
            self.status_text.set(status_msg)
            
            # Automatische Status-Prüfung im Hintergrund starten
            self.root.after(1000, self._background_status_check)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren der Sammlung: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Fehler beim Laden der Sammlung: {e}", 1.0)
    
    def _import_reg_files(self):
        """REG-Dateien importieren - direkt in Datenbank einbetten"""
        files = filedialog.askopenfilenames(
            title="REG-Dateien zum Importieren auswählen",
            filetypes=[("Registry-Dateien", "*.reg"), ("Alle Dateien", "*.*")]
        )
        
        if files:
            # Rufe die Embed-Funktion auf
            self._embed_reg_files_internal(files)
    
    def _export_collection(self):
        """Sammlung exportieren"""
        directory = filedialog.askdirectory(title="Zielverzeichnis für Export auswählen")
        
        if directory:
            try:
                import shutil
                reg_files_dir = Path(__file__).parent.parent.parent / "reg_files"
                destination_dir = Path(directory) / "registry_collection_export"
                
                shutil.copytree(reg_files_dir, destination_dir, dirs_exist_ok=True)
                
                # Dokumentation exportieren
                self.db.export_documentation(destination_dir / "documentation.json")
                
                AutoCloseMessageBox.showinfo("Export", f"Sammlung erfolgreich nach {destination_dir} exportiert.", 0.5)
                
            except Exception as e:
                self.logger.error(f"Fehler beim Exportieren: {e}")
                AutoCloseMessageBox.showerror("Fehler", f"Fehler beim Exportieren: {e}", 0.5)
    
    def _create_registry_backup(self):
        """Registry-Backup erstellen"""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"registry_backup_{timestamp}.reg"
            
            # Registry exportieren
            os.system(f'regedit /e "{backup_file}"')
            
            AutoCloseMessageBox.showinfo("Backup", f"Registry-Backup erstellt: {backup_file}", 0.5)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen des Backups: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Fehler beim Erstellen des Backups: {e}", 0.5)
    
    def _show_documentation(self):
        """Dokumentation anzeigen"""
        doc_window = tk.Toplevel(self.root)
        doc_window.title("Dokumentation")
        doc_window.geometry("800x600")
        
        doc_text = tk.Text(doc_window, wrap=tk.WORD)
        doc_scrollbar = ttk.Scrollbar(doc_window, orient="vertical", command=doc_text.yview)
        doc_text.configure(yscrollcommand=doc_scrollbar.set)
        
        # Dokumentation laden
        try:
            doc_path = Path(__file__).parent.parent.parent / "docs" / "README.md"
            if doc_path.exists():
                with open(doc_path, 'r', encoding='utf-8') as f:
                    doc_text.insert(1.0, f.read())
            else:
                doc_text.insert(1.0, "Dokumentation wird geladen...")
        except Exception:
            doc_text.insert(1.0, "Fehler beim Laden der Dokumentation.")
        
        doc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        doc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _show_about(self):
        """Info-Dialog anzeigen"""
        about_text = """Registry File Manager v1.0

Ein umfassendes Tool zur Verwaltung von Windows Registry-Files.

Funktionen:
• Erstellen und Bearbeiten von .reg-Dateien
• Sammlung und Organisation
• Dokumentation und Kategorisierung
• Status-Überprüfung der Registry-Einträge
• Import/Export von Sammlungen

Entwickelt im Oktober 2025
Python mit tkinter GUI"""
        
        AutoCloseMessageBox.showinfo("Über Registry File Manager", about_text, 0.5)
    
    def _on_closing(self):
        """Handler für Anwendungsende"""
        try:
            self.db.close()
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            self.logger.error(f"Fehler beim Beenden: {e}")
    
    def run(self):
        """Anwendung starten"""
        try:
            # Sammlung beim Start laden
            self._refresh_collection()
            
            # Hauptschleife starten
            self.root.mainloop()
            
        except Exception as e:
            self.logger.error(f"Fehler in der Hauptschleife: {e}")
    
    def _setup_keyboard_shortcuts(self):
        """Tastenkürzel einrichten"""
        # F5 - Status aktualisieren
        self.root.bind('<F5>', lambda e: self._refresh_collection())
        
        # Ctrl+N - Neue .reg-Datei
        self.root.bind('<Control-n>', lambda e: self._new_reg_file())
        
        # Ctrl+O - .reg-Datei importieren  
        self.root.bind('<Control-o>', lambda e: self._import_reg_file())
        
        # Enter - Ausgewählte Datei anwenden
        self.root.bind('<Return>', lambda e: self._apply_selected_reg())
        
        # Delete - Rückgängig machen
        self.root.bind('<Delete>', lambda e: self._revert_selected_reg())
        
        # Ctrl+F - Suche öffnen
        self.root.bind('<Control-f>', lambda e: self._open_search())
        
        # Escape - Suche schließen
        self.root.bind('<Escape>', lambda e: self._close_search())
    
    def _apply_selected_reg(self):
        """Ausgewählte .reg-Datei anwenden"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        file_path = item['values'][0] if item['values'] else None
        
        if file_path and os.path.exists(file_path):
            self._apply_reg_file(file_path)
    
    def _revert_selected_reg(self):
        """Ausgewählte .reg-Datei rückgängig machen"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        file_path = item['values'][0] if item['values'] else None
        
        if file_path:
            # TODO: Revert-Funktionalität implementieren
            AutoCloseMessageBox.showinfo("Info", "Revert-Funktion wird in Kürze verfügbar sein!", 0.5)
    
    def _open_search(self):
        """Suchfunktion öffnen"""
        # Fokus auf Suchfeld setzen
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if hasattr(child, 'focus'):
                        try:
                            child.focus()
                            break
                        except:
                            pass
    
    def _close_search(self):
        """Suche schließen"""
        self.search_var.set('')
    
    def _apply_reg_file(self, file_path: str):
        """Registry-Datei anwenden"""
        try:
            import subprocess
            result = messagebox.askyesno(
                "Registry-Datei anwenden",
                f"Möchten Sie die Registry-Datei '{os.path.basename(file_path)}' wirklich anwenden?\n\n"
                "WARNUNG: Dies kann Ihr System beeinträchtigen!"
            )
            
            if result:
                # Backup erstellen
                backup_id = self.backup_manager.create_backup(
                    file_path, 
                    f"Vor Anwendung von {os.path.basename(file_path)}"
                )
                
                if backup_id:
                    self.logger.info(f"Backup erstellt: {backup_id}")
                else:
                    backup_warning = messagebox.askyesno(
                        "Backup-Warnung",
                        "Backup konnte nicht erstellt werden. Trotzdem fortfahren?"
                    )
                    if not backup_warning:
                        return
                
                # Registry-Datei anwenden
                subprocess.run(['regedit', '/s', file_path], check=True)
                AutoCloseMessageBox.showinfo("Erfolg", f"Registry-Datei wurde erfolgreich angewendet!\n{f'Backup: {backup_id}' if backup_id else ''}", 0.5)
                
                # Status aktualisieren
                self._refresh_collection()
                
        except subprocess.CalledProcessError as e:
            AutoCloseMessageBox.showerror("Fehler", f"Fehler beim Anwenden der Registry-Datei: {e}", 0.5)
            self.logger.error(f"Fehler beim Anwenden von {file_path}: {e}")
        except Exception as e:
            AutoCloseMessageBox.showerror("Fehler", f"Unerwarteter Fehler: {e}", 0.5)
            self.logger.error(f"Unerwarteter Fehler beim Anwenden von {file_path}: {e}")
    
    def _new_reg_file(self):
        """Neue .reg-Datei erstellen"""
        if hasattr(self, 'reg_editor') and self.reg_editor:
            self.reg_editor.new_file()
        else:
            AutoCloseMessageBox.showinfo("Info", "Registry-Editor öffnen...", 0.5)
    
    def _import_reg_file(self):
        """Registry-Datei importieren"""
        file_path = filedialog.askopenfilename(
            title="Registry-Datei importieren",
            filetypes=[("Registry-Dateien", "*.reg"), ("Alle Dateien", "*.*")]
        )
        
        if file_path:
            try:
                # Datei in reg_files Verzeichnis kopieren
                import shutil
                dest_path = Path("reg_files") / os.path.basename(file_path)
                shutil.copy2(file_path, dest_path)
                
                # Zur Sammlung hinzufügen
                self._refresh_collection()
                AutoCloseMessageBox.showinfo("Erfolg", f"Datei wurde importiert: {dest_path}", 0.5)
                
            except Exception as e:
                AutoCloseMessageBox.showerror("Fehler", f"Fehler beim Importieren: {e}", 0.5)
                self.logger.error(f"Import-Fehler: {e}")
    
    def _show_backup_manager(self):
        """Backup-Manager-Fenster öffnen"""
        self._open_backup_manager_window()
    
    def _restore_backup(self):
        """Backup wiederherstellen"""
        backups = self.backup_manager.list_backups()
        
        if not backups:
            AutoCloseMessageBox.showinfo("Info", "Keine Backups vorhanden", 0.5)
            return
        
        # Backup-Auswahl-Dialog
        backup_window = tk.Toplevel(self.root)
        backup_window.title("Backup wiederherstellen")
        backup_window.geometry("600x400")
        backup_window.transient(self.root)
        backup_window.grab_set()
        
        # Backup-Liste
        list_frame = ttk.Frame(backup_window)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        backup_tree = ttk.Treeview(list_frame, columns=('date', 'file', 'description'), show='headings')
        backup_tree.heading('date', text='Datum')
        backup_tree.heading('file', text='Datei')
        backup_tree.heading('description', text='Beschreibung')
        
        for backup in backups:
            date_str = datetime.fromisoformat(backup['datetime']).strftime('%d.%m.%Y %H:%M')
            backup_tree.insert('', 'end', values=(
                date_str,
                backup['reg_file'],
                backup['description']
            ), tags=(backup['id'],))
        
        backup_tree.pack(fill='both', expand=True)
        
        # Buttons
        btn_frame = ttk.Frame(backup_window)
        btn_frame.pack(fill='x', padx=10, pady=5)
        
        def restore_selected():
            selection = backup_tree.selection()
            if not selection:
                AutoCloseMessageBox.showerror("Warnung", "Bitte wählen Sie ein Backup aus", 0.5)
                return
            
            backup_id = backup_tree.item(selection[0])['tags'][0]
            
            result = messagebox.askyesno(
                "Backup wiederherstellen",
                "Möchten Sie das ausgewählte Backup wirklich wiederherstellen?\n\n"
                "WARNUNG: Dies überschreibt die aktuellen Registry-Einstellungen!"
            )
            
            if result:
                if self.backup_manager.restore_backup(backup_id):
                    AutoCloseMessageBox.showinfo("Erfolg", "Backup wurde erfolgreich wiederhergestellt!", 0.5)
                    backup_window.destroy()
                    self._refresh_collection()
                else:
                    AutoCloseMessageBox.showerror("Fehler", "Backup konnte nicht wiederhergestellt werden", 0.5)
        
        ttk.Button(btn_frame, text="Wiederherstellen", command=restore_selected).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Abbrechen", command=backup_window.destroy).pack(side='right', padx=5)
    
    def _open_backup_manager_window(self):
        """Backup-Manager-Fenster öffnen"""
        backup_window = tk.Toplevel(self.root)
        backup_window.title("Backup-Manager")
        backup_window.geometry("800x600")
        backup_window.transient(self.root)
        
        # Backup-Liste
        main_frame = ttk.Frame(backup_window)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Treeview für Backups
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill='both', expand=True)
        
        backup_tree = ttk.Treeview(tree_frame, columns=('date', 'file', 'description', 'size'), show='headings')
        backup_tree.heading('date', text='Datum')
        backup_tree.heading('file', text='Datei')
        backup_tree.heading('description', text='Beschreibung')
        backup_tree.heading('size', text='Größe')
        
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=backup_tree.yview)
        backup_tree.configure(yscrollcommand=scrollbar.set)
        
        backup_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        def refresh_backup_list():
            # Liste leeren
            for item in backup_tree.get_children():
                backup_tree.delete(item)
            
            # Backups laden
            backups = self.backup_manager.list_backups()
            for backup in backups:
                date_str = datetime.fromisoformat(backup['datetime']).strftime('%d.%m.%Y %H:%M')
                
                # Backup-Größe berechnen
                backup_path = Path("backups") / backup['id']
                size = "N/A"
                if backup_path.exists():
                    total_size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
                    size = f"{total_size / 1024:.1f} KB"
                
                backup_tree.insert('', 'end', values=(
                    date_str,
                    backup['reg_file'],
                    backup['description'],
                    size
                ), tags=(backup['id'],))
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(10, 0))
        
        def delete_selected():
            selection = backup_tree.selection()
            if not selection:
                AutoCloseMessageBox.showerror("Warnung", "Bitte wählen Sie ein Backup aus", 0.5)
                return
            
            backup_id = backup_tree.item(selection[0])['tags'][0]
            
            result = messagebox.askyesno(
                "Backup löschen",
                "Möchten Sie das ausgewählte Backup wirklich löschen?"
            )
            
            if result:
                if self.backup_manager.delete_backup(backup_id):
                    AutoCloseMessageBox.showinfo("Erfolg", "Backup wurde gelöscht", 0.5)
                    refresh_backup_list()
                else:
                    AutoCloseMessageBox.showerror("Fehler", "Backup konnte nicht gelöscht werden", 0.5)
        
        def cleanup_old():
            result = messagebox.askyesno(
                "Alte Backups aufräumen",
                "Möchten Sie alte Backups aufräumen?\n(Behält die neuesten 20 Backups)"
            )
            
            if result:
                self.backup_manager.cleanup_old_backups(max_backups=20)
                AutoCloseMessageBox.showinfo("Erfolg", "Alte Backups wurden aufgeräumt", 0.5)
                refresh_backup_list()
        
        ttk.Button(btn_frame, text="Aktualisieren", command=refresh_backup_list).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Löschen", command=delete_selected).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Aufräumen", command=cleanup_old).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Schließen", command=backup_window.destroy).pack(side='right', padx=5)
        
        # Initiale Befüllung
        refresh_backup_list()
    
    def _on_search_change(self, *args):
        """Wird aufgerufen wenn sich der Suchtext ändert"""
        self._apply_filters()
    
    def _on_filter_change(self, event=None):
        """Wird aufgerufen wenn sich ein Filter ändert"""
        self._apply_filters()
    
    def _reset_filters(self):
        """Alle Filter zurücksetzen"""
        self.search_var.set('')
        self.category_filter.set('')
        self.status_filter.set('Alle')
        self._apply_filters()
    
    def _apply_filters(self):
        """Filter auf die Sammlung anwenden"""
        try:
            search_text = self.search_var.get().lower()
            category_filter = self.category_filter.get()
            status_filter = self.status_filter.get()
            
            # TreeView leeren
            for item in self.collection_tree.get_children():
                self.collection_tree.delete(item)
            
            # Registry-Files aus dem Verzeichnis laden
            reg_files_dir = Path(__file__).parent.parent.parent / "reg_files"
            
            for reg_file in reg_files_dir.glob("*.reg"):
                try:
                    # Dokumentation aus Datenbank abrufen
                    doc_data = self.db.get_documentation(str(reg_file))
                    
                    # Automatische Analyse falls keine oder unvollständige Dokumentation
                    if not doc_data or not doc_data.get('category') or doc_data.get('category') == 'Sonstiges':
                        analysis = self.content_analyzer.analyze_file(str(reg_file))
                        
                        if not doc_data:
                            doc_data = analysis
                            doc_data['status'] = 'Unbekannt'
                        else:
                            # Bestehende Daten mit Analyse ergänzen
                            if not doc_data.get('category') or doc_data.get('category') == 'Sonstiges':
                                doc_data['category'] = analysis['category']
                            if not doc_data.get('description'):
                                doc_data['description'] = analysis['description']
                            doc_data['title'] = analysis['formatted_name']
                        
                        # Aktualisierte Daten speichern
                        self.db.save_documentation(str(reg_file), doc_data)
                    
                    # Status automatisch prüfen falls unbekannt
                    if not doc_data.get('status') or doc_data.get('status') == 'Unbekannt':
                        try:
                            status_data = self.status_checker.check_file_status(str(reg_file), self.db)
                            if status_data and 'overall_status' in status_data:
                                if status_data['overall_status'] == 'all_active':
                                    doc_data['status'] = 'Aktiv'
                                elif status_data['overall_status'] == 'all_inactive':
                                    doc_data['status'] = 'Inaktiv'
                                elif status_data['overall_status'] == 'partial':
                                    doc_data['status'] = 'Teilweise'
                                else:
                                    doc_data['status'] = 'Unbekannt'
                            else:
                                doc_data['status'] = 'Unbekannt'
                            
                            # Status in Datenbank speichern
                            self.db.save_documentation(str(reg_file), doc_data)
                        except Exception as e:
                            self.logger.warning(f"Status-Prüfung für {reg_file.name} fehlgeschlagen: {e}")
                            doc_data['status'] = 'Unbekannt'
                    
                    # Formatierter Name (falls nicht vorhanden)
                    if not doc_data.get('title'):
                        doc_data['title'] = self.content_analyzer._format_filename(reg_file.stem)
                    
                    # Suchfilter anwenden
                    if search_text:
                        search_fields = [
                            os.path.basename(str(reg_file)).lower(),
                            doc_data.get('description', '').lower(),
                            doc_data.get('category', '').lower(),
                            doc_data.get('title', '').lower()
                        ]
                        if not any(search_text in field for field in search_fields):
                            continue
                    
                    # Kategorie-Filter anwenden
                    if category_filter and category_filter != doc_data.get('category', ''):
                        continue
                    
                    # Status-Filter anwenden
                    if status_filter != 'Alle':
                        file_status = doc_data.get('status', 'Unbekannt')
                        if status_filter != file_status:
                            continue
                    
                    # Item hinzufügen
                    status_icon = self._get_status_icon(doc_data.get('status', 'unknown'))
                    
                    self.collection_tree.insert("", "end", 
                        text=doc_data.get('title', reg_file.stem),
                        values=(
                            f"{status_icon} {doc_data.get('status', 'Unbekannt')}",
                            doc_data.get('category', 'Sonstiges'),
                            doc_data.get('description', 'Keine Beschreibung')
                        ),
                        tags=(str(reg_file),)
                    )
                    
                except Exception as e:
                    self.logger.warning(f"Fehler beim Laden von {reg_file.name}: {e}")
                    # Datei trotzdem anzeigen
                    self.collection_tree.insert("", "end", 
                        text=reg_file.stem,
                        values=("❓ Fehler", "Sonstiges", f"Fehler: {e}"),
                        tags=(str(reg_file),)
                    )
            
            # === GRUPPEN-ANSICHT (NEUE VERSION) ===
            # Alle eingebetteten REGs und ihre Gruppenzugehörigkeit sammeln
            embedded_regs = self.db.list_embedded_regs()
            all_groups = self.db.list_groups()
            
            # Gruppierte REGs tracken
            grouped_reg_ids = set()
            
            # Trennlinie nur wenn es Gruppen gibt
            if all_groups or embedded_regs:
                self.collection_tree.insert("", "end", text="═════ EMBEDDED REGS ═════", values=("", "", ""))
            
            # Erst alle Gruppen anzeigen
            if all_groups:
                for group in all_groups:
                    # Gruppen-Ordner einfügen
                    group_item = self.collection_tree.insert("", "end",
                        text=f"{group['icon']} {group['name']}",
                        values=("📁 Gruppe", "", group.get('description', '')),
                        tags=(f"group:{group['id']}",),
                        open=True  # Gruppe standardmäßig aufgeklappt
                    )
                    
                    # REGs dieser Gruppe holen
                    reg_ids_in_group = self.db.get_group_regs(group['id'])
                    
                    for reg_id in reg_ids_in_group:
                        reg_data = self.db.get_embedded_reg(reg_id)
                        if not reg_data:
                            continue
                        
                        metadata = reg_data['metadata']
                        
                        # Filter auch auf gruppierte REGs anwenden
                        if search_text:
                            search_fields = [
                                metadata.get('name', '').lower(),
                                metadata.get('description', '').lower(),
                                metadata.get('category', '').lower()
                            ]
                            if not any(search_text in field for field in search_fields):
                                continue
                        
                        if category_filter and category_filter != metadata.get('category', ''):
                            continue
                        
                        if status_filter != 'Alle':
                            if status_filter != metadata.get('status', 'Inaktiv'):
                                continue
                        
                        # REG als Kind der Gruppe hinzufügen
                        status_icon = self._get_status_icon(metadata.get('status', 'Inaktiv'))
                        self.collection_tree.insert(group_item, "end",
                            text=f"  📦 {metadata.get('name', reg_id)}",
                            values=(
                                f"{status_icon} {metadata.get('status', 'Inaktiv')}",
                                metadata.get('category', 'Sonstiges'),
                                metadata.get('description', 'Keine Beschreibung')
                            ),
                            tags=(f"embedded:{reg_id}",)
                        )
                        
                        # Als gruppiert markieren
                        grouped_reg_ids.add(reg_id)
            
            # === NICHT GRUPPIERTE REGs ===
            # Alle REGs die in keiner Gruppe sind
            ungrouped_regs = []
            for reg_id, reg_data in embedded_regs.items():
                if reg_id not in grouped_reg_ids:
                    metadata = reg_data.get('metadata', {})
                    
                    # Filter anwenden
                    if search_text:
                        search_fields = [
                            metadata.get('name', '').lower(),
                            metadata.get('description', '').lower(),
                            metadata.get('category', '').lower()
                        ]
                        if not any(search_text in field for field in search_fields):
                            continue
                    
                    if category_filter and category_filter != metadata.get('category', ''):
                        continue
                    
                    if status_filter != 'Alle':
                        if status_filter != metadata.get('status', 'Inaktiv'):
                            continue
                    
                    ungrouped_regs.append((reg_id, metadata))
            
            # "Ohne Gruppe" Ordner anzeigen wenn es ungrouped REGs gibt
            if ungrouped_regs:
                ungrouped_item = self.collection_tree.insert("", "end",
                    text="📦 Ohne Gruppe",
                    values=("", "", f"{len(ungrouped_regs)} REG(s) ohne Gruppenzuordnung"),
                    tags=("ungrouped",),
                    open=True
                )
                
                for reg_id, metadata in ungrouped_regs:
                    status_icon = self._get_status_icon(metadata.get('status', 'Inaktiv'))
                    self.collection_tree.insert(ungrouped_item, "end",
                        text=f"  📦 {metadata.get('name', reg_id)}",
                        values=(
                            f"{status_icon} {metadata.get('status', 'Inaktiv')}",
                            metadata.get('category', 'Sonstiges'),
                            metadata.get('description', 'Keine Beschreibung')
                        ),
                        tags=(f"embedded:{reg_id}",)
                    )
                    
        except Exception as e:
            self.logger.error(f"Fehler beim Anwenden der Filter: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Fehler beim Filtern: {e}", 1.0)

    
    def _check_all_status(self):
        """Status aller Registry-Dateien prüfen"""
        try:
            reg_files_dir = Path(__file__).parent.parent.parent / "reg_files"
            reg_files = list(reg_files_dir.glob("*.reg"))
            
            if not reg_files:
                AutoCloseMessageBox.showinfo("Info", "Keine Registry-Dateien gefunden", 0.5)
                return
            
            # Progress-Dialog erstellen
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Status wird geprüft...")
            progress_window.geometry("400x120")
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            progress_label = ttk.Label(progress_window, text="Prüfe Status...")
            progress_label.pack(pady=10)
            
            progress_bar = ttk.Progressbar(progress_window, length=300, mode='determinate')
            progress_bar.pack(pady=10)
            progress_bar['maximum'] = len(reg_files)
            
            # Status für jede Datei prüfen
            for i, reg_file in enumerate(reg_files):
                progress_label.config(text=f"Prüfe {reg_file.name}...")
                progress_bar['value'] = i + 1
                progress_window.update()
                
                try:
                    # Registry-Status prüfen
                    status_data = self.status_checker.check_file_status(str(reg_file), self.db)
                    
                    # Status in Datenbank speichern
                    doc_data = self.db.get_documentation(str(reg_file)) or {}
                    
                    if status_data and 'overall_status' in status_data:
                        if status_data['overall_status'] == 'all_active':
                            doc_data['status'] = 'Aktiv'
                        elif status_data['overall_status'] == 'all_inactive':
                            doc_data['status'] = 'Inaktiv'
                        elif status_data['overall_status'] == 'partial':
                            doc_data['status'] = 'Teilweise'
                        else:
                            doc_data['status'] = 'Unbekannt'
                    else:
                        doc_data['status'] = 'Unbekannt'
                    
                    # Automatische Analyse falls noch nicht vorhanden
                    if not doc_data.get('category') or doc_data.get('category') == 'Sonstiges':
                        analysis = self.content_analyzer.analyze_file(str(reg_file))
                        doc_data.update(analysis)
                    
                    self.db.save_documentation(str(reg_file), doc_data)
                    
                except Exception as e:
                    self.logger.warning(f"Fehler beim Prüfen von {reg_file.name}: {e}")
            
            progress_window.destroy()
            
            # Sammlung aktualisieren
            self._apply_filters()
            
            AutoCloseMessageBox.showinfo("Erfolg", f"Status von {len(reg_files)} Dateien wurde geprüft!", 0.5)
            
        except Exception as e:
            if 'progress_window' in locals():
                progress_window.destroy()
            self.logger.error(f"Fehler beim Prüfen aller Status: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Fehler beim Status-Check: {e}", 0.5)
    
    def _on_collection_select(self, event):
        """Eintrag ausgewählt - Details anzeigen"""
        selection = self.collection_tree.selection()
        if selection:
            item = self.collection_tree.item(selection[0])
            file_path = item['tags'][0] if item['tags'] else None
            
            # Ignoriere Gruppen-Ordner und "Ohne Gruppe"
            if file_path and not file_path.startswith('group:') and file_path != 'ungrouped':
                self._load_reg_file(file_path)
        
    def _on_collection_double_click_toggle(self, event):
        """Doppelklick zum Aktivieren/Deaktivieren einer Registry-Datei"""
        selection = self.collection_tree.selection()
        
        if not selection:
            return
        
        item = self.collection_tree.item(selection[0])
        file_path = item['tags'][0] if item['tags'] else None
        
        if not file_path:
            return
        
        # Ignoriere Gruppen-Ordner und "Ohne Gruppe"
        if file_path.startswith('group:') or file_path == 'ungrouped':
            return
        
        # Prüfen ob es sich um eine eingebettete REG handelt
        if file_path.startswith("embedded:"):
            reg_id = file_path.replace("embedded:", "")
            self._toggle_embedded_registry(reg_id)
        elif os.path.exists(file_path):
            self._toggle_file_registry(file_path)
        else:
            AutoCloseMessageBox.showerror("Fehler", "Datei nicht gefunden", 0.5)
    
    def _show_context_menu(self, event):
        """Rechtsklick-Kontextmenü anzeigen"""
        # Eintrag unter Mauszeiger auswählen
        item_id = self.collection_tree.identify_row(event.y)
        if not item_id:
            return
        
        self.collection_tree.selection_set(item_id)
        
        item = self.collection_tree.item(item_id)
        file_path = item['tags'][0] if item['tags'] else None
        
        if not file_path:
            return
        
        # Ignoriere Gruppen-Ordner und "Ohne Gruppe" - kein Kontextmenü
        if file_path.startswith('group:') or file_path == 'ungrouped':
            return
        
        # Kontextmenü erstellen
        context_menu = tk.Menu(self.root, tearoff=0)
        
        # Status ermitteln (entfernt Emojis)
        values = item['values']
        status_text = values[0] if values else 'Unbekannt'
        
        # Aktivieren/Deaktivieren (immer verfügbar, aber Label passt sich an)
        if 'Aktiv' in status_text and 'Inaktiv' not in status_text:
            context_menu.add_command(label="🔴 Deaktivieren", command=lambda: self._context_toggle(file_path))
        else:
            context_menu.add_command(label="🟢 Aktivieren", command=lambda: self._context_toggle(file_path))
        
        context_menu.add_separator()
        
        # Gruppen-Menü (nur für embedded REGs)
        if file_path.startswith("embedded:"):
            reg_id = file_path.replace("embedded:", "")
            groups_menu = tk.Menu(context_menu, tearoff=0)
            
            # Vorhandene Gruppen
            all_groups = self.db.list_groups()
            reg_groups = self.db.get_reg_groups(reg_id)
            
            if all_groups:
                for group in all_groups:
                    if group['id'] in reg_groups:
                        # Bereits in Gruppe - Option zum Entfernen
                        groups_menu.add_command(
                            label=f"✓ {group['icon']} {group['name']}",
                            command=lambda gid=group['id']: self._remove_from_group(reg_id, gid)
                        )
                    else:
                        # Nicht in Gruppe - Option zum Hinzufügen
                        groups_menu.add_command(
                            label=f"   {group['icon']} {group['name']}",
                            command=lambda gid=group['id']: self._add_to_group(reg_id, gid)
                        )
                
                groups_menu.add_separator()
            
            groups_menu.add_command(label="➕ Neue Gruppe erstellen...", command=self._create_group)
            
            context_menu.add_cascade(label="📁 Gruppen", menu=groups_menu)
            context_menu.add_separator()
        
        context_menu.add_command(label="🗑️ Löschen", command=lambda: self._context_delete(file_path))
        
        # Menü anzeigen
        context_menu.post(event.x_root, event.y_root)
    
    def _context_toggle(self, file_path: str):
        """Toggle aus Kontextmenü"""
        if file_path.startswith("embedded:"):
            reg_id = file_path.replace("embedded:", "")
            self._toggle_embedded_registry(reg_id)
        elif os.path.exists(file_path):
            self._toggle_file_registry(file_path)
        else:
            AutoCloseMessageBox.showerror("Fehler", "Datei nicht gefunden", 0.5)
    
    def _context_delete(self, file_path: str):
        """Löschen aus Kontextmenü"""
        if file_path.startswith("embedded:"):
            reg_id = file_path.replace("embedded:", "")
            self._delete_embedded_entry(reg_id)
        elif os.path.exists(file_path):
            self._delete_file_entry(file_path)
        else:
            AutoCloseMessageBox.showerror("Fehler", "Datei nicht gefunden", 0.5)
    
    def _delete_embedded_entry(self, reg_id: str):
        """Embedded REG-Eintrag löschen"""
        try:
            reg_data = self.db.get_embedded_reg(reg_id)
            if not reg_data:
                AutoCloseMessageBox.showerror("Fehler", "REG-Daten nicht gefunden", 3.0)
                return
            
            name = reg_data['metadata'].get('name', reg_id)
            
            result = messagebox.askyesno(
                "Löschen bestätigen", 
                f"Möchten Sie '{name}' wirklich löschen?\n\n"
                "Der eingebettete REG-Eintrag wird aus der Datenbank entfernt.\n"
                "Dieser Vorgang kann nicht rückgängig gemacht werden."
            )
            
            if result:
                if self.db.delete_embedded_reg(reg_id):
                    AutoCloseMessageBox.showsuccess("Gelöscht", f"'{name}' wurde gelöscht", 2.0)
                    self._refresh_collection()
                else:
                    AutoCloseMessageBox.showerror("Fehler", "Löschen fehlgeschlagen", 3.0)
                    
        except Exception as e:
            self.logger.error(f"Fehler beim Löschen von embedded REG {reg_id}: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Löschen fehlgeschlagen: {str(e)}", 3.0)
    
    def _delete_file_entry(self, file_path: str):
        """Datei-REG-Eintrag von Festplatte löschen"""
        try:
            filename = os.path.basename(file_path)
            
            result = messagebox.askyesno(
                "Löschen bestätigen",
                f"Möchten Sie '{filename}' wirklich löschen?\n\n"
                "⚠️ DIE DATEI WIRD DAUERHAFT VON DER FESTPLATTE GELÖSCHT!\n"
                "Dieser Vorgang kann nicht rückgängig gemacht werden."
            )
            
            if result:
                # Datei von Festplatte löschen
                if os.path.exists(file_path):
                    os.remove(file_path)
                    self.logger.info(f"Datei gelöscht: {file_path}")
                
                # Dokumentation löschen
                self.db.delete_documentation(file_path)
                
                AutoCloseMessageBox.showsuccess("Gelöscht", f"'{filename}' wurde dauerhaft gelöscht", 2.0)
                self._refresh_collection()
                
        except Exception as e:
            self.logger.error(f"Fehler beim Löschen von {file_path}: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Löschen fehlgeschlagen: {str(e)}", 3.0)
    
    def _toggle_embedded_registry(self, reg_id: str):
        """Toggle für eingebettete Registry-Einträge"""
        try:
            reg_data = self.db.get_embedded_reg(reg_id)
            if not reg_data:
                AutoCloseMessageBox.showerror("Fehler", "REG-Daten nicht gefunden", 0.5)
                return
            
            reg_content = reg_data['content']
            metadata = reg_data['metadata']
            current_status = metadata.get('status', 'Inaktiv')
            
            if current_status == 'Aktiv':
                # Deaktivieren - nutze die echte Deaktivierungs-Methode
                self._deactivate_embedded_registry(reg_id)
            else:
                # Aktivieren - nutze die echte Aktivierungs-Methode
                self._activate_embedded_registry(reg_id)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Toggle der eingebetteten REG {reg_id}: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Toggle fehlgeschlagen: {str(e)}")
    
    def _toggle_file_registry(self, file_path: str):
        """Toggle für dateibasierte Registry-Einträge"""
        try:
            doc_data = self.db.get_documentation(file_path) or {}
            current_status = doc_data.get('status', 'Inaktiv')
            
            if current_status == 'Aktiv':
                # Deaktivieren - nutze die echte Deaktivierungs-Methode
                self._deactivate_file_registry(file_path)
            else:
                # Aktivieren - nutze die echte Aktivierungs-Methode
                self._activate_file_registry(file_path)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Toggle der REG-Datei {file_path}: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Toggle fehlgeschlagen: {str(e)}")
    
    def _create_delete_reg(self, reg_content: str) -> str:
        """Erstellt eine DELETE-Registry-Datei aus dem ursprünglichen Inhalt
        
        Args:
            reg_content: Ursprünglicher Registry-Inhalt
            
        Returns:
            str: DELETE-Registry-Inhalt oder None bei Fehler
        """
        try:
            lines = reg_content.splitlines()
            delete_lines = []
            
            # Header beibehalten
            for line in lines:
                if line.startswith('Windows Registry Editor'):
                    delete_lines.append(line)
                    delete_lines.append('')
                    break
            
            # Keys sammeln und als Lösch-Einträge hinzufügen
            current_key = None
            for line in lines:
                line = line.strip()
                
                # Registry-Key erkannt
                if line.startswith('[') and line.endswith(']'):
                    # Key ohne Klammern extrahieren
                    key_path = line[1:-1]
                    
                    # Lösch-Eintrag erstellen: [-KEY]
                    delete_lines.append(f'[-{key_path}]')
                    delete_lines.append('')
            
            return '\n'.join(delete_lines)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen der DELETE-REG: {e}")
            return None
    
    def _apply_reg_content(self, reg_content: str) -> bool:
        """Registry-Inhalt direkt anwenden
        
        Args:
            reg_content: Registry-Inhalt als String
            
        Returns:
            bool: Erfolg der Operation
        """
        try:
            import tempfile
            import subprocess
            
            # Temporäre REG-Datei erstellen
            with tempfile.NamedTemporaryFile(mode='w', suffix='.reg', delete=False, encoding='utf-16') as temp_file:
                temp_file.write(reg_content)
                temp_file_path = temp_file.name
            
            # Registry-Datei anwenden
            subprocess.run(['regedit', '/s', temp_file_path], check=True)
            
            # Temporäre Datei löschen
            os.unlink(temp_file_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Anwenden der Registry-Inhalte: {e}")
            return False
    
    def _apply_reg_file(self, file_path: str) -> bool:
        """Registry-Datei anwenden
        
        Args:
            file_path: Pfad zur .reg-Datei
            
        Returns:
            bool: Erfolg der Operation
        """
        try:
            import subprocess
            subprocess.run(['regedit', '/s', file_path], check=True)
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Anwenden der Registry-Datei {file_path}: {e}")
            return False
    
    def _deactivate_registry_file(self, file_path: str):
        """Registry-Datei deaktivieren über Backup-Wiederherstellung"""
        try:
            filename = os.path.basename(file_path)
            
            # Verfügbare Backups für diese Datei finden
            backups = self.backup_manager.list_backups()
            relevant_backups = [
                backup for backup in backups 
                if backup.get('reg_file') == filename
            ]
            
            if not relevant_backups:
                # Kein Backup gefunden - manuelle Deaktivierung vorschlagen
                result = messagebox.askyesno(
                    "Kein Backup gefunden",
                    f"Für '{filename}' wurde kein Backup gefunden.\n\n"
                    "Möchten Sie trotzdem versuchen zu deaktivieren?\n"
                    "(Dies erstellt einen neuen Registry-Export als Backup)"
                )
                
                if result:
                    # Aktuellen Zustand als Backup speichern
                    backup_id = self.backup_manager.create_backup(
                        file_path,
                        f"Backup vor Deaktivierung von {filename}"
                    )
                    
                    if backup_id:
                        messagebox.showinfo(
                            "Backup erstellt",
                            f"Aktueller Zustand wurde als Backup gespeichert: {backup_id}\n\n"
                            "Zum Deaktivieren erstellen Sie eine entsprechende Revert-.reg Datei\n"
                            "oder verwenden Sie die Backup-Wiederherstellung."
                        )
                    else:
                        messagebox.showerror(
                            "Fehler",
                            "Konnte kein Backup erstellen. Deaktivierung abgebrochen."
                        )
                return
            
            # Backup-Auswahl anzeigen
            self._show_backup_selection_for_restore(file_path, relevant_backups)
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Deaktivierung von {file_path}: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Fehler bei der Deaktivierung: {e}", 0.5)
    
    def _show_backup_selection_for_restore(self, file_path: str, backups: list):
        """Backup-Auswahl für Wiederherstellung anzeigen"""
        filename = os.path.basename(file_path)
        
        # Backup-Auswahl-Dialog
        backup_window = tk.Toplevel(self.root)
        backup_window.title(f"Deaktivierung von {filename}")
        backup_window.geometry("500x300")
        backup_window.transient(self.root)
        backup_window.grab_set()
        
        ttk.Label(backup_window, text=f"Backup für Deaktivierung von '{filename}' auswählen:", 
                 font=("Arial", 10, "bold")).pack(pady=10)
        
        # Backup-Liste
        list_frame = ttk.Frame(backup_window)
        list_frame.pack(fill='both', expand=True, padx=10)
        
        backup_tree = ttk.Treeview(list_frame, columns=('date', 'description'), show='headings', height=8)
        backup_tree.heading('date', text='Datum')
        backup_tree.heading('description', text='Beschreibung')
        
        # Backups hinzufügen (neueste zuerst)
        for backup in sorted(backups, key=lambda x: x['datetime'], reverse=True):
            date_str = datetime.fromisoformat(backup['datetime']).strftime('%d.%m.%Y %H:%M')
            backup_tree.insert('', 'end', values=(
                date_str,
                backup['description']
            ), tags=(backup['id'],))
        
        backup_tree.pack(fill='both', expand=True)
        
        # Info-Text
        info_label = ttk.Label(backup_window, 
                              text="⚠ Wählen Sie ein Backup VOR der Aktivierung aus",
                              foreground='orange')
        info_label.pack(pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(backup_window)
        btn_frame.pack(fill='x', padx=10, pady=5)
        
        def restore_selected():
            selection = backup_tree.selection()
            if not selection:
                AutoCloseMessageBox.showerror("Warnung", "Bitte wählen Sie ein Backup aus", 0.5)
                return
            
            backup_id = backup_tree.item(selection[0])['tags'][0]
            
            result = messagebox.askyesno(
                "Backup wiederherstellen",
                f"Möchten Sie '{filename}' durch Wiederherstellung des Backups deaktivieren?\n\n"
                "⚠ Dies überschreibt die aktuellen Registry-Einstellungen!"
            )
            
            if result:
                if self.backup_manager.restore_backup(backup_id):
                    # Status in Datenbank aktualisieren
                    doc_data = self.db.get_documentation(file_path) or {}
                    doc_data['status'] = 'Inaktiv'
                    self.db.save_documentation(file_path, doc_data)
                    
                    AutoCloseMessageBox.showinfo("Erfolg", f"✓ '{filename}' wurde deaktiviert!", 0.5)
                    backup_window.destroy()
                    self._apply_filters()  # Sammlung aktualisieren
                else:
                    AutoCloseMessageBox.showerror("Fehler", "Backup konnte nicht wiederhergestellt werden", 0.5)
        
        ttk.Button(btn_frame, text="Wiederherstellen", command=restore_selected).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Abbrechen", command=backup_window.destroy).pack(side='right', padx=5)
    
    def _background_status_check(self):
        """Status-Prüfung im Hintergrund für Dateien mit unbekanntem Status"""
        try:
            reg_files_dir = Path(__file__).parent.parent.parent / "reg_files"
            unknown_files = []
            
            # Dateien mit unbekanntem Status finden
            for reg_file in reg_files_dir.glob("*.reg"):
                doc_data = self.db.get_documentation(str(reg_file))
                if not doc_data or doc_data.get('status') == 'Unbekannt':
                    unknown_files.append(reg_file)
            
            if unknown_files:
                # Nur die ersten 3 Dateien prüfen um die GUI nicht zu blockieren
                for reg_file in unknown_files[:3]:
                    try:
                        status_data = self.status_checker.check_file_status(str(reg_file), self.db)
                        doc_data = self.db.get_documentation(str(reg_file)) or {}
                        
                        if status_data and 'overall_status' in status_data:
                            if status_data['overall_status'] == 'all_active':
                                doc_data['status'] = 'Aktiv'
                            elif status_data['overall_status'] == 'all_inactive':
                                doc_data['status'] = 'Inaktiv'
                            elif status_data['overall_status'] == 'partial':
                                doc_data['status'] = 'Teilweise'
                            else:
                                doc_data['status'] = 'Unbekannt'
                        else:
                            doc_data['status'] = 'Unbekannt'
                        
                        self.db.save_documentation(str(reg_file), doc_data)
                        
                    except Exception as e:
                        self.logger.warning(f"Hintergrund-Status-Prüfung für {reg_file.name} fehlgeschlagen: {e}")
                
                # Anzeige aktualisieren
                self._apply_filters()
                
                # Fortsetzung planen falls noch mehr Dateien zu prüfen sind
                if len(unknown_files) > 3:
                    self.root.after(3000, self._background_status_check)  # In 3 Sekunden weitermachen
                else:
                    # Alle fertig
                    file_count = len(list(reg_files_dir.glob("*.reg")))
                    self.status_text.set(f"Sammlung komplett - {file_count} Dateien, Status geprüft")
            
        except Exception as e:
            self.logger.error(f"Fehler bei Hintergrund-Status-Prüfung: {e}")
    
    def _update_category_filter(self):
        """Kategorie-Filter mit verfügbaren Kategorien aktualisieren"""
        categories = [''] + self.db.get_categories()
        self.category_filter.configure(values=categories)
    
    def _get_status_icon(self, status: str) -> str:
        """Status-Icon für die Anzeige"""
        status_icons = {
            'aktiv': '✅',
            'active': '✅',
            'inaktiv': '❌',
            'inactive': '❌',
            'teilweise': '🔶',
            'partial': '🔶',
            'unbekannt': '❓',
            'unknown': '❓',
            'error': '⚠️',
            'fehler': '⚠️'
        }
        return status_icons.get(status.lower(), '❓')
    
    def _embed_reg_file(self):
        """REG-Datei in die Datenbank einbetten (Datei bleibt erhalten)"""
        # REG-Datei auswählen
        files = filedialog.askopenfilenames(
            title="REG-Dateien zum Einbetten auswählen",
            filetypes=[("Registry-Dateien", "*.reg"), ("Alle Dateien", "*.*")]
        )
        
        self._embed_reg_files_internal(files)
    
    def _embed_reg_files_internal(self, files):
        """Interne Funktion zum Einbetten"""
        if not files:
            return
        
        embedded_count = 0
        errors = []
        
        for file_path in files:
            try:
                file_path = Path(file_path)
                
                # REG-Datei einlesen mit mehreren Encoding-Versuchen
                reg_content = None
                encodings = ['utf-8-sig', 'utf-16', 'cp1252', 'latin1']
                
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            reg_content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                
                if reg_content is None:
                    errors.append(f"{file_path.name}: Encoding-Fehler")
                    continue
                
                # Automatische Analyse
                analysis = self.content_analyzer.analyze_file(str(file_path))
                
                # Eindeutige ID generieren
                reg_id = f"embedded_{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Metadaten erstellen
                metadata = {
                    'name': analysis.get('formatted_name', file_path.stem),
                    'description': analysis.get('description', 'Keine Beschreibung verfügbar'),
                    'category': analysis.get('category', 'Sonstiges'),
                    'original_file': str(file_path),
                    'file_size': file_path.stat().st_size,
                    'status': 'Inaktiv',
                    'created_date': datetime.now().isoformat(),
                    'embedded': True
                }
                
                # In Datenbank einbetten (mit Content!)
                if self.db.embed_reg_file(reg_id, reg_content, metadata):
                    # Datei NICHT mehr löschen - bleibt auf Festplatte
                    embedded_count += 1
                    self.logger.info(f"REG-Datei eingebettet (Datei bleibt erhalten): {file_path}")
                else:
                    errors.append(f"Fehler beim Einbetten: {file_path.name}")
                
            except Exception as e:
                errors.append(f"{file_path.name}: {str(e)}")
                self.logger.error(f"Fehler beim Einbetten von {file_path}: {e}")
        
        # Ergebnis anzeigen
        if embedded_count > 0:
            AutoCloseMessageBox.showsuccess(
                "Einbetten erfolgreich", 
                f"{embedded_count} REG-Datei(en) wurden in die Datenbank eingebettet"
            )
        
        if errors:
            error_msg = "Fehler beim Einbetten:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                error_msg += f"\n... und {len(errors) - 5} weitere"
            AutoCloseMessageBox.showerror("Fehler", error_msg)
        
        # Sammlung aktualisieren
        self._refresh_collection()
    
    def _show_settings(self):
        """Einstellungsfenster anzeigen"""
        try:
            from src.gui.settings_window import SettingsWindow
            SettingsWindow(self.root)
        except Exception as e:
            self.logger.error(f"Fehler beim Öffnen der Einstellungen: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Einstellungen konnten nicht geöffnet werden: {e}")
    
    def _reload_settings(self):
        """Einstellungen neu laden (wird von SettingsWindow aufgerufen)"""
        self.logger.info("Einstellungen wurden neu geladen")
        AutoCloseMessageBox.showsuccess("Einstellungen", "Neue Einstellungen wurden übernommen")
    
    def _simple_activate(self):
        """Einfache Aktivierung: Wähle Datei aus und aktiviere sie"""
        print("DEBUG: _simple_activate aufgerufen")
        selection = self.collection_tree.selection()
        if not selection:
            AutoCloseMessageBox.showerror("Fehler", "Bitte wählen Sie zuerst eine Registry-Datei aus", 5.0)
            return

        item = self.collection_tree.item(selection[0])
        file_path = item['tags'][0] if item['tags'] else None
        print(f"DEBUG: Gewählte Datei: {file_path}")

        if not file_path:
            AutoCloseMessageBox.showerror("Fehler", "Keine Datei-Information gefunden", 5.0)
            return

        try:
            if file_path.startswith("embedded:"):
                reg_id = file_path.replace("embedded:", "")
                print(f"DEBUG: Aktiviere embedded REG: {reg_id}")
                self._activate_embedded_registry(reg_id)
            else:
                print(f"DEBUG: Aktiviere File REG: {file_path}")
                self._activate_file_registry(file_path)
        except Exception as e:
            print(f"DEBUG: Exception in _simple_activate: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Aktivierung fehlgeschlagen: {str(e)}", 5.0)
    
    def _simple_deactivate(self):
        """Einfache Deaktivierung: Wähle Datei aus und deaktiviere sie"""
        selection = self.collection_tree.selection()
        if not selection:
            AutoCloseMessageBox.showerror("Fehler", "Bitte wählen Sie zuerst eine Registry-Datei aus")
            return
        
        item = self.collection_tree.item(selection[0])
        file_path = item['tags'][0] if item['tags'] else None
        
        if not file_path:
            AutoCloseMessageBox.showerror("Fehler", "Keine Datei-Information gefunden")
            return
        
        try:
            if file_path.startswith("embedded:"):
                reg_id = file_path.replace("embedded:", "")
                self._deactivate_embedded_registry(reg_id)
            else:
                self._deactivate_file_registry(file_path)
        except Exception as e:
            AutoCloseMessageBox.showerror("Fehler", f"Deaktivierung fehlgeschlagen: {str(e)}")
    
    def _delete_entry(self):
        """Eintrag aus der Liste löschen"""
        selection = self.collection_tree.selection()
        if not selection:
            AutoCloseMessageBox.showerror("Fehler", "Bitte wählen Sie zuerst einen Eintrag aus", 3.0)
            return
        
        item = self.collection_tree.item(selection[0])
        file_path = item['tags'][0] if item['tags'] else None
        
        if not file_path:
            AutoCloseMessageBox.showerror("Fehler", "Keine Datei-Information gefunden", 3.0)
            return
        
        # Bestätigungsdialog
        if file_path.startswith("embedded:"):
            reg_id = file_path.replace("embedded:", "")
            reg_data = self.db.get_embedded_reg(reg_id)
            name = reg_data['metadata'].get('name', reg_id) if reg_data else reg_id
            
            result = messagebox.askyesno(
                "Löschen bestätigen", 
                f"Möchten Sie '{name}' wirklich löschen?\n\n"
                "Der eingebettete REG-Eintrag wird aus der Datenbank entfernt.\n"
                "Dieser Vorgang kann nicht rückgängig gemacht werden."
            )
            
            if result:
                # Embedded REG löschen
                if self.db.delete_embedded_reg(reg_id):
                    AutoCloseMessageBox.showsuccess("Gelöscht", f"'{name}' wurde gelöscht", 2.0)
                    self._refresh_collection()
                else:
                    AutoCloseMessageBox.showerror("Fehler", "Löschen fehlgeschlagen", 3.0)
        else:
            # Normale REG-Datei von Festplatte löschen
            filename = os.path.basename(file_path)
            
            result = messagebox.askyesno(
                "Löschen bestätigen",
                f"Möchten Sie '{filename}' wirklich löschen?\n\n"
                "⚠️ DIE DATEI WIRD DAUERHAFT VON DER FESTPLATTE GELÖSCHT!\n"
                "Dieser Vorgang kann nicht rückgängig gemacht werden."
            )
            
            if result:
                try:
                    # Datei von Festplatte löschen
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        self.logger.info(f"Datei gelöscht: {file_path}")
                    
                    # Dokumentation löschen
                    self.db.delete_documentation(file_path)
                    
                    AutoCloseMessageBox.showsuccess("Gelöscht", f"'{filename}' wurde dauerhaft gelöscht", 2.0)
                    self._refresh_collection()
                except Exception as e:
                    self.logger.error(f"Fehler beim Löschen: {e}")
                    AutoCloseMessageBox.showerror("Fehler", f"Datei konnte nicht gelöscht werden: {str(e)}", 3.0)
    
    def _activate_embedded_registry(self, reg_id: str):
        """Eingebettete Registry aktivieren"""
        try:
            reg_data = self.db.get_embedded_reg(reg_id)
            if not reg_data:
                AutoCloseMessageBox.showerror("Fehler", "REG-Daten nicht gefunden")
                return
            
            reg_content = reg_data['content']
            metadata = reg_data['metadata']
            
            # Backup erstellen (temporäre REG-Datei für Backup)
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.reg', delete=False, encoding='utf-16') as temp_file:
                temp_file.write(reg_content)
                temp_file_path = temp_file.name
            
            backup_id = self.backup_manager.create_backup(temp_file_path, f"Vor Aktivierung von {metadata.get('name', reg_id)}")
            
            # Registry-Inhalt anwenden
            if self._apply_reg_content(reg_content):
                metadata['status'] = 'Aktiv'
                metadata['last_applied'] = datetime.now().isoformat()
                self.db.update_usage_count(reg_id)
                self.db.update_metadata(reg_id, metadata)
                AutoCloseMessageBox.showsuccess("Aktiviert", f"{metadata.get('name', reg_id)} wurde aktiviert")
                self._refresh_collection()
            else:
                AutoCloseMessageBox.showerror("Fehler", "Aktivierung fehlgeschlagen")
            
            # Temp-Datei löschen
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
        except Exception as e:
            self.logger.error(f"Fehler beim Aktivieren der embedded Registry {reg_id}: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Aktivierung fehlgeschlagen: {str(e)}")
    
    def _deactivate_embedded_registry_old(self, reg_id: str):
        """Eingebettete Registry deaktivieren"""
        try:
            reg_data = self.db.get_embedded_reg(reg_id)
            if not reg_data:
                AutoCloseMessageBox.showerror("Fehler", "REG-Daten nicht gefunden")
                return
            
            reg_content = reg_data['content']
            metadata = reg_data['metadata']
            
            # Backup erstellen (temporäre REG-Datei für Backup)
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.reg', delete=False, encoding='utf-16') as temp_file:
                temp_file.write(reg_content)
                temp_file_path = temp_file.name
            
            backup_id = self.backup_manager.create_backup(temp_file_path, f"Vor Deaktivierung von {metadata.get('name', reg_id)}")
            
            # Registry-Einträge löschen
            if self._delete_reg_keys(reg_content):
                metadata['status'] = 'Inaktiv'
                self.db.update_metadata(reg_id, metadata)
                AutoCloseMessageBox.showsuccess("Deaktiviert", f"{metadata.get('name', reg_id)} wurde deaktiviert")
                self._refresh_collection()
            else:
                AutoCloseMessageBox.showerror("Fehler", "Deaktivierung fehlgeschlagen")
            
            # Temp-Datei löschen
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
        except Exception as e:
            self.logger.error(f"Fehler beim Deaktivieren der embedded Registry {reg_id}: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Deaktivierung fehlgeschlagen: {str(e)}")
    
    def _activate_embedded_registry_old(self, reg_id: str):
        """Eingebettete Registry aktivieren"""
        try:
            reg_data = self.db.get_embedded_reg(reg_id)
            if not reg_data:
                AutoCloseMessageBox.showerror("Fehler", "REG-Daten nicht gefunden")
                return
            
            reg_content = reg_data['content']
            metadata = reg_data['metadata']
            
            # Backup erstellen (temporäre REG-Datei für Backup)
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.reg', delete=False, encoding='utf-16') as temp_file:
                temp_file.write(reg_content)
                temp_file_path = temp_file.name
            
            backup_id = self.backup_manager.create_backup(temp_file_path, f"Vor Aktivierung von {metadata.get('name', reg_id)}")
            
            # Registry-Inhalt anwenden
            if self._apply_reg_content(reg_content):
                metadata['status'] = 'Aktiv'
                metadata['last_applied'] = datetime.now().isoformat()
                self.db.update_usage_count(reg_id)
                self.db.update_metadata(reg_id, metadata)
                AutoCloseMessageBox.showsuccess("Aktiviert", f"{metadata.get('name', reg_id)} wurde aktiviert")
                self._refresh_collection()
            else:
                AutoCloseMessageBox.showerror("Fehler", "Aktivierung fehlgeschlagen")
            
            # Temp-Datei löschen
            import os
            os.unlink(temp_file_path)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktivieren der eingebetteten REG {reg_id}: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Aktivierung fehlgeschlagen: {str(e)}")
    
    def _deactivate_embedded_registry(self, reg_id: str):
        """Eingebettete Registry deaktivieren"""
        try:
            reg_data = self.db.get_embedded_reg(reg_id)
            if not reg_data:
                AutoCloseMessageBox.showerror("Fehler", "REG-Daten nicht gefunden")
                return
            
            reg_content = reg_data['content']
            metadata = reg_data['metadata']
            
            # Backup erstellen vor Deaktivierung
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(mode='w', suffix='.reg', delete=False, encoding='utf-16') as temp_file:
                temp_file.write(reg_content)
                temp_file_path = temp_file.name
            
            backup_id = self.backup_manager.create_backup(temp_file_path, f"Vor Deaktivierung von {metadata.get('name', reg_id)}")
            
            # Registry-Einträge löschen durch Erstellen einer "Delete"-REG-Datei
            delete_reg_content = self._create_delete_reg(reg_content)
            
            if delete_reg_content and self._apply_reg_content(delete_reg_content):
                metadata['status'] = 'Inaktiv'
                self.db.embed_reg_file(reg_id, reg_data['content'], metadata)
                AutoCloseMessageBox.showsuccess("Deaktiviert", f"{metadata.get('name', reg_id)} wurde deaktiviert")
                self._refresh_collection()
            else:
                AutoCloseMessageBox.showerror("Fehler", "Deaktivierung fehlgeschlagen")
            
            # Temp-Datei löschen
            os.unlink(temp_file_path)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Deaktivieren der eingebetteten REG {reg_id}: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Deaktivierung fehlgeschlagen: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Deaktivieren der eingebetteten REG {reg_id}: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Deaktivierung fehlgeschlagen: {str(e)}")
    
    def _activate_file_registry(self, file_path: str):
        """Dateibasierte Registry aktivieren"""
        try:
            if not os.path.exists(file_path):
                AutoCloseMessageBox.showerror("Fehler", "Datei nicht gefunden")
                return
            
            # Backup erstellen
            backup_id = self.backup_manager.create_backup(file_path, f"Vor Aktivierung von {os.path.basename(file_path)}")
            
            # Registry-Datei anwenden
            if self._apply_reg_file(file_path):
                doc_data = self.db.get_documentation(file_path) or {}
                doc_data['status'] = 'Aktiv'
                doc_data['last_applied'] = datetime.now().isoformat()
                self.db.save_documentation(file_path, doc_data)
                AutoCloseMessageBox.showsuccess("Aktiviert", f"{os.path.basename(file_path)} wurde aktiviert")
                self._refresh_collection()
            else:
                AutoCloseMessageBox.showerror("Fehler", "Aktivierung fehlgeschlagen")
                
        except Exception as e:
            self.logger.error(f"Fehler beim Aktivieren der REG-Datei {file_path}: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Aktivierung fehlgeschlagen: {str(e)}")
    
    def _deactivate_file_registry(self, file_path: str):
        """Dateibasierte Registry deaktivieren"""
        try:
            if not os.path.exists(file_path):
                AutoCloseMessageBox.showerror("Fehler", "Datei nicht gefunden")
                return
            
            # REG-Datei lesen
            encodings = ['utf-8-sig', 'utf-16', 'utf-8', 'cp1252', 'latin1']
            reg_content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        reg_content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if not reg_content:
                AutoCloseMessageBox.showerror("Fehler", "Datei konnte nicht gelesen werden")
                return
            
            # Backup erstellen
            backup_id = self.backup_manager.create_backup(file_path, f"Vor Deaktivierung von {os.path.basename(file_path)}")
            
            # DELETE-REG erstellen und anwenden
            delete_reg_content = self._create_delete_reg(reg_content)
            
            if delete_reg_content and self._apply_reg_content(delete_reg_content):
                doc_data = self.db.get_documentation(file_path) or {}
                doc_data['status'] = 'Inaktiv'
                self.db.save_documentation(file_path, doc_data)
                AutoCloseMessageBox.showsuccess("Deaktiviert", f"{os.path.basename(file_path)} wurde deaktiviert")
                self._refresh_collection()
            else:
                AutoCloseMessageBox.showerror("Fehler", "Deaktivierung fehlgeschlagen")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Deaktivieren der REG-Datei {file_path}: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Deaktivierung fehlgeschlagen: {str(e)}")
    
    def _context_show_details(self):
        """Details über Kontextmenü anzeigen"""
        selection = self.collection_tree.selection()
        if selection:
            item = self.collection_tree.item(selection[0])
            file_path = item['tags'][0] if item['tags'] else None
            if file_path:
                self._load_reg_file(file_path)
    
    def _context_edit(self):
        """Bearbeiten über Kontextmenü"""
        # TODO: Editor öffnen
        AutoCloseMessageBox.showinfo("Info", "Editor-Funktion wird in der nächsten Version verfügbar sein")
    
    def _context_create_backup(self):
        """Backup über Kontextmenü erstellen"""
        selection = self.collection_tree.selection()
        if not selection:
            return
        
        item = self.collection_tree.item(selection[0])
        file_path = item['tags'][0] if item['tags'] else None
        
        if not file_path or file_path.startswith("embedded:"):
            AutoCloseMessageBox.showinfo("Info", "Backup nur für dateibasierte Registry-Einträge möglich")
            return
        
        try:
            backup_id = self.backup_manager.create_backup(file_path, f"Manuelles Backup von {os.path.basename(file_path)}")
            if backup_id:
                AutoCloseMessageBox.showsuccess("Backup erstellt", f"Backup {backup_id} wurde erstellt")
            else:
                AutoCloseMessageBox.showerror("Fehler", "Backup konnte nicht erstellt werden")
        except Exception as e:
            AutoCloseMessageBox.showerror("Fehler", f"Backup-Fehler: {str(e)}")
    
    def _context_refresh_status(self):
        """Status über Kontextmenü aktualisieren"""
        selection = self.collection_tree.selection()
        if not selection:
            return
        
        item = self.collection_tree.item(selection[0])
        file_path = item['tags'][0] if item['tags'] else None
        
        if not file_path or file_path.startswith("embedded:"):
            AutoCloseMessageBox.showinfo("Info", "Status-Prüfung nur für dateibasierte Registry-Einträge möglich")
            return
        
        try:
            # Status neu prüfen
            status_data = self.status_checker.check_file_status(file_path, self.db)
            doc_data = self.db.get_documentation(file_path) or {}
            
            if status_data and 'overall_status' in status_data:
                if status_data['overall_status'] == 'all_active':
                    doc_data['status'] = 'Aktiv'
                elif status_data['overall_status'] == 'all_inactive':
                    doc_data['status'] = 'Inaktiv'
                elif status_data['overall_status'] == 'partial':
                    doc_data['status'] = 'Teilweise'
                else:
                    doc_data['status'] = 'Unbekannt'
            else:
                doc_data['status'] = 'Unbekannt'
            
            self.db.save_documentation(file_path, doc_data)
            self._refresh_collection()
            AutoCloseMessageBox.showsuccess("Status aktualisiert", f"Status für {os.path.basename(file_path)} wurde aktualisiert")
            
        except Exception as e:
            AutoCloseMessageBox.showerror("Fehler", f"Status-Prüfung fehlgeschlagen: {str(e)}")
    
    def _restart_explorer(self):
        """Windows Explorer neu starten"""
        if messagebox.askyesno(
            "Explorer neu starten",
            "Windows Explorer wird neugestartet.\n\n"
            "Dies kann helfen wenn Kontextmenü-Änderungen nicht sichtbar sind.\n\n"
            "Fortfahren?"
        ):
            self.logger.info("Benutzer startet Explorer neu")
            
            if SystemRestart.restart_explorer():
                AutoCloseMessageBox.showsuccess(
                    "Explorer neugestartet",
                    "Windows Explorer wurde erfolgreich neugestartet"
                )
            else:
                AutoCloseMessageBox.showerror(
                    "Fehler",
                    "Explorer konnte nicht neugestartet werden"
                )
    
    def _restart_windows(self):
        """Windows neu starten mit Auto-Wiederstart der App"""
        result = messagebox.askyesnocancel(
            "Windows neu starten",
            "Windows wird neu gestartet.\n\n"
            "Dieses Programm wird nach dem Neustart automatisch wieder geöffnet "
            "und zeigt den aktualisierten Status aller Registry-Einträge.\n\n"
            "⏱️ Countdown: 30 Sekunden\n\n"
            "Ja = Jetzt neu starten (30 Sek. Countdown)\n"
            "Nein = Abbrechen"
        )
        
        if result:  # Ja geklickt
            self.logger.info("Benutzer startet Windows neu mit Auto-Restart")
            
            # Neustart initiieren
            if SystemRestart.restart_windows(countdown_seconds=30):
                # Countdown-Dialog anzeigen
                countdown_dialog = tk.Toplevel(self.root)
                countdown_dialog.title("Windows wird neu gestartet...")
                countdown_dialog.geometry("400x150")
                countdown_dialog.transient(self.root)
                countdown_dialog.grab_set()
                
                info_label = ttk.Label(
                    countdown_dialog,
                    text="Windows wird in 30 Sekunden neu gestartet.\n\n"
                         "Registry Manager wird nach dem Neustart\n"
                         "automatisch wieder geöffnet.",
                    justify=tk.CENTER
                )
                info_label.pack(pady=20)
                
                # Abbrechen Button
                def abort_restart():
                    if SystemRestart.cancel_restart():
                        AutoCloseMessageBox.showinfo(
                            "Abgebrochen",
                            "Neustart wurde abgebrochen"
                        )
                        countdown_dialog.destroy()
                    else:
                        AutoCloseMessageBox.showerror(
                            "Fehler",
                            "Neustart konnte nicht abgebrochen werden"
                        )
                
                ttk.Button(
                    countdown_dialog,
                    text="❌ Neustart abbrechen",
                    command=abort_restart
                ).pack(pady=10)
                
                # App nach 5 Sekunden schließen (damit sie sauber beendet wird)
                def close_app():
                    countdown_dialog.destroy()
                    self.root.quit()
                
                self.root.after(5000, close_app)
                
            else:
                AutoCloseMessageBox.showerror(
                    "Fehler",
                    "Windows-Neustart konnte nicht initiiert werden"
                )
    
    def _create_group(self):
        """Neue Gruppe erstellen"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Neue Gruppe erstellen")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Gruppenname:", font=("Arial", 10, "bold")).pack(pady=(10, 5))
        name_var = tk.StringVar()
        name_entry = ttk.Entry(dialog, textvariable=name_var, width=40)
        name_entry.pack(pady=5)
        name_entry.focus()
        
        ttk.Label(dialog, text="Beschreibung (optional):").pack(pady=(10, 5))
        desc_var = tk.StringVar()
        desc_entry = ttk.Entry(dialog, textvariable=desc_var, width=40)
        desc_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Icon:").pack(pady=(10, 5))
        icon_var = tk.StringVar(value="📁")
        icon_frame = ttk.Frame(dialog)
        icon_frame.pack(pady=5)
        
        icons = ["📁", "📂", "🗂️", "📋", "⭐", "🎯", "🔧", "⚙️", "🎨", "🚀"]
        for icon in icons:
            ttk.Button(icon_frame, text=icon, width=3, 
                      command=lambda i=icon: icon_var.set(i)).pack(side=tk.LEFT, padx=2)
        
        def create():
            name = name_var.get().strip()
            if not name:
                AutoCloseMessageBox.showerror("Fehler", "Bitte Gruppennamen eingeben")
                return
            
            group_id = self.db.create_group(name, desc_var.get(), icon=icon_var.get())
            if group_id:
                AutoCloseMessageBox.showsuccess("Erfolg", f"Gruppe '{name}' wurde erstellt")
                dialog.destroy()
                self._refresh_collection()
            else:
                AutoCloseMessageBox.showerror("Fehler", f"Gruppe '{name}' existiert bereits")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=15)
        ttk.Button(button_frame, text="Erstellen", command=create).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Abbrechen", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Enter-Taste zum Erstellen
        dialog.bind('<Return>', lambda e: create())
    
    def _add_to_group(self, reg_id: str, group_id: str):
        """REG zu Gruppe hinzufügen (GRUPPENWECHSEL - entfernt aus anderen Gruppen)"""
        try:
            # WICHTIG: Erst aus ALLEN anderen Gruppen entfernen (Gruppenwechsel!)
            current_groups = self.db.get_reg_groups(reg_id)
            for old_group_id in current_groups:
                if old_group_id != group_id:  # Nicht die Zielgruppe entfernen
                    self.db.remove_reg_from_group(reg_id, old_group_id)
                    self.logger.info(f"REG {reg_id} aus alter Gruppe {old_group_id} entfernt (Gruppenwechsel)")
            
            # Jetzt zur neuen Gruppe hinzufügen
            if self.db.add_reg_to_group(reg_id, group_id):
                # Gruppenname holen
                groups = self.db.list_groups()
                group_name = next((g['name'] for g in groups if g['id'] == group_id), "Gruppe")
                
                AutoCloseMessageBox.showsuccess("Erfolg", f"Zur Gruppe '{group_name}' verschoben")
                self._refresh_collection()
            else:
                AutoCloseMessageBox.showerror("Fehler", "Konnte nicht zur Gruppe hinzufügen")
        except Exception as e:
            self.logger.error(f"Fehler beim Gruppenwechsel: {e}")
            AutoCloseMessageBox.showerror("Fehler", f"Gruppenwechsel fehlgeschlagen: {str(e)}")
    
    def _remove_from_group(self, reg_id: str, group_id: str):
        """REG aus Gruppe entfernen"""
        if self.db.remove_reg_from_group(reg_id, group_id):
            # Gruppenname holen
            groups = self.db.list_groups()
            group_name = next((g['name'] for g in groups if g['id'] == group_id), "Gruppe")
            
            AutoCloseMessageBox.showsuccess("Erfolg", f"Aus Gruppe '{group_name}' entfernt")
            self._refresh_collection()
        else:
            AutoCloseMessageBox.showerror("Fehler", "Konnte nicht aus Gruppe entfernen")


