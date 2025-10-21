"""
Status Display
=============

Widget zur Anzeige des Registry-Status.
"""

import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox
import logging
from typing import Dict, Optional


class StatusDisplay:
    """Widget zur Anzeige von Registry-Status-Informationen"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.logger = logging.getLogger(__name__)
        
        self.status_data = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Benutzeroberfläche einrichten"""
        # Hauptcontainer
        main_frame = ttk.Frame(self.parent_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Zusammenfassung oben
        self.summary_frame = ttk.LabelFrame(main_frame, text="Zusammenfassung")
        self.summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Grid für Zusammenfassung
        summary_grid = ttk.Frame(self.summary_frame)
        summary_grid.pack(fill=tk.X, padx=10, pady=10)
        
        # Labels für Statistiken
        self.stats_labels = {}
        
        row = 0
        stats_info = [
            ("total_keys", "Gesamt Keys:"),
            ("active_keys", "Aktive Keys:"),
            ("missing_keys", "Fehlende Keys:"),
            ("total_values", "Gesamt Werte:"),
            ("matching_values", "Übereinstimmende Werte:"),
            ("different_values", "Unterschiedliche Werte:"),
            ("missing_values", "Fehlende Werte:")
        ]
        
        for key, label_text in stats_info:
            ttk.Label(summary_grid, text=label_text).grid(row=row, column=0, sticky="w", padx=(0, 10))
            self.stats_labels[key] = ttk.Label(summary_grid, text="0", font=("Arial", 10, "bold"))
            self.stats_labels[key].grid(row=row, column=1, sticky="w")
            row += 1
        
        # Timestamp
        ttk.Label(summary_grid, text="Letzte Prüfung:").grid(row=row, column=0, sticky="w", padx=(0, 10))
        self.timestamp_label = ttk.Label(summary_grid, text="Noch nicht geprüft")
        self.timestamp_label.grid(row=row, column=1, sticky="w")
        
        # Detaillierte Anzeige
        details_frame = ttk.LabelFrame(main_frame, text="Details")
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview für Details
        self.details_tree = ttk.Treeview(details_frame, columns=("status", "expected", "actual"), show="tree headings")
        self.details_tree.heading("#0", text="Registry-Pfad")
        self.details_tree.heading("status", text="Status")
        self.details_tree.heading("expected", text="Erwartet")
        self.details_tree.heading("actual", text="Aktuell")
        
        self.details_tree.column("#0", width=300)
        self.details_tree.column("status", width=100)
        self.details_tree.column("expected", width=150)
        self.details_tree.column("actual", width=150)
        
        # Scrollbars für Treeview
        tree_scrollbar_v = ttk.Scrollbar(details_frame, orient="vertical", command=self.details_tree.yview)
        tree_scrollbar_h = ttk.Scrollbar(details_frame, orient="horizontal", command=self.details_tree.xview)
        self.details_tree.configure(yscrollcommand=tree_scrollbar_v.set, xscrollcommand=tree_scrollbar_h.set)
        
        self.details_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        tree_scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        tree_scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X, padx=5)
        
        # Status-Farben definieren
        self.details_tree.tag_configure("match", foreground="green")
        self.details_tree.tag_configure("different", foreground="orange")
        self.details_tree.tag_configure("missing", foreground="red")
        self.details_tree.tag_configure("should_not_exist", foreground="purple")
        self.details_tree.tag_configure("correctly_deleted", foreground="blue")
        
        # Kontextmenü
        self.context_menu = tk.Menu(self.details_tree, tearoff=0)
        self.context_menu.add_command(label="Details anzeigen", command=self._show_value_details)
        self.context_menu.add_command(label="In Registry öffnen", command=self._open_in_registry)
        
        self.details_tree.bind("<Button-3>", self._show_context_menu)
        self.details_tree.bind("<Double-1>", self._on_double_click)
    
    def _on_double_click(self, event):
        """Event-Handler für Doppelklick"""
        self._show_value_details()
    
    def update_status(self, status_data: Dict):
        """
        Status-Anzeige aktualisieren
        
        Args:
            status_data: Status-Daten vom StatusChecker
        """
        try:
            self.status_data = status_data
            
            # Zusammenfassung aktualisieren
            summary = status_data.get('summary', {})
            for key, label in self.stats_labels.items():
                value = summary.get(key, 0)
                label.config(text=str(value))
                
                # Farbe je nach Status
                if key in ['missing_keys', 'different_values', 'missing_values'] and value > 0:
                    label.config(foreground="red")
                elif key in ['active_keys', 'matching_values'] and value > 0:
                    label.config(foreground="green")
                else:
                    label.config(foreground="black")
            
            # Timestamp aktualisieren
            timestamp = status_data.get('timestamp')
            if timestamp:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp)
                    formatted_time = dt.strftime("%d.%m.%Y %H:%M:%S")
                    self.timestamp_label.config(text=formatted_time)
                except:
                    self.timestamp_label.config(text=timestamp)
            
            # Details aktualisieren
            self._update_details_tree()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren der Status-Anzeige: {e}")
    
    def _update_details_tree(self):
        """Details-Treeview aktualisieren"""
        # Alle Einträge löschen
        self.details_tree.delete(*self.details_tree.get_children())
        
        if not self.status_data:
            return
        
        try:
            keys_data = self.status_data.get('keys', {})
            
            for key_path, key_status in keys_data.items():
                # Key-Eintrag hinzufügen
                key_exists = key_status.get('exists', False)
                expected_deleted = key_status.get('expected_deleted', False)
                
                if expected_deleted:
                    key_status_text = "Sollte gelöscht sein" if key_exists else "Korrekt gelöscht"
                    key_tag = "should_not_exist" if key_exists else "correctly_deleted"
                else:
                    key_status_text = "Existiert" if key_exists else "Fehlt"
                    key_tag = "match" if key_exists else "missing"
                
                key_item = self.details_tree.insert("", "end", 
                                                   text=key_path, 
                                                   values=(key_status_text, "", ""),
                                                   tags=(key_tag,))
                
                # Wert-Einträge hinzufügen
                for value_name, value_status in key_status.get('values', {}).items():
                    status_text = self._get_status_text(value_status['status'])
                    expected_text = self._format_value_display(value_status.get('expected'))
                    actual_text = self._format_value_display(value_status.get('actual'))
                    
                    value_display_name = value_name if value_name != '@default' else '(Standard)'
                    
                    self.details_tree.insert(key_item, "end",
                                           text=f"  └─ {value_display_name}",
                                           values=(status_text, expected_text, actual_text),
                                           tags=(value_status['status'],))
                
                # Key aufklappen falls Werte vorhanden
                if key_status.get('values'):
                    self.details_tree.item(key_item, open=True)
                    
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren der Details: {e}")
    
    def _get_status_text(self, status: str) -> str:
        """Status-Text für Anzeige formatieren"""
        status_texts = {
            'match': '✓ Übereinstimmung',
            'different': '⚠ Unterschiedlich',
            'missing': '✗ Fehlt',
            'should_not_exist': '⚠ Sollte nicht existieren',
            'correctly_deleted': '✓ Korrekt gelöscht'
        }
        return status_texts.get(status, status)
    
    def _format_value_display(self, value_data: Optional[Dict]) -> str:
        """Wert für Anzeige formatieren"""
        if not value_data:
            return "N/A"
        
        try:
            value_type = value_data.get('type', '')
            data = value_data.get('data', '')
            
            if value_type == 'REG_DWORD':
                return f"{data} (0x{data:08x})" if isinstance(data, int) else str(data)
            elif value_type == 'REG_QWORD':
                return f"{data} (0x{data:016x})" if isinstance(data, int) else str(data)
            elif value_type == 'REG_BINARY':
                if isinstance(data, (list, bytes)):
                    hex_str = ' '.join([f"{b:02x}" for b in data[:8]])
                    if len(data) > 8:
                        hex_str += "..."
                    return f"[{hex_str}]"
                return str(data)
            elif value_type == 'REG_MULTI_SZ':
                if isinstance(data, list):
                    return "; ".join(data[:3]) + ("..." if len(data) > 3 else "")
                return str(data)
            else:
                # String-Werte (REG_SZ, REG_EXPAND_SZ)
                text = str(data)
                return text[:50] + "..." if len(text) > 50 else text
                
        except Exception:
            return str(value_data)
    
    def _show_context_menu(self, event):
        """Kontextmenü anzeigen"""
        item = self.details_tree.identify_row(event.y)
        if item:
            self.details_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _show_value_details(self):
        """Detaillierte Wert-Informationen anzeigen"""
        selection = self.details_tree.selection()
        if not selection:
            return
        
        item = self.details_tree.item(selection[0])
        text = item['text']
        values = item['values']
        
        # Details-Fenster erstellen
        details_window = tk.Toplevel(self.parent_frame)
        details_window.title("Wert-Details")
        details_window.geometry("500x400")
        details_window.transient(self.parent_frame.winfo_toplevel())
        
        # Text-Widget für Details
        details_text = tk.Text(details_window, wrap=tk.WORD, font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(details_window, orient="vertical", command=details_text.yview)
        details_text.configure(yscrollcommand=scrollbar.set)
        
        # Details zusammenstellen
        details_content = f"Registry-Element: {text}\\n"
        details_content += f"Status: {values[0]}\\n"
        details_content += f"Erwartet: {values[1]}\\n"
        details_content += f"Aktuell: {values[2]}\\n\\n"
        
        # Zusätzliche Informationen aus den Status-Daten
        if self.status_data:
            # Hier könnte man detailliertere Informationen hinzufügen
            pass
        
        details_text.insert(1.0, details_content)
        details_text.config(state=tk.DISABLED)
        
        details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
    
    def _open_in_registry(self):
        """Registry-Editor öffnen"""
        selection = self.details_tree.selection()
        if not selection:
            return
        
        item = self.details_tree.item(selection[0])
        text = item['text'].strip()
        
        # Key-Pfad extrahieren
        if text.startswith('└─'):
            # Das ist ein Wert, parent-Key verwenden
            parent_item = self.details_tree.parent(selection[0])
            if parent_item:
                parent_text = self.details_tree.item(parent_item)['text']
                registry_path = parent_text
            else:
                return
        else:
            # Das ist ein Key
            registry_path = text
        
        try:
            # Registry-Editor mit Key öffnen
            import subprocess
            subprocess.run(['regedit', '/m', registry_path], check=False)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Öffnen des Registry-Editors: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Öffnen des Registry-Editors: {e}")
    
    def clear_status(self):
        """Status-Anzeige zurücksetzen"""
        self.status_data = None
        
        # Statistiken zurücksetzen
        for label in self.stats_labels.values():
            label.config(text="0", foreground="black")
        
        self.timestamp_label.config(text="Noch nicht geprüft")
        
        # Details löschen
        self.details_tree.delete(*self.details_tree.get_children())
    
    def export_status_report(self) -> Optional[str]:
        """
        Status-Report als Text exportieren
        
        Returns:
            Formatierter Report-Text oder None
        """
        if not self.status_data:
            return None
        
        try:
            lines = []
            lines.append("Registry-Status Report")
            lines.append("=" * 50)
            lines.append("")
            
            # Zusammenfassung
            summary = self.status_data.get('summary', {})
            lines.append("Zusammenfassung:")
            lines.append(f"  Gesamt Keys: {summary.get('total_keys', 0)}")
            lines.append(f"  Aktive Keys: {summary.get('active_keys', 0)}")
            lines.append(f"  Fehlende Keys: {summary.get('missing_keys', 0)}")
            lines.append(f"  Gesamt Werte: {summary.get('total_values', 0)}")
            lines.append(f"  Übereinstimmende Werte: {summary.get('matching_values', 0)}")
            lines.append(f"  Unterschiedliche Werte: {summary.get('different_values', 0)}")
            lines.append(f"  Fehlende Werte: {summary.get('missing_values', 0)}")
            lines.append("")
            
            # Timestamp
            timestamp = self.status_data.get('timestamp')
            if timestamp:
                lines.append(f"Letzte Prüfung: {timestamp}")
                lines.append("")
            
            # Details
            lines.append("Details:")
            lines.append("-" * 30)
            
            keys_data = self.status_data.get('keys', {})
            for key_path, key_status in keys_data.items():
                key_exists = key_status.get('exists', False)
                lines.append(f"\\n[{key_path}]")
                lines.append(f"  Status: {'Existiert' if key_exists else 'Fehlt'}")
                
                for value_name, value_status in key_status.get('values', {}).items():
                    status_text = self._get_status_text(value_status['status'])
                    expected = self._format_value_display(value_status.get('expected'))
                    actual = self._format_value_display(value_status.get('actual'))
                    
                    value_display_name = value_name if value_name != '@default' else '(Standard)'
                    lines.append(f"  {value_display_name}:")
                    lines.append(f"    Status: {status_text}")
                    lines.append(f"    Erwartet: {expected}")
                    lines.append(f"    Aktuell: {actual}")
            
            return "\\n".join(lines)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen des Reports: {e}")
            return None