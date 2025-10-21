"""
System-Neustart mit automatischem Programm-Wiederstart
"""
import winreg
import sys
import os
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SystemRestart:
    """Verwaltet System-Neustart mit Auto-Wiederstart der App"""
    
    AUTOSTART_KEY = r"Software\Microsoft\Windows\CurrentVersion\RunOnce"
    APP_NAME = "RegistryManager"
    
    @staticmethod
    def setup_auto_restart():
        """
        Richtet automatischen Neustart der App nach System-Neustart ein
        Verwendet RunOnce Registry-Key für einmaliges Auto-Start
        """
        try:
            # Pfad zur ausführbaren Datei ermitteln
            if getattr(sys, 'frozen', False):
                # EXE-Modus
                app_path = sys.executable
            else:
                # Script-Modus: Python + main.py
                python_exe = sys.executable
                main_script = Path(__file__).parent.parent.parent / "main.py"
                app_path = f'"{python_exe}" "{main_script}"'
            
            logger.info(f"Richte Auto-Restart ein: {app_path}")
            
            # RunOnce Key öffnen/erstellen (HKCU für keine Admin-Rechte nötig)
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                SystemRestart.AUTOSTART_KEY,
                0,
                winreg.KEY_SET_VALUE
            )
            
            # App-Eintrag setzen (wird nach einem Start automatisch gelöscht)
            winreg.SetValueEx(
                key,
                SystemRestart.APP_NAME,
                0,
                winreg.REG_SZ,
                app_path
            )
            
            winreg.CloseKey(key)
            logger.info("Auto-Restart erfolgreich eingerichtet")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Einrichten von Auto-Restart: {e}")
            return False
    
    @staticmethod
    def remove_auto_restart():
        """
        Entfernt Auto-Restart Eintrag (z.B. wenn Benutzer Neustart abbricht)
        """
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                SystemRestart.AUTOSTART_KEY,
                0,
                winreg.KEY_SET_VALUE
            )
            
            try:
                winreg.DeleteValue(key, SystemRestart.APP_NAME)
                logger.info("Auto-Restart Eintrag entfernt")
            except FileNotFoundError:
                # Eintrag existiert nicht - kein Problem
                pass
            
            winreg.CloseKey(key)
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Entfernen von Auto-Restart: {e}")
            return False
    
    @staticmethod
    def check_auto_restart_exists():
        """
        Prüft ob ein Auto-Restart Eintrag existiert
        """
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                SystemRestart.AUTOSTART_KEY,
                0,
                winreg.KEY_READ
            )
            
            try:
                value, _ = winreg.QueryValueEx(key, SystemRestart.APP_NAME)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
                
        except Exception:
            return False
    
    @staticmethod
    def restart_windows(countdown_seconds=10):
        """
        Startet Windows neu nach Countdown
        
        Args:
            countdown_seconds: Sekunden bis zum Neustart (0 = sofort)
        
        Returns:
            bool: True wenn Neustart initiiert wurde
        """
        try:
            # Auto-Restart einrichten BEVOR Neustart
            if not SystemRestart.setup_auto_restart():
                logger.warning("Auto-Restart konnte nicht eingerichtet werden")
                # Trotzdem fortfahren mit Neustart
            
            # Windows Neustart mit shutdown Kommando
            # /r = Restart, /t = Time in Sekunden, /c = Comment
            cmd = [
                "shutdown",
                "/r",
                "/t", str(countdown_seconds),
                "/c", "Registry Manager Neustart - Programm wird automatisch wieder geöffnet"
            ]
            
            logger.info(f"Starte Windows-Neustart in {countdown_seconds} Sekunden")
            subprocess.run(cmd, check=True)
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Fehler beim Ausführen von shutdown: {e}")
            return False
        except Exception as e:
            logger.error(f"Fehler beim Windows-Neustart: {e}")
            return False
    
    @staticmethod
    def cancel_restart():
        """
        Bricht geplanten Windows-Neustart ab
        """
        try:
            # shutdown /a = Abort
            subprocess.run(["shutdown", "/a"], check=True)
            
            # Auto-Restart Eintrag entfernen
            SystemRestart.remove_auto_restart()
            
            logger.info("Windows-Neustart abgebrochen")
            return True
            
        except subprocess.CalledProcessError:
            # Kein Neustart geplant - kein Fehler
            logger.info("Kein Neustart zum Abbrechen vorhanden")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Abbrechen des Neustarts: {e}")
            return False
    
    @staticmethod
    def restart_explorer():
        """
        Startet nur Windows Explorer neu (für Kontextmenü-Änderungen etc.)
        Kein kompletter System-Neustart nötig
        """
        try:
            logger.info("Starte Windows Explorer neu...")
            
            # Explorer beenden
            subprocess.run(["taskkill", "/F", "/IM", "explorer.exe"], 
                         capture_output=True, check=False)
            
            # Kurz warten
            import time
            time.sleep(1)
            
            # Explorer neu starten
            subprocess.Popen("explorer.exe")
            
            logger.info("Windows Explorer erfolgreich neugestartet")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Explorer-Neustart: {e}")
            return False
