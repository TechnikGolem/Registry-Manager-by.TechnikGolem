"""
Registry File Editor
===================

Dialog zum Erstellen und Bearbeiten von Registry-Files.
"""

import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog
import logging
from typing import Optional, Dict
from pathlib import Path

from src.registry.reg_creator import RegFileCreator


class RegFileEditor:
    """Editor-Dialog für Registry-Files"""
    
    def __init__(self, parent, reg_creator: RegFileCreator):
        self.parent = parent
        self.reg_creator = reg_creator
        self.logger = logging.getLogger(__name__)
        
        self.window = None
        self.result_file = None
        
        # Daten für die Registry-Einträge
        self.registry_entries = []
        
        self._create_window()
        self._setup_ui()
    
    def _create_window(self):
        """Editor-Fenster erstellen"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Registry-Datei erstellen")
        self.window.geometry("800x600")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Zentrieren
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.window.winfo_screenheight() // 2) - (600 // 2)
        self.window.geometry(f"800x600+{x}+{y}")
    
    def _setup_ui(self):
        """Benutzeroberfläche einrichten"""
        # Hauptcontainer
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Notebook für Tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Datei-Informationen
        self.info_frame = ttk.Frame(notebook)
        notebook.add(self.info_frame, text="Datei-Informationen")
        
        # Tab 2: Registry-Einträge
        self.entries_frame = ttk.Frame(notebook)
        notebook.add(self.entries_frame, text="Registry-Einträge")
        
        # Tab 3: Vorlagen
        self.templates_frame = ttk.Frame(notebook)
        notebook.add(self.templates_frame, text="Vorlagen")
        
        # Tab 4: Vorschau
        self.preview_frame = ttk.Frame(notebook)
        notebook.add(self.preview_frame, text="Vorschau")
        
        self._setup_info_tab()
        self._setup_entries_tab()
        self._setup_templates_tab()
        self._setup_preview_tab()
        
        # Button-Leiste
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Abbrechen", command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Speichern", command=self._save).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Vorschau aktualisieren", command=self._update_preview).pack(side=tk.LEFT)
    
    def _setup_info_tab(self):
        """Datei-Informationen Tab einrichten"""
        # Dateiname und Pfad
        file_group = ttk.LabelFrame(self.info_frame, text="Datei")
        file_group.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(file_group, text="Dateiname:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.filename_var = tk.StringVar()
        filename_frame = ttk.Frame(file_group)
        filename_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        file_group.columnconfigure(1, weight=1)
        
        self.filename_entry = ttk.Entry(filename_frame, textvariable=self.filename_var)
        self.filename_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(filename_frame, text=".reg").pack(side=tk.RIGHT)
        
        ttk.Label(file_group, text="Speicherort:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        location_frame = ttk.Frame(file_group)
        location_frame.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        
        self.location_var = tk.StringVar()
        self.location_var.set(str(Path(__file__).parent.parent.parent / "reg_files"))
        ttk.Entry(location_frame, textvariable=self.location_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(location_frame, text="...", width=3, command=self._browse_location).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Dokumentation
        doc_group = ttk.LabelFrame(self.info_frame, text="Dokumentation")
        doc_group.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(doc_group, text="Titel:").pack(anchor="w", padx=5, pady=(5, 0))
        self.title_var = tk.StringVar()
        ttk.Entry(doc_group, textvariable=self.title_var).pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(doc_group, text="Kategorie:").pack(anchor="w", padx=5, pady=(5, 0))
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(doc_group, textvariable=self.category_var, values=[
            "System", "Registry-Tweaks", "Sicherheit", "Performance", 
            "UI-Anpassungen", "Netzwerk", "Software", "Sonstiges"
        ])
        self.category_combo.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(doc_group, text="Beschreibung:").pack(anchor="w", padx=5, pady=(5, 0))
        self.description_text = tk.Text(doc_group, height=6, wrap=tk.WORD)
        desc_scrollbar = ttk.Scrollbar(doc_group, orient="vertical", command=self.description_text.yview)
        self.description_text.configure(yscrollcommand=desc_scrollbar.set)
        self.description_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        desc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 5))
    
    def _setup_entries_tab(self):
        """Registry-Einträge Tab einrichten"""
        # Toolbar
        toolbar = ttk.Frame(self.entries_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="Eintrag hinzufügen", command=self._add_entry).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Eintrag bearbeiten", command=self._edit_entry).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Eintrag löschen", command=self._delete_entry).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Separator(toolbar, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="Key löschen", command=self._add_delete_key).pack(side=tk.LEFT, padx=(0, 5))
        
        # Treeview für Einträge
        self.entries_tree = ttk.Treeview(self.entries_frame, columns=("type", "value"), show="tree headings")
        self.entries_tree.heading("#0", text="Registry-Pfad")
        self.entries_tree.heading("type", text="Typ")
        self.entries_tree.heading("value", text="Wert")
        
        self.entries_tree.column("#0", width=400)
        self.entries_tree.column("type", width=100)
        self.entries_tree.column("value", width=200)
        
        # Scrollbars
        entries_scrollbar_v = ttk.Scrollbar(self.entries_frame, orient="vertical", command=self.entries_tree.yview)
        entries_scrollbar_h = ttk.Scrollbar(self.entries_frame, orient="horizontal", command=self.entries_tree.xview)
        self.entries_tree.configure(yscrollcommand=entries_scrollbar_v.set, xscrollcommand=entries_scrollbar_h.set)
        
        self.entries_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        entries_scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 5))
        entries_scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X, padx=5)
        
        # Doppelklick-Handler
        self.entries_tree.bind("<Double-1>", lambda e: self._edit_entry())
    
    def _setup_templates_tab(self):
        """Vorlagen Tab einrichten"""
        # Beschreibung
        desc_label = ttk.Label(self.templates_frame, 
                              text="Wählen Sie eine Vorlage aus, um schnell häufige Registry-Änderungen zu erstellen:",
                              wraplength=750)
        desc_label.pack(anchor="w", padx=5, pady=5)
        
        # Template-Liste
        templates_frame = ttk.Frame(self.templates_frame)
        templates_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.templates_listbox = tk.Listbox(templates_frame, height=15)
        templates_scrollbar = ttk.Scrollbar(templates_frame, orient="vertical", command=self.templates_listbox.yview)
        self.templates_listbox.configure(yscrollcommand=templates_scrollbar.set)
        
        # Templates hinzufügen
        self.template_data = {
            "Windows Defender deaktivieren": "disable_windows_defender",
            "Desktop-Icons ausblenden": "hide_desktop_icons", 
            "Cortana deaktivieren": "disable_cortana",
            "Dunkles Theme aktivieren": "dark_theme"
        }
        
        for template_name in self.template_data.keys():
            self.templates_listbox.insert(tk.END, template_name)
        
        self.templates_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        templates_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Template-Buttons
        template_buttons = ttk.Frame(self.templates_frame)
        template_buttons.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(template_buttons, text="Vorlage anwenden", command=self._apply_template).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(template_buttons, text="Vorlage anzeigen", command=self._preview_template).pack(side=tk.LEFT)
    
    def _setup_preview_tab(self):
        """Vorschau Tab einrichten"""
        # Text-Widget für Vorschau
        self.preview_text = tk.Text(self.preview_frame, wrap=tk.NONE, font=("Consolas", 10))
        
        # Scrollbars
        preview_scrollbar_v = ttk.Scrollbar(self.preview_frame, orient="vertical", command=self.preview_text.yview)
        preview_scrollbar_h = ttk.Scrollbar(self.preview_frame, orient="horizontal", command=self.preview_text.xview)
        self.preview_text.configure(yscrollcommand=preview_scrollbar_v.set, xscrollcommand=preview_scrollbar_h.set)
        
        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        preview_scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        preview_scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X, padx=5)
    
    def _browse_location(self):
        """Speicherort durchsuchen"""
        directory = filedialog.askdirectory(
            title="Speicherort auswählen",
            initialdir=self.location_var.get()
        )
        if directory:
            self.location_var.set(directory)
    
    def _add_entry(self):
        """Neuen Registry-Eintrag hinzufügen"""
        dialog = RegEntryDialog(self.window)
        self.window.wait_window(dialog.window)
        
        if hasattr(dialog, 'result') and dialog.result:
            entry_data = dialog.result
            self._add_entry_to_tree(entry_data)
            self.registry_entries.append(entry_data)
            self._update_preview()
    
    def _edit_entry(self):
        """Ausgewählten Eintrag bearbeiten"""
        selection = self.entries_tree.selection()
        if not selection:
            messagebox.showwarning("Warnung", "Bitte wählen Sie einen Eintrag aus.")
            return
        
        # Eintrag-Index finden
        item = self.entries_tree.item(selection[0])
        entry_id = item.get('tags', [None])[0]
        
        if entry_id is not None:
            try:
                entry_index = int(entry_id)
                entry_data = self.registry_entries[entry_index]
                
                dialog = RegEntryDialog(self.window, entry_data)
                self.window.wait_window(dialog.window)
                
                if hasattr(dialog, 'result') and dialog.result:
                    self.registry_entries[entry_index] = dialog.result
                    self._refresh_entries_tree()
                    self._update_preview()
                    
            except (ValueError, IndexError):
                messagebox.showerror("Fehler", "Fehler beim Bearbeiten des Eintrags.")
    
    def _delete_entry(self):
        """Ausgewählten Eintrag löschen"""
        selection = self.entries_tree.selection()
        if not selection:
            messagebox.showwarning("Warnung", "Bitte wählen Sie einen Eintrag aus.")
            return
        
        if messagebox.askyesno("Bestätigung", "Eintrag wirklich löschen?"):
            item = self.entries_tree.item(selection[0])
            entry_id = item.get('tags', [None])[0]
            
            if entry_id is not None:
                try:
                    entry_index = int(entry_id)
                    del self.registry_entries[entry_index]
                    self._refresh_entries_tree()
                    self._update_preview()
                    
                except (ValueError, IndexError):
                    messagebox.showerror("Fehler", "Fehler beim Löschen des Eintrags.")
    
    def _add_delete_key(self):
        """Key-Lösch-Eintrag hinzufügen"""
        dialog = DeleteKeyDialog(self.window)
        self.window.wait_window(dialog.window)
        
        if hasattr(dialog, 'result') and dialog.result:
            delete_data = {
                'action': 'delete_key',
                'key_path': dialog.result
            }
            self.registry_entries.append(delete_data)
            self._refresh_entries_tree()
            self._update_preview()
    
    def _add_entry_to_tree(self, entry_data: Dict):
        """Eintrag zur Treeview hinzufügen"""
        entry_id = len(self.registry_entries) - 1
        
        if entry_data.get('action') == 'delete_key':
            text = f"[-{entry_data['key_path']}]"
            self.entries_tree.insert("", "end", text=text, values=("DELETE_KEY", ""), tags=(str(entry_id),))
        else:
            key_path = entry_data['key_path']
            value_name = entry_data['value_name']
            value_type = entry_data['value_type']
            value_data = entry_data['value_data']
            
            text = f"{key_path}\\{value_name}" if value_name else f"{key_path}\\@"
            value_display = str(value_data)[:50] + "..." if len(str(value_data)) > 50 else str(value_data)
            
            self.entries_tree.insert("", "end", text=text, values=(value_type, value_display), tags=(str(entry_id),))
    
    def _refresh_entries_tree(self):
        """Treeview komplett aktualisieren"""
        self.entries_tree.delete(*self.entries_tree.get_children())
        
        for i, entry_data in enumerate(self.registry_entries):
            if entry_data.get('action') == 'delete_key':
                text = f"[-{entry_data['key_path']}]"
                self.entries_tree.insert("", "end", text=text, values=("DELETE_KEY", ""), tags=(str(i),))
            else:
                key_path = entry_data['key_path']
                value_name = entry_data['value_name']
                value_type = entry_data['value_type']
                value_data = entry_data['value_data']
                
                text = f"{key_path}\\{value_name}" if value_name else f"{key_path}\\@"
                value_display = str(value_data)[:50] + "..." if len(str(value_data)) > 50 else str(value_data)
                
                self.entries_tree.insert("", "end", text=text, values=(value_type, value_display), tags=(str(i),))
    
    def _apply_template(self):
        """Ausgewählte Vorlage anwenden"""
        selection = self.templates_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warnung", "Bitte wählen Sie eine Vorlage aus.")
            return
        
        template_name = self.templates_listbox.get(selection[0])
        template_key = self.template_data[template_name]
        
        template_data = self.reg_creator.get_template_data(template_key)
        if template_data:
            # Template zu Einträgen hinzufügen
            for key_path, key_data in template_data.get('keys', {}).items():
                for value_name, value_info in key_data.get('values', {}).items():
                    entry = {
                        'key_path': key_path,
                        'value_name': value_name,
                        'value_type': value_info['type'],
                        'value_data': value_info['data']
                    }
                    self.registry_entries.append(entry)
            
            # Titel und Beschreibung setzen falls leer
            if not self.title_var.get():
                self.title_var.set(template_name)
            
            if not self.description_text.get(1.0, tk.END).strip():
                descriptions = {
                    "Windows Defender deaktivieren": "Deaktiviert Windows Defender Antivirus",
                    "Desktop-Icons ausblenden": "Blendet alle Desktop-Icons aus", 
                    "Cortana deaktivieren": "Deaktiviert Cortana komplett",
                    "Dunkles Theme aktivieren": "Aktiviert das dunkle Windows-Theme"
                }
                desc = descriptions.get(template_name, f"Vorlage: {template_name}")
                self.description_text.insert(1.0, desc)
            
            self._refresh_entries_tree()
            self._update_preview()
            messagebox.showinfo("Erfolg", f"Vorlage '{template_name}' wurde angewendet.")
    
    def _preview_template(self):
        """Vorlage in der Vorschau anzeigen"""
        selection = self.templates_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warnung", "Bitte wählen Sie eine Vorlage aus.")
            return
        
        template_name = self.templates_listbox.get(selection[0])
        template_key = self.template_data[template_name]
        
        template_data = self.reg_creator.get_template_data(template_key)
        if template_data:
            content = self.reg_creator._generate_content(template_data, template_name, f"Vorlage: {template_name}")
            
            # Vorschau-Fenster
            preview_window = tk.Toplevel(self.window)
            preview_window.title(f"Vorschau: {template_name}")
            preview_window.geometry("600x400")
            
            preview_text = tk.Text(preview_window, wrap=tk.NONE, font=("Consolas", 10))
            preview_scrollbar = ttk.Scrollbar(preview_window, orient="vertical", command=preview_text.yview)
            preview_text.configure(yscrollcommand=preview_scrollbar.set)
            
            preview_text.insert(1.0, content)
            preview_text.config(state=tk.DISABLED)
            
            preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
    
    def _update_preview(self):
        """Vorschau aktualisieren"""
        try:
            # Registry-Daten zusammenstellen
            registry_data = {'keys': {}, 'deleted_keys': []}
            
            for entry in self.registry_entries:
                if entry.get('action') == 'delete_key':
                    registry_data['deleted_keys'].append(entry['key_path'])
                else:
                    key_path = entry['key_path']
                    value_name = entry['value_name']
                    
                    if key_path not in registry_data['keys']:
                        registry_data['keys'][key_path] = {'values': {}}
                    
                    if value_name:  # Benannter Wert
                        registry_data['keys'][key_path]['values'][value_name] = {
                            'type': entry['value_type'],
                            'data': entry['value_data']
                        }
                    else:  # Default-Wert
                        registry_data['keys'][key_path]['default_value'] = {
                            'type': entry['value_type'],
                            'data': entry['value_data']
                        }
            
            # Inhalt generieren
            content = self.reg_creator._generate_content(
                registry_data, 
                self.title_var.get(),
                self.description_text.get(1.0, tk.END).strip()
            )
            
            # Vorschau aktualisieren
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, content)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren der Vorschau: {e}")
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, f"Fehler bei der Vorschau: {e}")
    
    def _save(self):
        """Registry-Datei speichern"""
        try:
            # Validierung
            if not self.filename_var.get().strip():
                messagebox.showerror("Fehler", "Bitte geben Sie einen Dateinamen ein.")
                return
            
            if not self.registry_entries:
                messagebox.showerror("Fehler", "Bitte fügen Sie mindestens einen Registry-Eintrag hinzu.")
                return
            
            # Datei-Pfad zusammenstellen
            filename = self.filename_var.get().strip()
            if not filename.endswith('.reg'):
                filename += '.reg'
            
            filepath = Path(self.location_var.get()) / filename
            
            # Überschreiben bestätigen
            if filepath.exists():
                if not messagebox.askyesno("Bestätigung", f"Datei '{filename}' existiert bereits. Überschreiben?"):
                    return
            
            # Registry-Daten zusammenstellen
            registry_data = {'keys': {}, 'deleted_keys': []}
            
            for entry in self.registry_entries:
                if entry.get('action') == 'delete_key':
                    registry_data['deleted_keys'].append(entry['key_path'])
                else:
                    key_path = entry['key_path']
                    value_name = entry['value_name']
                    
                    if key_path not in registry_data['keys']:
                        registry_data['keys'][key_path] = {'values': {}}
                    
                    if value_name:  # Benannter Wert
                        registry_data['keys'][key_path]['values'][value_name] = {
                            'type': entry['value_type'],
                            'data': entry['value_data']
                        }
                    else:  # Default-Wert
                        registry_data['keys'][key_path]['default_value'] = {
                            'type': entry['value_type'],
                            'data': entry['value_data']
                        }
            
            # Datei erstellen
            success = self.reg_creator.create_file(
                str(filepath),
                registry_data,
                self.title_var.get(),
                self.description_text.get(1.0, tk.END).strip()
            )
            
            if success:
                self.result_file = str(filepath)
                messagebox.showinfo("Erfolg", f"Registry-Datei '{filename}' wurde erfolgreich erstellt.")
                self.window.destroy()
            else:
                messagebox.showerror("Fehler", "Fehler beim Erstellen der Registry-Datei.")
                
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Speichern: {e}")
    
    def _cancel(self):
        """Abbrechen"""
        self.window.destroy()


class RegEntryDialog:
    """Dialog zum Hinzufügen/Bearbeiten einzelner Registry-Einträge"""
    
    def __init__(self, parent, entry_data: Optional[Dict] = None):
        self.parent = parent
        self.entry_data = entry_data
        self.window = None
        self.result = None
        
        self._create_window()
        self._setup_ui()
        
        if entry_data:
            self._load_entry_data()
    
    def _create_window(self):
        """Dialog-Fenster erstellen"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Registry-Eintrag" + (" bearbeiten" if self.entry_data else " hinzufügen"))
        self.window.geometry("500x300")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Zentrieren
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.window.winfo_screenheight() // 2) - (300 // 2)
        self.window.geometry(f"500x300+{x}+{y}")
    
    def _setup_ui(self):
        """UI einrichten"""
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Registry-Key
        ttk.Label(main_frame, text="Registry-Key:").pack(anchor="w")
        self.key_var = tk.StringVar()
        key_frame = ttk.Frame(main_frame)
        key_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.key_combo = ttk.Combobox(key_frame, textvariable=self.key_var, values=[
            "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion",
            "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion",
            "HKEY_CURRENT_USER\\Control Panel\\Desktop",
            "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services"
        ])
        self.key_combo.pack(fill=tk.X)
        
        # Wert-Name
        ttk.Label(main_frame, text="Wert-Name (leer für Default-Wert):").pack(anchor="w")
        self.value_name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.value_name_var).pack(fill=tk.X, pady=(0, 10))
        
        # Wert-Typ
        ttk.Label(main_frame, text="Wert-Typ:").pack(anchor="w")
        self.value_type_var = tk.StringVar()
        self.value_type_combo = ttk.Combobox(main_frame, textvariable=self.value_type_var, values=[
            "REG_SZ", "REG_DWORD", "REG_QWORD", "REG_BINARY", "REG_MULTI_SZ", "REG_EXPAND_SZ"
        ], state="readonly")
        self.value_type_combo.pack(fill=tk.X, pady=(0, 10))
        self.value_type_combo.set("REG_SZ")
        self.value_type_combo.bind("<<ComboboxSelected>>", self._on_type_change)
        
        # Wert-Daten
        ttk.Label(main_frame, text="Wert-Daten:").pack(anchor="w")
        self.value_data_var = tk.StringVar()
        self.value_data_entry = ttk.Entry(main_frame, textvariable=self.value_data_var)
        self.value_data_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Abbrechen", command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="OK", command=self._ok).pack(side=tk.RIGHT)
    
    def _load_entry_data(self):
        """Eintragsdaten laden"""
        if self.entry_data:
            self.key_var.set(self.entry_data.get('key_path', ''))
            self.value_name_var.set(self.entry_data.get('value_name', ''))
            self.value_type_var.set(self.entry_data.get('value_type', 'REG_SZ'))
            self.value_data_var.set(str(self.entry_data.get('value_data', '')))
    
    def _on_type_change(self, event=None):
        """Handler für Typ-Änderung"""
        value_type = self.value_type_var.get()
        
        # Platzhalter-Text setzen
        if value_type == "REG_DWORD":
            self.value_data_entry.config(state="normal")
            if not self.value_data_var.get():
                self.value_data_var.set("0")
        elif value_type == "REG_QWORD":
            self.value_data_entry.config(state="normal")
            if not self.value_data_var.get():
                self.value_data_var.set("0")
        else:
            self.value_data_entry.config(state="normal")
    
    def _ok(self):
        """OK-Button gedrückt"""
        try:
            # Validierung
            key_path = self.key_var.get().strip()
            if not key_path:
                messagebox.showerror("Fehler", "Bitte geben Sie einen Registry-Key ein.")
                return
            
            value_type = self.value_type_var.get()
            value_data_str = self.value_data_var.get()
            
            # Daten je nach Typ konvertieren
            if value_type in ["REG_DWORD", "REG_QWORD"]:
                try:
                    if value_data_str.startswith("0x"):
                        value_data = int(value_data_str, 16)
                    else:
                        value_data = int(value_data_str)
                except ValueError:
                    messagebox.showerror("Fehler", f"Ungültiger Wert für {value_type}. Bitte geben Sie eine Zahl ein.")
                    return
            else:
                value_data = value_data_str
            
            self.result = {
                'key_path': key_path,
                'value_name': self.value_name_var.get().strip(),
                'value_type': value_type,
                'value_data': value_data
            }
            
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Verarbeiten der Eingabe: {e}")
    
    def _cancel(self):
        """Abbrechen"""
        self.window.destroy()


class DeleteKeyDialog:
    """Dialog zum Hinzufügen eines Key-Lösch-Eintrags"""
    
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.result = None
        
        self._create_window()
        self._setup_ui()
    
    def _create_window(self):
        """Dialog-Fenster erstellen"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Registry-Key löschen")
        self.window.geometry("400x150")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Zentrieren
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.window.winfo_screenheight() // 2) - (150 // 2)
        self.window.geometry(f"400x150+{x}+{y}")
    
    def _setup_ui(self):
        """UI einrichten"""
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(main_frame, text="Registry-Key zum Löschen:").pack(anchor="w")
        
        self.key_var = tk.StringVar()
        self.key_combo = ttk.Combobox(main_frame, textvariable=self.key_var, values=[
            "HKEY_CURRENT_USER\\Software\\TestKey",
            "HKEY_LOCAL_MACHINE\\SOFTWARE\\TestKey"
        ])
        self.key_combo.pack(fill=tk.X, pady=(5, 10))
        
        ttk.Label(main_frame, text="⚠️ Warnung: Das Löschen von Registry-Keys kann das System beschädigen!", 
                 foreground="red").pack(anchor="w", pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Abbrechen", command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="OK", command=self._ok).pack(side=tk.RIGHT)
    
    def _ok(self):
        """OK-Button gedrückt"""
        key_path = self.key_var.get().strip()
        if not key_path:
            messagebox.showerror("Fehler", "Bitte geben Sie einen Registry-Key ein.")
            return
        
        if messagebox.askyesno("Bestätigung", 
                              f"Registry-Key '{key_path}' wirklich zum Löschen vormerken?",
                              icon="warning"):
            self.result = key_path
            self.window.destroy()
    
    def _cancel(self):
        """Abbrechen"""
        self.window.destroy()