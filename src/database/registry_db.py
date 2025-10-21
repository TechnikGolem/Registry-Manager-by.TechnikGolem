"""
Registry Database
================

Modul für die Verwaltung der Registry-File-Dokumentation und -Metadaten.
Verwendet JSON-Dateien für die Persistierung.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime


class RegistryDatabase:
    """Datenbank für Registry-File-Metadaten"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        if db_path:
            self.db_path = Path(db_path)
        else:
            # Standard-Pfad: config/registry_db.json
            # Für EXE: Verwende das Verzeichnis der ausführbaren Datei
            import sys
            if getattr(sys, 'frozen', False):
                # Running as compiled EXE
                base_path = Path(sys.executable).parent
            else:
                # Running as script
                base_path = Path(__file__).parent.parent.parent
            
            self.db_path = base_path / "config" / "registry_db.json"
        
        self.db_data = {
            'version': '2.0',  # Updated für embedded REG content
            'created': None,
            'modified': None,
            'files': {},
            'embedded_regs': {},  # Neue Sektion für eingebettete REG-Inhalte
            'categories': [
                'System',
                'Design', 
                'Performance',
                'Sicherheit',
                'Entwicklung',
                'Registry-Tweaks',
                'UI-Anpassungen',
                'Netzwerk',
                'Software',
                'Gaming',
                'Privacy',
                'Sonstiges'
            ],
            'tags': []
        }
        
        self._load_database()
    
    def _load_database(self):
        """Datenbank aus Datei laden"""
        try:
            if self.db_path.exists():
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                
                # Datenbank-Schema aktualisieren falls nötig
                self.db_data.update(loaded_data)
                
                self.logger.info(f"Datenbank geladen: {self.db_path}")
            else:
                # Neue Datenbank erstellen
                self.db_data['created'] = datetime.now().isoformat()
                self._save_database()
                self.logger.info(f"Neue Datenbank erstellt: {self.db_path}")
                
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Datenbank: {e}")
            # Bei Fehler mit Standard-Daten weitermachen
    
    def _save_database(self):
        """Datenbank in Datei speichern"""
        try:
            # Verzeichnis erstellen falls nötig
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Timestamp aktualisieren
            self.db_data['modified'] = datetime.now().isoformat()
            
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.db_data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Datenbank gespeichert: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Datenbank: {e}")
            raise
    
    def save_documentation(self, filepath: str, doc_data: Dict):
        """
        Dokumentation für eine Registry-Datei speichern
        
        Args:
            filepath: Pfad zur Registry-Datei
            doc_data: Dokumentations-Daten
        """
        try:
            file_key = str(Path(filepath).resolve())
            
            # Basis-Informationen der Datei
            file_info = {
                'title': doc_data.get('title', ''),
                'category': doc_data.get('category', ''),
                'description': doc_data.get('description', ''),
                'tags': doc_data.get('tags', []),
                'created': datetime.now().isoformat(),
                'modified': datetime.now().isoformat(),
                'file_size': 0,
                'file_hash': None
            }
            
            # Datei-Statistiken hinzufügen
            if Path(filepath).exists():
                stat = Path(filepath).stat()
                file_info['file_size'] = stat.st_size
                file_info['file_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                
                # Hash berechnen für Änderungsvergleich
                import hashlib
                with open(filepath, 'rb') as f:
                    file_info['file_hash'] = hashlib.md5(f.read()).hexdigest()
            
            # Existierende Daten aktualisieren
            if file_key in self.db_data['files']:
                existing = self.db_data['files'][file_key]
                file_info['created'] = existing.get('created', file_info['created'])
            
            self.db_data['files'][file_key] = file_info
            
            # Tags zur globalen Tag-Liste hinzufügen
            for tag in doc_data.get('tags', []):
                if tag and tag not in self.db_data['tags']:
                    self.db_data['tags'].append(tag)
            
            self._save_database()
            self.logger.info(f"Dokumentation gespeichert für: {filepath}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Dokumentation: {e}")
            raise
    
    def get_documentation(self, filepath: str) -> Optional[Dict]:
        """
        Dokumentation für eine Registry-Datei abrufen
        
        Args:
            filepath: Pfad zur Registry-Datei
            
        Returns:
            Dokumentations-Daten oder None
        """
        try:
            file_key = str(Path(filepath).resolve())
            return self.db_data['files'].get(file_key)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Dokumentation: {e}")
            return None
    
    def get_all_files(self) -> Dict[str, Dict]:
        """
        Alle dokumentierten Dateien abrufen
        
        Returns:
            Dictionary mit allen Datei-Dokumentationen
        """
        return self.db_data['files']
    
    def search_files(self, query: str) -> List[Dict]:
        """
        Dateien nach Text durchsuchen
        
        Args:
            query: Suchbegriff
            
        Returns:
            Liste der gefundenen Dateien
        """
        results = []
        query_lower = query.lower()
        
        try:
            for filepath, file_data in self.db_data['files'].items():
                # In Titel, Beschreibung und Tags suchen
                searchable_text = ' '.join([
                    file_data.get('title', ''),
                    file_data.get('description', ''),
                    file_data.get('category', ''),
                    ' '.join(file_data.get('tags', []))
                ]).lower()
                
                if query_lower in searchable_text:
                    result = file_data.copy()
                    result['filepath'] = filepath
                    results.append(result)
            
            self.logger.info(f"Suche nach '{query}' ergab {len(results)} Ergebnisse")
            return results
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Suche: {e}")
            return []
    
    def has_file(self, filepath: str) -> bool:
        """
        Prüfen ob Datei in der Datenbank vorhanden ist
        
        Args:
            filepath: Pfad zur Datei
            
        Returns:
            True wenn Datei vorhanden, False sonst
        """
        file_key = str(Path(filepath).resolve())
        return file_key in self.db_data['files']
    
    def get_files_by_category(self, category: str) -> List[Dict]:
        """
        Dateien nach Kategorie filtern
        
        Args:
            category: Kategorie-Name
            
        Returns:
            Liste der Dateien in der Kategorie
        """
        results = []
        
        try:
            for filepath, file_data in self.db_data['files'].items():
                if file_data.get('category') == category:
                    result = file_data.copy()
                    result['filepath'] = filepath
                    results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Fehler beim Filtern nach Kategorie: {e}")
            return []
    
    def get_files_by_tag(self, tag: str) -> List[Dict]:
        """
        Dateien nach Tag filtern
        
        Args:
            tag: Tag-Name
            
        Returns:
            Liste der Dateien mit dem Tag
        """
        results = []
        
        try:
            for filepath, file_data in self.db_data['files'].items():
                if tag in file_data.get('tags', []):
                    result = file_data.copy()
                    result['filepath'] = filepath
                    results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Fehler beim Filtern nach Tag: {e}")
            return []
    
    def delete_documentation(self, filepath: str) -> bool:
        """
        Dokumentation für eine Datei löschen
        
        Args:
            filepath: Pfad zur Registry-Datei
            
        Returns:
            True bei Erfolg
        """
        try:
            file_key = str(Path(filepath).resolve())
            
            if file_key in self.db_data['files']:
                del self.db_data['files'][file_key]
                self._save_database()
                self.logger.info(f"Dokumentation gelöscht für: {filepath}")
                return True
            else:
                self.logger.warning(f"Keine Dokumentation gefunden für: {filepath}")
                return False
                
        except Exception as e:
            self.logger.error(f"Fehler beim Löschen der Dokumentation: {e}")
            return False
    
    def add_category(self, category: str) -> bool:
        """
        Neue Kategorie hinzufügen
        
        Args:
            category: Kategorie-Name
            
        Returns:
            True bei Erfolg
        """
        try:
            if category and category not in self.db_data['categories']:
                self.db_data['categories'].append(category)
                self._save_database()
                self.logger.info(f"Kategorie hinzugefügt: {category}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Fehler beim Hinzufügen der Kategorie: {e}")
            return False
    
    def get_categories(self) -> List[str]:
        """
        Alle verfügbaren Kategorien abrufen
        
        Returns:
            Liste der Kategorien
        """
        return self.db_data['categories']
    
    def get_tags(self) -> List[str]:
        """
        Alle verwendeten Tags abrufen
        
        Returns:
            Liste der Tags
        """
        return sorted(self.db_data['tags'])
    
    def get_statistics(self) -> Dict:
        """
        Datenbank-Statistiken abrufen
        
        Returns:
            Statistik-Dictionary
        """
        stats = {
            'total_files': len(self.db_data['files']),
            'categories': {},
            'tags': {},
            'total_size': 0,
            'last_modified': self.db_data.get('modified')
        }
        
        try:
            for file_data in self.db_data['files'].values():
                # Kategorien zählen
                category = file_data.get('category', 'Ohne Kategorie')
                stats['categories'][category] = stats['categories'].get(category, 0) + 1
                
                # Tags zählen
                for tag in file_data.get('tags', []):
                    stats['tags'][tag] = stats['tags'].get(tag, 0) + 1
                
                # Gesamtgröße
                stats['total_size'] += file_data.get('file_size', 0)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen der Statistiken: {e}")
            return stats
    
    def export_documentation(self, export_path: str) -> bool:
        """
        Komplette Dokumentation exportieren
        
        Args:
            export_path: Pfad für Export-Datei
            
        Returns:
            True bei Erfolg
        """
        try:
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'database': self.db_data
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Dokumentation exportiert: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Exportieren: {e}")
            return False
    
    def import_documentation(self, import_path: str, merge: bool = True) -> bool:
        """
        Dokumentation importieren
        
        Args:
            import_path: Pfad zur Import-Datei
            merge: True = mit bestehenden Daten zusammenführen, False = ersetzen
            
        Returns:
            True bei Erfolg
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            imported_db = import_data.get('database', import_data)
            
            if merge:
                # Zusammenführen
                for file_key, file_data in imported_db.get('files', {}).items():
                    self.db_data['files'][file_key] = file_data
                
                # Kategorien und Tags zusammenführen
                for category in imported_db.get('categories', []):
                    if category not in self.db_data['categories']:
                        self.db_data['categories'].append(category)
                
                for tag in imported_db.get('tags', []):
                    if tag not in self.db_data['tags']:
                        self.db_data['tags'].append(tag)
            else:
                # Ersetzen
                self.db_data['files'] = imported_db.get('files', {})
                self.db_data['categories'] = imported_db.get('categories', [])
                self.db_data['tags'] = imported_db.get('tags', [])
            
            self._save_database()
            self.logger.info(f"Dokumentation importiert: {import_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Importieren: {e}")
            return False
    
    def cleanup_missing_files(self) -> int:
        """
        Dokumentation für nicht mehr existierende Dateien entfernen
        
        Returns:
            Anzahl der entfernten Einträge
        """
        removed_count = 0
        
        try:
            files_to_remove = []
            
            for file_key in self.db_data['files'].keys():
                if not Path(file_key).exists():
                    files_to_remove.append(file_key)
            
            for file_key in files_to_remove:
                del self.db_data['files'][file_key]
                removed_count += 1
            
            if removed_count > 0:
                self._save_database()
                self.logger.info(f"Dokumentation für {removed_count} fehlende Dateien entfernt")
            
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Fehler beim Bereinigen: {e}")
            return 0
    
    def embed_reg_file(self, reg_id: str, reg_content: str, metadata: Dict[str, Any]) -> bool:
        """REG-Datei-Inhalt in die Datenbank einbetten
        
        Args:
            reg_id: Eindeutige ID für die REG-Datei
            reg_content: Vollständiger REG-Datei-Inhalt als String
            metadata: Metadaten wie Name, Beschreibung, Kategorie etc.
            
        Returns:
            bool: Erfolg der Operation
        """
        try:
            self.db_data['embedded_regs'][reg_id] = {
                'content': reg_content,
                'metadata': metadata,
                'embedded_date': datetime.now().isoformat(),
                'last_used': None,
                'use_count': 0
            }
            
            self._save_database()
            self.logger.info(f"REG-Datei eingebettet: {reg_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Einbetten der REG-Datei {reg_id}: {e}")
            return False
    
    def get_embedded_reg(self, reg_id: str) -> Optional[Dict[str, Any]]:
        """Eingebettete REG-Datei abrufen
        
        Args:
            reg_id: ID der REG-Datei
            
        Returns:
            Dict mit REG-Inhalt und Metadaten oder None
        """
        return self.db_data.get('embedded_regs', {}).get(reg_id)
    
    def list_embedded_regs(self) -> Dict[str, Dict[str, Any]]:
        """Alle eingebetteten REG-Dateien auflisten
        
        Returns:
            Dict mit allen eingebetteten REG-Dateien
        """
        return self.db_data.get('embedded_regs', {})
    
    def delete_embedded_reg(self, reg_id: str) -> bool:
        """Eingebettete REG-Datei löschen
        
        Args:
            reg_id: ID der zu löschenden REG-Datei
            
        Returns:
            bool: Erfolg der Operation
        """
        try:
            if reg_id in self.db_data.get('embedded_regs', {}):
                del self.db_data['embedded_regs'][reg_id]
                self._save_database()
                self.logger.info(f"Eingebettete REG-Datei gelöscht: {reg_id}")
                return True
            else:
                self.logger.warning(f"REG-Datei nicht gefunden: {reg_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Fehler beim Löschen der REG-Datei {reg_id}: {e}")
            return False
    
    def update_embedded_reg_usage(self, reg_id: str):
        """Nutzungsstatistiken für eingebettete REG-Datei aktualisieren
        
        Args:
            reg_id: ID der REG-Datei
        """
        try:
            if reg_id in self.db_data.get('embedded_regs', {}):
                reg_data = self.db_data['embedded_regs'][reg_id]
                reg_data['last_used'] = datetime.now().isoformat()
                reg_data['use_count'] = reg_data.get('use_count', 0) + 1
                self._save_database()
                
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren der Nutzungsstatistiken für {reg_id}: {e}")

    def close(self):
        """Datenbank schließen und letzte Änderungen speichern"""
        try:
            self._save_database()
            self.logger.info("Datenbank geschlossen")
        except Exception as e:
            self.logger.error(f"Fehler beim Schließen der Datenbank: {e}")