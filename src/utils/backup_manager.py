"""
Registry Backup Manager
======================

Verwaltet automatische Backups der Registry vor Änderungen.
"""

import os
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging


class RegistryBackupManager:
    """Manager für Registry-Backups"""
    
    def __init__(self, backup_dir: str = "backups"):
        self.logger = logging.getLogger(__name__)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Backup-Metadaten
        self.metadata_file = self.backup_dir / "backup_metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Backup-Metadaten laden"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Fehler beim Laden der Backup-Metadaten: {e}")
        
        return {"backups": []}
    
    def _save_metadata(self):
        """Backup-Metadaten speichern"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Backup-Metadaten: {e}")
    
    def create_backup(self, reg_file_path: str, description: str = "") -> Optional[str]:
        """
        Backup vor Registry-Änderung erstellen
        
        Args:
            reg_file_path: Pfad zur .reg-Datei die angewendet wird
            description: Beschreibung des Backups
            
        Returns:
            Backup-ID oder None bei Fehler
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_id = f"backup_{timestamp}"
            backup_path = self.backup_dir / backup_id
            backup_path.mkdir(exist_ok=True)
            
            # Registry-Keys aus .reg-Datei extrahieren
            reg_keys = self._extract_registry_keys(reg_file_path)
            
            # Aktuelle Registry-Werte exportieren
            export_file = backup_path / "current_state.reg"
            self._export_registry_keys(reg_keys, export_file)
            
            # Original .reg-Datei kopieren
            original_file = backup_path / "applied_changes.reg"
            shutil.copy2(reg_file_path, original_file)
            
            # Backup-Info speichern
            backup_info = {
                "id": backup_id,
                "timestamp": timestamp,
                "datetime": datetime.now().isoformat(),
                "reg_file": os.path.basename(reg_file_path),
                "description": description,
                "registry_keys": reg_keys,
                "files": {
                    "current_state": str(export_file),
                    "applied_changes": str(original_file)
                }
            }
            
            self.metadata["backups"].append(backup_info)
            self._save_metadata()
            
            self.logger.info(f"Backup erstellt: {backup_id}")
            return backup_id
            
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen des Backups: {e}")
            return None
    
    def _extract_registry_keys(self, reg_file_path: str) -> List[str]:
        """Registry-Keys aus .reg-Datei extraktieren"""
        keys = []
        try:
            # Multi-Encoding-Support für Registry-Dateien
            encodings = ['utf-8-sig', 'utf-16', 'cp1252', 'latin1']
            content = None
            
            for encoding in encodings:
                try:
                    with open(reg_file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise Exception("Konnte Datei mit keinem Encoding lesen")
            
            # Keys aus Content extrahieren
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('[') and line.endswith(']'):
                    key = line[1:-1]  # Klammern entfernen
                    if key not in keys:
                        keys.append(key)
                        
        except Exception as e:
            self.logger.error(f"Fehler beim Extrahieren der Registry-Keys: {e}")
        
        return keys
    
    def _export_registry_keys(self, keys: List[str], output_file: Path):
        """Registry-Keys in .reg-Datei exportieren"""
        try:
            # Temporäre .reg-Datei mit allen Keys erstellen
            temp_reg = output_file.with_suffix('.temp.reg')
            
            with open(temp_reg, 'w', encoding='utf-8') as f:
                f.write("Windows Registry Editor Version 5.00\n\n")
                
                for key in keys:
                    # Jeden Key einzeln exportieren
                    try:
                        result = subprocess.run(
                            ['reg', 'export', key, str(temp_reg.with_suffix(f'.{key.replace("\\", "_")}.reg')), '/y'],
                            capture_output=True,
                            text=True,
                            encoding='utf-8',
                            errors='ignore',
                            check=False
                        )
                        
                        # Exportierte Datei an Haupt-Backup anhängen
                        key_file = temp_reg.with_suffix(f'.{key.replace("\\", "_")}.reg')
                        if key_file.exists():
                            try:
                                # Verschiedene Encodings versuchen
                                encodings = ['utf-16le', 'utf-8-sig', 'utf-8', 'cp1252', 'latin1']
                                content = None
                                
                                for encoding in encodings:
                                    try:
                                        with open(key_file, 'r', encoding=encoding) as kf:
                                            content = kf.read()
                                        break
                                    except UnicodeDecodeError:
                                        continue
                                
                                if content:
                                    f.write(f"; Backup für {key}\n")
                                    f.write(content)
                                    f.write("\n")
                                else:
                                    f.write(f"; FEHLER: Konnte {key} nicht lesen (Encoding-Problem)\n\n")
                                    
                            except Exception as read_error:
                                f.write(f"; FEHLER: Konnte {key} nicht lesen: {read_error}\n\n")
                            
                            try:
                                key_file.unlink()  # Temporäre Datei löschen
                            except:
                                pass
                            
                    except Exception as e:
                        self.logger.warning(f"Konnte Key {key} nicht exportieren: {e}")
                        f.write(f"; FEHLER: Konnte {key} nicht exportieren\n\n")
            
            # Finale Datei umbenennen
            temp_reg.rename(output_file)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Exportieren der Registry-Keys: {e}")
    
    def restore_backup(self, backup_id: str) -> bool:
        """
        Backup wiederherstellen
        
        Args:
            backup_id: ID des Backups
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            backup_info = self.get_backup_info(backup_id)
            if not backup_info:
                return False
            
            restore_file = backup_info["files"]["current_state"]
            
            if not os.path.exists(restore_file):
                self.logger.error(f"Backup-Datei nicht gefunden: {restore_file}")
                return False
            
            # Registry-Backup anwenden
            result = subprocess.run(['regedit', '/s', restore_file], check=True)
            
            self.logger.info(f"Backup wiederhergestellt: {backup_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Wiederherstellen des Backups: {e}")
            return False
    
    def get_backup_info(self, backup_id: str) -> Optional[Dict]:
        """Backup-Informationen abrufen"""
        for backup in self.metadata["backups"]:
            if backup["id"] == backup_id:
                return backup
        return None
    
    def list_backups(self) -> List[Dict]:
        """Alle verfügbaren Backups auflisten"""
        return sorted(
            self.metadata["backups"], 
            key=lambda x: x["datetime"], 
            reverse=True
        )
    
    def delete_backup(self, backup_id: str) -> bool:
        """
        Backup löschen
        
        Args:
            backup_id: ID des zu löschenden Backups
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            backup_info = self.get_backup_info(backup_id)
            if not backup_info:
                return False
            
            # Backup-Verzeichnis löschen
            backup_path = self.backup_dir / backup_id
            if backup_path.exists():
                shutil.rmtree(backup_path)
            
            # Aus Metadaten entfernen
            self.metadata["backups"] = [
                b for b in self.metadata["backups"] 
                if b["id"] != backup_id
            ]
            self._save_metadata()
            
            self.logger.info(f"Backup gelöscht: {backup_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Löschen des Backups: {e}")
            return False
    
    def cleanup_old_backups(self, max_backups: int = 50):
        """Alte Backups aufräumen"""
        try:
            backups = self.list_backups()
            
            if len(backups) > max_backups:
                old_backups = backups[max_backups:]
                
                for backup in old_backups:
                    self.delete_backup(backup["id"])
                
                self.logger.info(f"{len(old_backups)} alte Backups gelöscht")
                
        except Exception as e:
            self.logger.error(f"Fehler beim Aufräumen alter Backups: {e}")