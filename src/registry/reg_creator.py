"""
Registry File Creator
====================

Modul zum Erstellen neuer Windows Registry-Files (.reg).
"""

import logging
from typing import Dict, List, Optional, Union
from pathlib import Path
from datetime import datetime


class RegFileCreator:
    """Ersteller für Windows Registry-Files"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Registry-Root-Keys
        self.root_keys = {
            'HKEY_CLASSES_ROOT': 'HKCR',
            'HKEY_CURRENT_USER': 'HKCU', 
            'HKEY_LOCAL_MACHINE': 'HKLM',
            'HKEY_USERS': 'HKU',
            'HKEY_CURRENT_CONFIG': 'HKCC'
        }
    
    def create_file(self, filepath: str, registry_data: Dict, 
                   title: str = None, description: str = None) -> bool:
        """
        Registry-Datei erstellen
        
        Args:
            filepath: Ziel-Pfad für die .reg-Datei
            registry_data: Registry-Daten Dictionary
            title: Titel für die Datei (als Kommentar)
            description: Beschreibung für die Datei (als Kommentar)
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            self.logger.info(f"Erstelle Registry-Datei: {filepath}")
            
            content = self._generate_content(registry_data, title, description)
            
            # Datei schreiben
            with open(filepath, 'w', encoding='utf-8-sig') as f:
                f.write(content)
            
            self.logger.info(f"Registry-Datei erfolgreich erstellt: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen der Registry-Datei: {e}")
            return False
    
    def _generate_content(self, registry_data: Dict, title: str = None, 
                         description: str = None) -> str:
        """
        Registry-Dateiinhalt generieren
        
        Args:
            registry_data: Registry-Daten
            title: Titel
            description: Beschreibung
            
        Returns:
            Generierter Dateiinhalt
        """
        lines = []
        
        # Header
        lines.append("Windows Registry Editor Version 5.00")
        lines.append("")
        
        # Kommentare hinzufügen
        if title or description:
            lines.append(f"; ==========================================")
            
            if title:
                lines.append(f"; {title}")
                
            if description:
                lines.append(f"; ")
                for desc_line in description.split('\n'):
                    lines.append(f"; {desc_line}")
                    
            lines.append(f"; ")
            lines.append(f"; Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
            lines.append(f"; ==========================================")
            lines.append("")
        
        # Registry-Keys verarbeiten
        for key_path, key_data in registry_data.get('keys', {}).items():
            lines.append(f"[{key_path}]")
            
            # Default-Wert
            if 'default_value' in key_data and key_data['default_value'] is not None:
                value_str = self._format_value(key_data['default_value'])
                lines.append(f"@={value_str}")
            
            # Benannte Werte
            for value_name, value_data in key_data.get('values', {}).items():
                if value_data.get('action') == 'delete':
                    lines.append(f'"{value_name}"=-')
                else:
                    value_str = self._format_value(value_data)
                    lines.append(f'"{value_name}"={value_str}')
            
            lines.append("")
        
        # Keys zum Löschen
        for deleted_key in registry_data.get('deleted_keys', []):
            lines.append(f"[-{deleted_key}]")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _format_value(self, value_data: Union[Dict, str, int]) -> str:
        """
        Registry-Wert formatieren
        
        Args:
            value_data: Wert-Daten
            
        Returns:
            Formatierter Wert-String
        """
        # Einfache Werte (für Rückwärtskompatibilität)
        if isinstance(value_data, str):
            return f'"{value_data}"'
        elif isinstance(value_data, int):
            return f"dword:{value_data:08x}"
        
        # Dictionary-Format
        if not isinstance(value_data, dict):
            return f'"{str(value_data)}"'
        
        value_type = value_data.get('type', 'REG_SZ')
        data = value_data.get('data')
        
        if value_type == 'REG_SZ':
            # String-Wert
            if data is None:
                return '""'
            escaped = str(data).replace('"', '\\"')
            return f'"{escaped}"'
        
        elif value_type == 'REG_DWORD':
            # DWORD-Wert
            if isinstance(data, int):
                return f"dword:{data:08x}"
            else:
                return "dword:00000000"
        
        elif value_type == 'REG_QWORD':
            # QWORD-Wert
            if isinstance(data, int):
                return f"qword:{data:016x}"
            else:
                return "qword:0000000000000000"
        
        elif value_type == 'REG_BINARY':
            # Binäre Daten
            if isinstance(data, (list, tuple)):
                hex_values = [f"{b:02x}" for b in data]
                if len(hex_values) <= 8:
                    return f"hex:{','.join(hex_values)}"
                else:
                    # Mehrzeilige Ausgabe für längere Daten
                    lines = []
                    for i in range(0, len(hex_values), 16):
                        chunk = hex_values[i:i+16]
                        if i + 16 < len(hex_values):
                            lines.append(','.join(chunk) + ',\\')
                        else:
                            lines.append(','.join(chunk))
                    return f"hex:{lines[0]}" + '\n  ' + '\n  '.join(lines[1:])
            else:
                return "hex:"
        
        elif value_type == 'REG_MULTI_SZ':
            # Multi-String
            if isinstance(data, (list, tuple)):
                # Strings zu Unicode-Bytes konvertieren
                unicode_bytes = []
                for string in data:
                    for char in str(string):
                        unicode_bytes.extend([ord(char) & 0xFF, (ord(char) >> 8) & 0xFF])
                    unicode_bytes.extend([0, 0])  # Null-Terminator
                unicode_bytes.extend([0, 0])  # Doppelter Null-Terminator am Ende
                
                hex_values = [f"{b:02x}" for b in unicode_bytes]
                return f"hex(7):{','.join(hex_values)}"
            else:
                return "hex(7):00,00"
        
        elif value_type == 'REG_EXPAND_SZ':
            # Expandierbarer String
            if data is None:
                unicode_bytes = [0, 0]
            else:
                unicode_bytes = []
                for char in str(data):
                    unicode_bytes.extend([ord(char) & 0xFF, (ord(char) >> 8) & 0xFF])
                unicode_bytes.extend([0, 0])  # Null-Terminator
            
            hex_values = [f"{b:02x}" for b in unicode_bytes]
            return f"hex(2):{','.join(hex_values)}"
        
        else:
            # Unbekannter Typ - als String behandeln
            return f'"{str(data)}"'
    
    def create_simple_string_entry(self, key_path: str, value_name: str, 
                                  value_data: str) -> Dict:
        """
        Einfachen String-Eintrag erstellen
        
        Args:
            key_path: Registry-Key-Pfad
            value_name: Name des Werts
            value_data: String-Daten
            
        Returns:
            Registry-Daten Dictionary
        """
        return {
            'keys': {
                key_path: {
                    'values': {
                        value_name: {
                            'type': 'REG_SZ',
                            'data': value_data
                        }
                    }
                }
            }
        }
    
    def create_dword_entry(self, key_path: str, value_name: str, 
                          value_data: int) -> Dict:
        """
        DWORD-Eintrag erstellen
        
        Args:
            key_path: Registry-Key-Pfad
            value_name: Name des Werts
            value_data: Integer-Wert
            
        Returns:
            Registry-Daten Dictionary
        """
        return {
            'keys': {
                key_path: {
                    'values': {
                        value_name: {
                            'type': 'REG_DWORD',
                            'data': value_data
                        }
                    }
                }
            }
        }
    
    def create_delete_key_entry(self, key_path: str) -> Dict:
        """
        Key-Lösch-Eintrag erstellen
        
        Args:
            key_path: Registry-Key-Pfad zum Löschen
            
        Returns:
            Registry-Daten Dictionary
        """
        return {
            'deleted_keys': [key_path]
        }
    
    def create_delete_value_entry(self, key_path: str, value_name: str) -> Dict:
        """
        Wert-Lösch-Eintrag erstellen
        
        Args:
            key_path: Registry-Key-Pfad
            value_name: Name des zu löschenden Werts
            
        Returns:
            Registry-Daten Dictionary
        """
        return {
            'keys': {
                key_path: {
                    'values': {
                        value_name: {
                            'action': 'delete'
                        }
                    }
                }
            }
        }
    
    def merge_registry_data(self, *data_dicts: Dict) -> Dict:
        """
        Mehrere Registry-Daten-Dictionaries zusammenführen
        
        Args:
            *data_dicts: Variable Anzahl von Registry-Daten-Dictionaries
            
        Returns:
            Zusammengeführtes Dictionary
        """
        merged = {
            'keys': {},
            'deleted_keys': []
        }
        
        for data_dict in data_dicts:
            # Keys zusammenführen
            for key_path, key_data in data_dict.get('keys', {}).items():
                if key_path not in merged['keys']:
                    merged['keys'][key_path] = {'values': {}}
                
                # Default-Wert
                if 'default_value' in key_data:
                    merged['keys'][key_path]['default_value'] = key_data['default_value']
                
                # Werte zusammenführen
                merged['keys'][key_path]['values'].update(key_data.get('values', {}))
            
            # Gelöschte Keys zusammenführen
            merged['deleted_keys'].extend(data_dict.get('deleted_keys', []))
        
        # Duplikate entfernen
        merged['deleted_keys'] = list(set(merged['deleted_keys']))
        
        return merged
    
    def validate_key_path(self, key_path: str) -> bool:
        """
        Registry-Key-Pfad validieren
        
        Args:
            key_path: Zu validierender Key-Pfad
            
        Returns:
            True wenn gültig, False sonst
        """
        if not key_path:
            return False
        
        # Muss mit einem Root-Key beginnen
        for root_key in self.root_keys:
            if key_path.startswith(root_key):
                return True
        
        return False
    
    def get_template_data(self, template_name: str) -> Optional[Dict]:
        """
        Vordefinierte Template-Daten abrufen
        
        Args:
            template_name: Name des Templates
            
        Returns:
            Template-Daten oder None
        """
        templates = {
            'disable_windows_defender': {
                'keys': {
                    'HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows Defender': {
                        'values': {
                            'DisableAntiSpyware': {'type': 'REG_DWORD', 'data': 1}
                        }
                    }
                }
            },
            
            'hide_desktop_icons': {
                'keys': {
                    'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced': {
                        'values': {
                            'HideIcons': {'type': 'REG_DWORD', 'data': 1}
                        }
                    }
                }
            },
            
            'disable_cortana': {
                'keys': {
                    'HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search': {
                        'values': {
                            'AllowCortana': {'type': 'REG_DWORD', 'data': 0}
                        }
                    }
                }
            },
            
            'dark_theme': {
                'keys': {
                    'HKEY_CURRENT_USER\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize': {
                        'values': {
                            'AppsUseLightTheme': {'type': 'REG_DWORD', 'data': 0},
                            'SystemUsesLightTheme': {'type': 'REG_DWORD', 'data': 0}
                        }
                    }
                }
            }
        }
        
        return templates.get(template_name)