"""
Registry Content Analyzer
=========================

Analysiert Registry-Dateien und ermittelt automatisch Kategorien und Beschreibungen.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class RegistryContentAnalyzer:
    """Analysiert Registry-Inhalte für automatische Kategorisierung"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Kategorie-Erkennungsregeln
        self.category_patterns = {
            'System': [
                r'HKEY_LOCAL_MACHINE\\SYSTEM',
                r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run',
                r'Windows\\CurrentVersion\\Explorer\\Advanced',
                r'ControlPanel',
                r'SystemRoot',
                r'Windows NT\\CurrentVersion',
                r'Services\\',
                r'Drivers\\',
                r'Boot\\',
                r'System32'
            ],
            'Design': [
                r'Themes',
                r'Desktop\\Wallpaper',
                r'Colors',
                r'Appearance',
                r'WindowMetrics',
                r'Desktop\\WindowArrangement',
                r'Explorer\\Advanced\\ShowSuperHidden',
                r'PersonalizationCSP',
                r'DWM\\',
                r'Aero',
                r'Theme',
                r'Visual'
            ],
            'Performance': [
                r'Performance',
                r'Memory',
                r'Processor',
                r'PrefetchParameters',
                r'SuperFetch',
                r'ReadyBoost',
                r'Performance\\',
                r'CPU',
                r'RAM',
                r'Cache',
                r'Optimization'
            ],
            'Sicherheit': [
                r'Security',
                r'Firewall',
                r'Windows Defender',
                r'UAC',
                r'WindowsUpdate',
                r'Antivirus',
                r'Policies\\System',
                r'Authentication',
                r'Password',
                r'Encryption',
                r'BitLocker',
                r'SmartScreen'
            ],
            'Privacy': [
                r'Privacy',
                r'Telemetry',
                r'DataCollection',
                r'DiagTrack',
                r'AppHost',
                r'AdvertisingInfo',
                r'LocationAndSensors',
                r'Feedback',
                r'SpeechServices',
                r'InputPersonalization'
            ],
            'Entwicklung': [
                r'Visual Studio',
                r'Git',
                r'Python',
                r'Node\.js',
                r'Code\.exe',
                r'PowerShell',
                r'cmd\.exe',
                r'Developer',
                r'SDK',
                r'JetBrains',
                r'IntelliJ',
                r'Eclipse'
            ],
            'Gaming': [
                r'Steam',
                r'Games',
                r'DirectX',
                r'Gaming',
                r'GameDVR',
                r'Xbox',
                r'Graphics',
                r'NVIDIA',
                r'AMD',
                r'Radeon',
                r'GeForce'
            ],
            'Netzwerk': [
                r'Network',
                r'Internet',
                r'TCP',
                r'IP',
                r'Ethernet',
                r'WiFi',
                r'Wireless',
                r'VPN',
                r'Proxy',
                r'DNS',
                r'DHCP',
                r'Firewall'
            ],
            'Software': [
                r'Uninstall\\',
                r'SOFTWARE\\',
                r'Applications\\',
                r'Programs\\',
                r'Microsoft Office',
                r'Adobe',
                r'Google',
                r'Mozilla',
                r'Chrome',
                r'Firefox'
            ]
        }
        
        # Beschreibungsregeln
        self.description_patterns = {
            r'Hide.*Desktop.*Icons?': 'Versteckt Desktop-Icons',
            r'Dark.*Theme': 'Aktiviert dunkles Design',
            r'Context.*Menu': 'Erweitert Kontextmenü',
            r'Explorer.*Advanced': 'Erweiterte Explorer-Einstellungen',
            r'UAC.*Disable': 'Deaktiviert Benutzerkontensteuerung',
            r'Telemetry.*Disable': 'Deaktiviert Telemetrie-Datensammlung',
            r'Windows.*Update': 'Konfiguriert Windows-Updates',
            r'Performance.*Tweak': 'Optimiert System-Performance',
            r'Gaming.*Mode': 'Aktiviert Gaming-Optimierungen',
            r'Privacy.*Settings': 'Verbessert Datenschutz-Einstellungen'
        }
    
    def analyze_file(self, file_path: str) -> Dict[str, str]:
        """
        Analysiert eine Registry-Datei und ermittelt Kategorie und Beschreibung
        
        Args:
            file_path: Pfad zur .reg-Datei
            
        Returns:
            Dict mit 'category', 'description', 'formatted_name'
        """
        try:
            # Datei einlesen
            content = self._read_reg_file(file_path)
            if not content:
                return self._fallback_analysis(file_path)
            
            # Dateiname formatieren
            formatted_name = self._format_filename(Path(file_path).stem)
            
            # Kategorie ermitteln
            category = self._detect_category(content, formatted_name)
            
            # Beschreibung generieren
            description = self._generate_description(content, formatted_name)
            
            return {
                'category': category,
                'description': description,
                'formatted_name': formatted_name
            }
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Analyse von {file_path}: {e}")
            return self._fallback_analysis(file_path)
    
    def _read_reg_file(self, file_path: str) -> str:
        """Registry-Datei einlesen mit verschiedenen Encodings"""
        encodings = ['utf-8-sig', 'utf-16', 'utf-8', 'cp1252', 'latin1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self.logger.warning(f"Fehler beim Lesen mit {encoding}: {e}")
                continue
        
        return ""
    
    def _format_filename(self, filename: str) -> str:
        """Dateiname formatieren: Bindestriche/Unterstriche entfernen, Großschreibung"""
        # Alle Arten von Bindestrichen und Unterstrichen durch Leerzeichen ersetzen
        formatted = filename.replace('-', ' ').replace('_', ' ').replace('–', ' ').replace('—', ' ')
        
        # Punkte durch Leerzeichen ersetzen (außer am Ende)
        if not formatted.endswith('.'):
            formatted = formatted.replace('.', ' ')
        
        # Mehrfache Leerzeichen reduzieren
        formatted = re.sub(r'\s+', ' ', formatted)
        
        # Jeden Wortanfang großschreiben
        formatted = ' '.join(word.capitalize() for word in formatted.split())
        
        return formatted.strip()
    
    def _detect_category(self, content: str, filename: str) -> str:
        """Kategorie basierend auf Inhalt und Dateiname erkennen"""
        content_lower = content.lower()
        filename_lower = filename.lower()
        
        category_scores = {}
        
        # Punkte für Kategorie-Patterns im Inhalt
        for category, patterns in self.category_patterns.items():
            score = 0
            for pattern in patterns:
                # Im Inhalt suchen
                if re.search(pattern, content, re.IGNORECASE):
                    score += 3
                # Im Dateinamen suchen
                if re.search(pattern.lower(), filename_lower):
                    score += 2
            
            if score > 0:
                category_scores[category] = score
        
        # Zusätzliche Keyword-Analyse
        keyword_categories = {
            'system': ['system', 'registry', 'windows', 'boot', 'startup'],
            'design': ['theme', 'color', 'appearance', 'visual', 'desktop', 'wallpaper'],
            'performance': ['performance', 'speed', 'optimization', 'fast', 'memory'],
            'sicherheit': ['security', 'uac', 'defender', 'firewall', 'secure'],
            'privacy': ['privacy', 'telemetry', 'tracking', 'data', 'collection'],
            'entwicklung': ['vscode', 'visual studio', 'code', 'developer', 'programming'],
            'gaming': ['gaming', 'game', 'directx', 'nvidia', 'amd', 'fps'],
            'netzwerk': ['network', 'internet', 'wifi', 'ethernet', 'connection']
        }
        
        for category, keywords in keyword_categories.items():
            for keyword in keywords:
                if keyword in content_lower or keyword in filename_lower:
                    cat_name = category.capitalize()
                    if cat_name == 'System':
                        cat_name = 'System'
                    elif cat_name == 'Sicherheit':
                        cat_name = 'Sicherheit'
                    elif cat_name == 'Entwicklung':
                        cat_name = 'Entwicklung'
                    
                    category_scores[cat_name] = category_scores.get(cat_name, 0) + 1
        
        # Beste Kategorie zurückgeben
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return 'Sonstiges'
    
    def _generate_description(self, content: str, filename: str) -> str:
        """Automatische Beschreibung generieren"""
        # Vordefinierte Beschreibungen für bekannte Patterns
        for pattern, description in self.description_patterns.items():
            if re.search(pattern, filename, re.IGNORECASE):
                return description
        
        # Registry-Keys analysieren
        key_matches = re.findall(r'\[([^\]]+)\]', content)
        if key_matches:
            main_key = key_matches[0]
            
            # Beschreibung basierend auf Registry-Pfad
            if 'Explorer\\Advanced' in main_key:
                return 'Erweiterte Explorer-Einstellungen'
            elif 'Desktop' in main_key:
                return 'Desktop-Konfiguration'
            elif 'Run' in main_key:
                return 'Autostart-Einstellungen'
            elif 'Themes' in main_key:
                return 'Design- und Theme-Einstellungen'
            elif 'Performance' in main_key:
                return 'System-Performance-Optimierung'
            elif 'Privacy' in main_key or 'Telemetry' in main_key:
                return 'Datenschutz-Einstellungen'
            elif 'Security' in main_key or 'UAC' in main_key:
                return 'Sicherheits-Konfiguration'
        
        # Fallback: Beschreibung aus Dateiname ableiten
        if 'hide' in filename.lower():
            return f'Versteckt oder zeigt {filename.lower().replace("hide", "").strip()}'
        elif 'enable' in filename.lower():
            return f'Aktiviert {filename.lower().replace("enable", "").strip()}'
        elif 'disable' in filename.lower():
            return f'Deaktiviert {filename.lower().replace("disable", "").strip()}'
        elif 'tweak' in filename.lower():
            return f'Optimiert {filename.lower().replace("tweak", "").strip()}'
        
        return filename
    
    def _fallback_analysis(self, file_path: str) -> Dict[str, str]:
        """Fallback-Analyse wenn Datei nicht gelesen werden kann"""
        filename = Path(file_path).stem
        formatted_name = self._format_filename(filename)
        
        return {
            'category': 'Sonstiges',
            'description': formatted_name,
            'formatted_name': formatted_name
        }