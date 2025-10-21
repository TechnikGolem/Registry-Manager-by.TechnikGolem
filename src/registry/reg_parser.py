"""
Registry File Parser
==================

Modul zum Parsen und Analysieren von Windows Registry-Files (.reg).
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class RegFileParser:
    """Parser für Windows Registry-Files"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Regex-Patterns für Registry-Einträge
        self.key_pattern = re.compile(r'^\[([^\]]+)\]$')
        self.value_pattern = re.compile(r'^"([^"]*)"=(.+)$')
        self.default_value_pattern = re.compile(r'^@=(.+)$')
        self.delete_key_pattern = re.compile(r'^\[-([^\]]+)\]$')
        self.delete_value_pattern = re.compile(r'^"([^"]*)"=-$')
    
    def parse_file(self, filepath: str, db_instance=None) -> Dict:
        """
        Registry-Datei parsen
        
        Args:
            filepath: Pfad zur .reg-Datei oder embedded:reg_id
            db_instance: Optional - Database instance für embedded REGs
            
        Returns:
            Dictionary mit geparsten Registry-Daten
        """
        try:
            self.logger.info(f"Parse Registry-Datei: {filepath}")
            
            # Prüfung für embedded REG files
            if filepath.startswith("embedded:"):
                if not db_instance:
                    raise ValueError("Database instance required for embedded REG files")
                
                reg_id = filepath.replace("embedded:", "")
                reg_data = db_instance.get_embedded_reg(reg_id)
                if not reg_data:
                    raise FileNotFoundError(f"Embedded REG {reg_id} not found")
                
                return self.parse_content(reg_data['content'])
            
            # Normale Datei-basierte REG files
            # Verschiedene Encodings versuchen
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
                # Als letzte Option binär lesen und versuchen zu dekodieren
                with open(filepath, 'rb') as f:
                    raw_content = f.read()
                try:
                    content = raw_content.decode('utf-8-sig')
                except:
                    content = raw_content.decode('utf-8', errors='replace')
            
            return self.parse_content(content)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Parsen der Datei {filepath}: {e}")
            raise
    
    def parse_content(self, content: str) -> Dict:
        """
        Registry-Inhalt parsen
        
        Args:
            content: Registry-Dateiinhalt als String
            
        Returns:
            Dictionary mit geparsten Daten
        """
        result = {
            'version': None,
            'keys': {},
            'deleted_keys': [],
            'errors': []
        }
        
        lines = content.splitlines()
        current_key = None
        line_number = 0
        
        try:
            for line in lines:
                line_number += 1
                line = line.strip()
                
                # Leere Zeilen und Kommentare überspringen
                if not line or line.startswith(';'):
                    continue
                
                # Registry-Version
                if line.startswith('Windows Registry Editor'):
                    result['version'] = line
                    continue
                
                # Registry-Key (normal)
                key_match = self.key_pattern.match(line)
                if key_match:
                    current_key = key_match.group(1)
                    if current_key not in result['keys']:
                        result['keys'][current_key] = {
                            'values': {},
                            'default_value': None
                        }
                    continue
                
                # Registry-Key (löschen)
                delete_key_match = self.delete_key_pattern.match(line)
                if delete_key_match:
                    deleted_key = delete_key_match.group(1)
                    result['deleted_keys'].append(deleted_key)
                    continue
                
                # Wenn wir in einem Key sind
                if current_key:
                    # Default-Wert
                    default_match = self.default_value_pattern.match(line)
                    if default_match:
                        value_data = self._parse_value(default_match.group(1))
                        result['keys'][current_key]['default_value'] = value_data
                        continue
                    
                    # Benannter Wert
                    value_match = self.value_pattern.match(line)
                    if value_match:
                        value_name = value_match.group(1)
                        value_raw = value_match.group(2)
                        
                        if value_raw == '-':
                            # Wert löschen
                            result['keys'][current_key]['values'][value_name] = {
                                'type': 'DELETE',
                                'data': None
                            }
                        else:
                            value_data = self._parse_value(value_raw)
                            result['keys'][current_key]['values'][value_name] = value_data
                        continue
                    
                    # Mehrzeilige Werte (Hex-Daten)
                    if line.endswith('\\'):
                        # Dies ist der Beginn mehrzeiliger Daten
                        # Hier könnte erweiterte Logik für mehrzeilige Hex-Werte implementiert werden
                        pass
                
                # Unbekannte Zeile
                if line and not line.startswith(';'):
                    result['errors'].append(f"Zeile {line_number}: Unbekanntes Format: {line}")
        
        except Exception as e:
            result['errors'].append(f"Zeile {line_number}: Parsing-Fehler: {e}")
        
        self.logger.info(f"Parsing abgeschlossen. {len(result['keys'])} Keys gefunden, {len(result['errors'])} Fehler")
        return result
    
    def _parse_value(self, value_str: str) -> Dict:
        """
        Registry-Wert parsen
        
        Args:
            value_str: Wert-String aus der .reg-Datei
            
        Returns:
            Dictionary mit Typ und Daten
        """
        value_str = value_str.strip()
        
        # String-Wert
        if value_str.startswith('"') and value_str.endswith('"'):
            return {
                'type': 'REG_SZ',
                'data': value_str[1:-1].replace('\\"', '"')
            }
        
        # DWORD-Wert
        if value_str.startswith('dword:'):
            hex_value = value_str[6:]
            try:
                return {
                    'type': 'REG_DWORD',
                    'data': int(hex_value, 16)
                }
            except ValueError:
                return {
                    'type': 'REG_DWORD',
                    'data': 0,
                    'error': f"Ungültiger DWORD-Wert: {value_str}"
                }
        
        # QWORD-Wert
        if value_str.startswith('qword:'):
            hex_value = value_str[6:]
            try:
                return {
                    'type': 'REG_QWORD',
                    'data': int(hex_value, 16)
                }
            except ValueError:
                return {
                    'type': 'REG_QWORD',
                    'data': 0,
                    'error': f"Ungültiger QWORD-Wert: {value_str}"
                }
        
        # Hex-Werte (REG_BINARY, REG_MULTI_SZ, etc.)
        if value_str.startswith('hex'):
            if value_str.startswith('hex:'):
                reg_type = 'REG_BINARY'
                hex_data = value_str[4:]
            elif value_str.startswith('hex('):
                # hex(type):data Format
                type_match = re.match(r'hex\(([^)]+)\):', value_str)
                if type_match:
                    type_code = type_match.group(1)
                    hex_data = value_str[len(type_match.group(0)):]
                    reg_type = self._get_reg_type_from_code(type_code)
                else:
                    reg_type = 'REG_BINARY'
                    hex_data = value_str
            else:
                reg_type = 'REG_BINARY'
                hex_data = value_str
            
            # Hex-Daten parsen
            try:
                hex_bytes = []
                for hex_pair in hex_data.split(','):
                    hex_pair = hex_pair.strip()
                    if hex_pair and hex_pair != '\\':
                        hex_bytes.append(int(hex_pair, 16))
                
                return {
                    'type': reg_type,
                    'data': hex_bytes
                }
            except ValueError as e:
                return {
                    'type': reg_type,
                    'data': [],
                    'error': f"Ungültige Hex-Daten: {e}"
                }
        
        # Unbekannter Typ
        return {
            'type': 'UNKNOWN',
            'data': value_str,
            'error': f"Unbekannter Wert-Typ: {value_str}"
        }
    
    def _get_reg_type_from_code(self, type_code: str) -> str:
        """Registry-Typ aus Code ermitteln"""
        type_mapping = {
            '0': 'REG_NONE',
            '1': 'REG_SZ',
            '2': 'REG_EXPAND_SZ',
            '3': 'REG_BINARY',
            '4': 'REG_DWORD',
            '5': 'REG_DWORD_BIG_ENDIAN',
            '6': 'REG_LINK',
            '7': 'REG_MULTI_SZ',
            '8': 'REG_RESOURCE_LIST',
            '9': 'REG_FULL_RESOURCE_DESCRIPTOR',
            'a': 'REG_RESOURCE_REQUIREMENTS_LIST',
            'b': 'REG_QWORD'
        }
        
        return type_mapping.get(type_code.lower(), 'REG_BINARY')
    
    def get_summary(self, parsed_data: Dict) -> Dict:
        """
        Zusammenfassung der geparsten Daten erstellen
        
        Args:
            parsed_data: Geparste Registry-Daten
            
        Returns:
            Zusammenfassung
        """
        summary = {
            'total_keys': len(parsed_data['keys']),
            'deleted_keys': len(parsed_data['deleted_keys']),
            'total_values': 0,
            'value_types': {},
            'errors': len(parsed_data['errors']),
            'root_keys': set()
        }
        
        for key_path, key_data in parsed_data['keys'].items():
            # Root-Key ermitteln
            root_key = key_path.split('\\')[0]
            summary['root_keys'].add(root_key)
            
            # Werte zählen
            summary['total_values'] += len(key_data['values'])
            if key_data['default_value']:
                summary['total_values'] += 1
            
            # Wert-Typen zählen
            for value_data in key_data['values'].values():
                value_type = value_data['type']
                summary['value_types'][value_type] = summary['value_types'].get(value_type, 0) + 1
            
            if key_data['default_value']:
                value_type = key_data['default_value']['type']
                summary['value_types'][value_type] = summary['value_types'].get(value_type, 0) + 1
        
        summary['root_keys'] = list(summary['root_keys'])
        return summary
    
    def validate_file(self, filepath: str) -> Dict:
        """
        Registry-Datei validieren
        
        Args:
            filepath: Pfad zur .reg-Datei
            
        Returns:
            Validierungsergebnis
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Datei existiert?
            if not Path(filepath).exists():
                result['valid'] = False
                result['errors'].append("Datei existiert nicht")
                return result
            
            # Datei parsen
            parsed_data = self.parse_file(filepath)
            
            # Fehler beim Parsen?
            if parsed_data['errors']:
                result['warnings'].extend(parsed_data['errors'])
            
            # Version prüfen
            if not parsed_data['version']:
                result['warnings'].append("Keine gültige Registry-Version gefunden")
            
            # Mindestens ein Key?
            if not parsed_data['keys'] and not parsed_data['deleted_keys']:
                result['warnings'].append("Keine Registry-Einträge gefunden")
            
            # Gefährliche Keys prüfen
            dangerous_keys = [
                'HKEY_LOCAL_MACHINE\\SYSTEM',
                'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run'
            ]
            
            for key_path in parsed_data['keys']:
                for dangerous in dangerous_keys:
                    if key_path.startswith(dangerous):
                        result['warnings'].append(f"Potentiell gefährlicher Key: {key_path}")
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Validierungsfehler: {e}")
        
        return result