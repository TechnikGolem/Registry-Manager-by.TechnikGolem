"""
SQLite Database für Embedded Registry Files
============================================

Speichert alle eingebetteten REG-Files in einer SQLite-Datenbank,
die zusammen mit der EXE als portable Anwendung läuft.
"""

import sqlite3
import logging
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import sys


class SQLiteRegistryDB:
    """SQLite-Datenbank für eingebettete Registry-Files"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Datenbank-Pfad: Immer neben der EXE/dem Skript
        if getattr(sys, 'frozen', False):
            # Running as compiled EXE
            base_path = Path(sys.executable).parent
        else:
            # Running as script
            base_path = Path(__file__).parent.parent.parent
        
        self.db_path = base_path / "registry_manager.db"
        self.logger.info(f"Datenbank-Pfad: {self.db_path}")
        
        self._init_database()
    
    def _init_database(self):
        """Datenbank-Schema erstellen"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Tabelle für eingebettete REG-Files
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS embedded_regs (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    status TEXT DEFAULT 'Inaktiv',
                    created_date TEXT,
                    embedded_date TEXT,
                    last_applied TEXT,
                    usage_count INTEGER DEFAULT 0,
                    tags TEXT,
                    metadata TEXT
                )
            ''')
            
            # Tabelle für Kategorien
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            ''')
            
            # Tabelle für Gruppen (neue Funktion!)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS groups (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    color TEXT,
                    icon TEXT,
                    created_date TEXT,
                    sort_order INTEGER DEFAULT 0
                )
            ''')
            
            # Tabelle für Gruppen-Zuordnungen (n:m Beziehung)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reg_groups (
                    reg_id TEXT NOT NULL,
                    group_id TEXT NOT NULL,
                    added_date TEXT,
                    PRIMARY KEY (reg_id, group_id),
                    FOREIGN KEY (reg_id) REFERENCES embedded_regs(id) ON DELETE CASCADE,
                    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
                )
            ''')
            
            # Standard-Kategorien einfügen
            default_categories = [
                'System', 'Design', 'Performance', 'Sicherheit',
                'Entwicklung', 'Registry-Tweaks', 'UI-Anpassungen',
                'Netzwerk', 'Software', 'Gaming', 'Privacy', 'Sonstiges'
            ]
            
            for cat in default_categories:
                cursor.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', (cat,))
            
            conn.commit()
            conn.close()
            
            self.logger.info("Datenbank initialisiert")
            
        except Exception as e:
            self.logger.error(f"Fehler bei Datenbank-Initialisierung: {e}")
    
    def embed_reg_file(self, reg_id: str, content: str, metadata: Dict) -> bool:
        """REG-File in Datenbank einbetten"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO embedded_regs 
                (id, name, content, description, category, status, 
                 created_date, embedded_date, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                reg_id,
                metadata.get('name', reg_id),
                content,
                metadata.get('description', ''),
                metadata.get('category', 'Sonstiges'),
                metadata.get('status', 'Inaktiv'),
                metadata.get('created_date', datetime.now().isoformat()),
                datetime.now().isoformat(),
                json.dumps(metadata.get('tags', [])),
                json.dumps(metadata)
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"REG-File eingebettet: {reg_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Einbetten: {e}")
            return False
    
    def get_embedded_reg(self, reg_id: str) -> Optional[Dict]:
        """Eingebettete REG-Datei laden"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM embedded_regs WHERE id = ?', (reg_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            metadata = json.loads(row[11]) if row[11] else {}
            metadata.update({
                'name': row[1],
                'description': row[3],
                'category': row[4],
                'status': row[5],
                'created_date': row[6],
                'embedded_date': row[7],
                'last_applied': row[8],
                'usage_count': row[9],
                'tags': json.loads(row[10]) if row[10] else []
            })
            
            return {
                'content': row[2],
                'metadata': metadata
            }
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden: {e}")
            return None
    
    def list_embedded_regs(self) -> Dict[str, Dict]:
        """Alle eingebetteten REG-Files auflisten - als Dict für Kompatibilität"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, name, category, status, description, content, metadata FROM embedded_regs')
            rows = cursor.fetchall()
            conn.close()
            
            result = {}
            for row in rows:
                reg_id = row[0]
                metadata = json.loads(row[6]) if row[6] else {}
                metadata.update({
                    'name': row[1],
                    'category': row[2],
                    'status': row[3],
                    'description': row[4]
                })
                
                result[reg_id] = {
                    'content': row[5],
                    'metadata': metadata
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Fehler beim Auflisten: {e}")
            return {}
    
    def delete_embedded_reg(self, reg_id: str) -> bool:
        """Eingebettete REG-Datei löschen"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM embedded_regs WHERE id = ?', (reg_id,))
            conn.commit()
            conn.close()
            
            self.logger.info(f"REG-File gelöscht: {reg_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Löschen: {e}")
            return False
    
    def update_status(self, reg_id: str, status: str) -> bool:
        """Status aktualisieren"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE embedded_regs 
                SET status = ?, last_applied = ?
                WHERE id = ?
            ''', (status, datetime.now().isoformat(), reg_id))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Status-Update: {e}")
            return False
    
    def update_usage_count(self, reg_id: str) -> bool:
        """Verwendungszähler erhöhen"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE embedded_regs 
                SET usage_count = usage_count + 1
                WHERE id = ?
            ''', (reg_id,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Usage-Update: {e}")
            return False
    
    def update_metadata(self, reg_id: str, metadata: Dict) -> bool:
        """Metadaten eines REG-Eintrags aktualisieren"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE embedded_regs 
                SET name = ?, description = ?, category = ?, 
                    status = ?, metadata = ?
                WHERE id = ?
            ''', (
                metadata.get('name'),
                metadata.get('description'),
                metadata.get('category'),
                metadata.get('status'),
                json.dumps(metadata),
                reg_id
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Metadata-Update: {e}")
            return False
    
    def get_categories(self) -> List[str]:
        """Alle Kategorien abrufen"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('SELECT name FROM categories ORDER BY name')
            rows = cursor.fetchall()
            conn.close()
            
            return [row[0] for row in rows]
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Kategorien: {e}")
            return ['Sonstiges']
    
    # === GRUPPEN-FUNKTIONEN ===
    
    def create_group(self, name: str, description: str = "", color: str = "", icon: str = "📁") -> Optional[str]:
        """Neue Gruppe erstellen"""
        try:
            group_id = f"group_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO groups (id, name, description, color, icon, created_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (group_id, name, description, color, icon, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Gruppe erstellt: {name} ({group_id})")
            return group_id
            
        except sqlite3.IntegrityError:
            self.logger.warning(f"Gruppe existiert bereits: {name}")
            return None
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen der Gruppe: {e}")
            return None
    
    def list_groups(self) -> List[Dict]:
        """Alle Gruppen auflisten"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, name, description, color, icon, sort_order FROM groups ORDER BY sort_order, name')
            rows = cursor.fetchall()
            conn.close()
            
            groups = []
            for row in rows:
                groups.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2] or '',
                    'color': row[3] or '',
                    'icon': row[4] or '📁',
                    'sort_order': row[5]
                })
            
            return groups
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Gruppen: {e}")
            return []
    
    def delete_group(self, group_id: str) -> bool:
        """Gruppe löschen (inkl. aller Zuordnungen)"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Zuordnungen werden automatisch durch CASCADE gelöscht
            cursor.execute('DELETE FROM groups WHERE id = ?', (group_id,))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Gruppe gelöscht: {group_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Löschen der Gruppe: {e}")
            return False
    
    def add_reg_to_group(self, reg_id: str, group_id: str) -> bool:
        """REG zu Gruppe hinzufügen"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO reg_groups (reg_id, group_id, added_date)
                VALUES (?, ?, ?)
            ''', (reg_id, group_id, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"REG {reg_id} zu Gruppe {group_id} hinzugefügt")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Hinzufügen zur Gruppe: {e}")
            return False
    
    def remove_reg_from_group(self, reg_id: str, group_id: str) -> bool:
        """REG aus Gruppe entfernen"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM reg_groups WHERE reg_id = ? AND group_id = ?', (reg_id, group_id))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"REG {reg_id} aus Gruppe {group_id} entfernt")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Entfernen aus Gruppe: {e}")
            return False
    
    def get_reg_groups(self, reg_id: str) -> List[str]:
        """Alle Gruppen einer REG abrufen"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('SELECT group_id FROM reg_groups WHERE reg_id = ?', (reg_id,))
            rows = cursor.fetchall()
            conn.close()
            
            return [row[0] for row in rows]
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Gruppen: {e}")
            return []
    
    def get_group_regs(self, group_id: str) -> List[str]:
        """Alle REGs einer Gruppe abrufen"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('SELECT reg_id FROM reg_groups WHERE group_id = ?', (group_id,))
            rows = cursor.fetchall()
            conn.close()
            
            return [row[0] for row in rows]
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der REGs: {e}")
            return []
    
    # === KOMPATIBILITÄTS-METHODEN ===
    
    # Kompatibilitäts-Methoden für alte Datei-basierte Funktionen
    def has_file(self, file_path: str) -> bool:
        """Prüft ob Datei dokumentiert ist (Kompatibilität)"""
        return False  # Wir nutzen nur noch embedded REGs
    
    def get_documentation(self, file_path: str) -> Optional[Dict]:
        """Dokumentation für Datei abrufen (Kompatibilität)"""
        return None  # Wir nutzen nur noch embedded REGs
    
    def save_documentation(self, file_path: str, doc_data: Dict) -> bool:
        """Dokumentation speichern (Kompatibilität)"""
        return True  # Wir nutzen nur noch embedded REGs
    
    def delete_documentation(self, file_path: str) -> bool:
        """Dokumentation löschen (Kompatibilität)"""
        return True  # Wir nutzen nur noch embedded REGs
    
    def export_documentation(self, export_path: str) -> bool:
        """Dokumentation exportieren (Kompatibilität)"""
        return True  # Nicht mehr benötigt
    
    def close(self):
        """Datenbank schließen (Kompatibilität)"""
        pass  # SQLite braucht kein explizites Schließen
