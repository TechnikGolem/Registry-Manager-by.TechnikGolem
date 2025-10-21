"""
Registry Status Checker
======================

Modul zur Überprüfung des aktuellen Status von Registry-Einträgen.
Vergleicht .reg-Dateien mit den tatsächlichen Registry-Werten.
"""

import winreg
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from src.registry.reg_parser import RegFileParser


class RegistryStatusChecker:
    """Checker für Registry-Status"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.parser = RegFileParser()
        
        # Registry-Root-Keys Mapping
        self.root_keys = {
            'HKEY_CLASSES_ROOT': winreg.HKEY_CLASSES_ROOT,
            'HKEY_CURRENT_USER': winreg.HKEY_CURRENT_USER,
            'HKEY_LOCAL_MACHINE': winreg.HKEY_LOCAL_MACHINE,
            'HKEY_USERS': winreg.HKEY_USERS,
            'HKEY_CURRENT_CONFIG': winreg.HKEY_CURRENT_CONFIG
        }
        
        # Registry-Typ Mapping
        self.reg_types = {
            winreg.REG_SZ: 'REG_SZ',
            winreg.REG_EXPAND_SZ: 'REG_EXPAND_SZ',
            winreg.REG_BINARY: 'REG_BINARY',
            winreg.REG_DWORD: 'REG_DWORD',
            winreg.REG_DWORD_BIG_ENDIAN: 'REG_DWORD_BIG_ENDIAN',
            winreg.REG_LINK: 'REG_LINK',
            winreg.REG_MULTI_SZ: 'REG_MULTI_SZ',
            winreg.REG_RESOURCE_LIST: 'REG_RESOURCE_LIST',
            winreg.REG_FULL_RESOURCE_DESCRIPTOR: 'REG_FULL_RESOURCE_DESCRIPTOR',
            winreg.REG_RESOURCE_REQUIREMENTS_LIST: 'REG_RESOURCE_REQUIREMENTS_LIST',
            winreg.REG_QWORD: 'REG_QWORD'
        }
    
    def check_file_status(self, filepath: str, db_instance=None) -> Dict:
        """
        Status einer gesamten .reg-Datei prüfen
        
        Args:
            filepath: Pfad zur .reg-Datei oder embedded:reg_id
            db_instance: Optional - Database instance für embedded REGs
            
        Returns:
            Status-Dictionary mit Details für jeden Eintrag
        """
        try:
            self.logger.info(f"Prüfe Registry-Status für: {filepath}")
            
            # Datei parsen (mit optional database instance für embedded REGs)
            parsed_data = self.parser.parse_file(filepath, db_instance)
            
            status_result = {
                'file': filepath,
                'timestamp': None,
                'summary': {
                    'total_keys': 0,
                    'active_keys': 0,
                    'missing_keys': 0,
                    'total_values': 0,
                    'matching_values': 0,
                    'different_values': 0,
                    'missing_values': 0
                },
                'keys': {},
                'errors': []
            }
            
            # Timestamp setzen
            import datetime
            status_result['timestamp'] = datetime.datetime.now().isoformat()
            
            # Jeden Key prüfen
            for key_path, key_data in parsed_data.get('keys', {}).items():
                key_status = self._check_key_status(key_path, key_data)
                status_result['keys'][key_path] = key_status
                
                # Statistiken aktualisieren
                status_result['summary']['total_keys'] += 1
                if key_status['exists']:
                    status_result['summary']['active_keys'] += 1
                else:
                    status_result['summary']['missing_keys'] += 1
                
                for value_status in key_status['values'].values():
                    status_result['summary']['total_values'] += 1
                    if value_status['status'] == 'match':
                        status_result['summary']['matching_values'] += 1
                    elif value_status['status'] == 'different':
                        status_result['summary']['different_values'] += 1
                    else:
                        status_result['summary']['missing_values'] += 1
            
            # Gelöschte Keys prüfen
            for deleted_key in parsed_data.get('deleted_keys', []):
                key_exists = self._key_exists(deleted_key)
                status_result['keys'][deleted_key] = {
                    'exists': key_exists,
                    'expected_deleted': True,
                    'status': 'should_not_exist' if key_exists else 'correctly_deleted',
                    'values': {}
                }
            
            # Overall Status berechnen
            status_result['overall_status'] = self._calculate_overall_status(status_result)
            
            self.logger.info(f"Status-Prüfung abgeschlossen für {filepath}")
            return status_result
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Status-Prüfung: {e}")
            return {
                'file': filepath,
                'error': str(e),
                'summary': {},
                'keys': {},
                'errors': [str(e)]
            }
    
    def _calculate_overall_status(self, status_result: Dict) -> str:
        """
        Berechnet den Gesamt-Status basierend auf den Einzelergebnissen
        
        Args:
            status_result: Status-Dictionary
            
        Returns:
            'all_active', 'all_inactive', 'partial', 'unknown'
        """
        try:
            summary = status_result.get('summary', {})
            total_values = summary.get('total_values', 0)
            matching_values = summary.get('matching_values', 0)
            
            if total_values == 0:
                return 'unknown'
            
            # Alle Werte stimmen überein
            if matching_values == total_values:
                return 'all_active'
            
            # Keine Werte stimmen überein
            if matching_values == 0:
                return 'all_inactive'
            
            # Teilweise übereinstimmend
            return 'partial'
            
        except Exception as e:
            self.logger.error(f"Fehler bei Overall-Status-Berechnung: {e}")
            return 'unknown'
    
    def _check_key_status(self, key_path: str, key_data: Dict) -> Dict:
        """
        Status eines einzelnen Registry-Keys prüfen
        
        Args:
            key_path: Registry-Key-Pfad
            key_data: Key-Daten aus geparster .reg-Datei
            
        Returns:
            Status-Dictionary für den Key
        """
        key_status = {
            'exists': False,
            'values': {},
            'errors': []
        }
        
        try:
            # Key öffnen
            root_key, sub_key = self._parse_key_path(key_path)
            if not root_key:
                key_status['errors'].append(f"Ungültiger Key-Pfad: {key_path}")
                return key_status
            
            try:
                with winreg.OpenKey(root_key, sub_key, 0, winreg.KEY_READ) as reg_key:
                    key_status['exists'] = True
                    
                    # Default-Wert prüfen
                    if key_data.get('default_value'):
                        default_status = self._check_value_status(
                            reg_key, None, key_data['default_value']
                        )
                        key_status['values']['@default'] = default_status
                    
                    # Benannte Werte prüfen
                    for value_name, expected_value in key_data.get('values', {}).items():
                        value_status = self._check_value_status(
                            reg_key, value_name, expected_value
                        )
                        key_status['values'][value_name] = value_status
                        
            except FileNotFoundError:
                key_status['exists'] = False
                
                # Alle erwarteten Werte als fehlend markieren
                if key_data.get('default_value'):
                    key_status['values']['@default'] = {
                        'status': 'missing',
                        'expected': key_data['default_value'],
                        'actual': None
                    }
                
                for value_name, expected_value in key_data.get('values', {}).items():
                    key_status['values'][value_name] = {
                        'status': 'missing',
                        'expected': expected_value,
                        'actual': None
                    }
            
        except Exception as e:
            key_status['errors'].append(f"Fehler beim Prüfen des Keys: {e}")
        
        return key_status
    
    def _check_value_status(self, reg_key, value_name: Optional[str], 
                           expected_value: Dict) -> Dict:
        """
        Status eines einzelnen Registry-Werts prüfen
        
        Args:
            reg_key: Geöffneter Registry-Key
            value_name: Name des Werts (None für Default-Wert)
            expected_value: Erwarteter Wert aus .reg-Datei
            
        Returns:
            Status-Dictionary für den Wert
        """
        value_status = {
            'status': 'missing',
            'expected': expected_value,
            'actual': None
        }
        
        try:
            # Aktuellen Wert lesen
            if value_name is None:
                # Default-Wert
                actual_value, reg_type = winreg.QueryValue(reg_key, ""), winreg.REG_SZ
            else:
                actual_value, reg_type = winreg.QueryValueEx(reg_key, value_name)
            
            # Aktuellen Wert in Dictionary-Format konvertieren
            actual_dict = {
                'type': self.reg_types.get(reg_type, f'UNKNOWN({reg_type})'),
                'data': actual_value
            }
            value_status['actual'] = actual_dict
            
            # Lösch-Aktion?
            if expected_value.get('action') == 'delete':
                value_status['status'] = 'should_not_exist'
                return value_status
            
            # Werte vergleichen
            if self._compare_values(expected_value, actual_dict):
                value_status['status'] = 'match'
            else:
                value_status['status'] = 'different'
                
        except FileNotFoundError:
            # Wert existiert nicht
            if expected_value.get('action') == 'delete':
                value_status['status'] = 'correctly_deleted'
            else:
                value_status['status'] = 'missing'
        except Exception as e:
            value_status['error'] = str(e)
        
        return value_status
    
    def _compare_values(self, expected: Dict, actual: Dict) -> bool:
        """
        Zwei Registry-Werte vergleichen
        
        Args:
            expected: Erwarteter Wert
            actual: Tatsächlicher Wert
            
        Returns:
            True wenn die Werte übereinstimmen
        """
        try:
            # Typ vergleichen
            if expected.get('type') != actual.get('type'):
                return False
            
            expected_data = expected.get('data')
            actual_data = actual.get('data')
            
            # Daten vergleichen je nach Typ
            value_type = expected.get('type')
            
            if value_type in ['REG_SZ', 'REG_EXPAND_SZ']:
                return str(expected_data) == str(actual_data)
            
            elif value_type in ['REG_DWORD', 'REG_QWORD']:
                return int(expected_data) == int(actual_data)
            
            elif value_type == 'REG_BINARY':
                if isinstance(expected_data, list) and isinstance(actual_data, bytes):
                    return expected_data == list(actual_data)
                elif isinstance(expected_data, list) and isinstance(actual_data, list):
                    return expected_data == actual_data
                return expected_data == actual_data
            
            elif value_type == 'REG_MULTI_SZ':
                if isinstance(expected_data, list) and isinstance(actual_data, list):
                    return expected_data == actual_data
                return str(expected_data) == str(actual_data)
            
            else:
                # Fallback: String-Vergleich
                return str(expected_data) == str(actual_data)
                
        except Exception:
            return False
    
    def _parse_key_path(self, key_path: str) -> Tuple[Optional[int], str]:
        """
        Registry-Key-Pfad in Root-Key und Sub-Key aufteilen
        
        Args:
            key_path: Vollständiger Key-Pfad
            
        Returns:
            Tuple aus (Root-Key-Handle, Sub-Key-Pfad)
        """
        for root_name, root_handle in self.root_keys.items():
            if key_path.startswith(root_name):
                sub_key = key_path[len(root_name):].lstrip('\\')
                return root_handle, sub_key
        
        return None, key_path
    
    def _key_exists(self, key_path: str) -> bool:
        """
        Prüfen ob ein Registry-Key existiert
        
        Args:
            key_path: Registry-Key-Pfad
            
        Returns:
            True wenn Key existiert
        """
        try:
            root_key, sub_key = self._parse_key_path(key_path)
            if not root_key:
                return False
            
            with winreg.OpenKey(root_key, sub_key, 0, winreg.KEY_READ):
                return True
                
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    def get_status_summary(self, status_result: Dict) -> str:
        """
        Zusammenfassung des Status als String
        
        Args:
            status_result: Status-Ergebnis
            
        Returns:
            Formatierte Zusammenfassung
        """
        summary = status_result.get('summary', {})
        
        lines = [
            f"Registry-Status Zusammenfassung:",
            f"",
            f"Keys: {summary.get('active_keys', 0)}/{summary.get('total_keys', 0)} aktiv",
            f"Werte: {summary.get('matching_values', 0)}/{summary.get('total_values', 0)} übereinstimmend",
            f""
        ]
        
        if summary.get('missing_keys', 0) > 0:
            lines.append(f"⚠️ {summary.get('missing_keys', 0)} Keys fehlen")
        
        if summary.get('different_values', 0) > 0:
            lines.append(f"⚠️ {summary.get('different_values', 0)} Werte sind unterschiedlich")
        
        if summary.get('missing_values', 0) > 0:
            lines.append(f"⚠️ {summary.get('missing_values', 0)} Werte fehlen")
        
        return '\\n'.join(lines)
    
    def export_status_report(self, status_result: Dict, output_path: str) -> bool:
        """
        Detaillierten Status-Report exportieren
        
        Args:
            status_result: Status-Ergebnis
            output_path: Ausgabe-Pfad für den Report
            
        Returns:
            True bei Erfolg
        """
        try:
            import json
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(status_result, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Status-Report exportiert: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Exportieren des Reports: {e}")
            return False