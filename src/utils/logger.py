"""
Logger Setup
===========

Konfiguration des Logging-Systems für den Registry Manager.
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime


def setup_logging(log_level: str = "INFO", log_to_file: bool = True, 
                 log_to_console: bool = True) -> None:
    """
    Logging-System einrichten
    
    Args:
        log_level: Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: In Datei loggen
        log_to_console: In Konsole loggen
    """
    
    # Log-Level konvertieren
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Root-Logger konfigurieren
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Bestehende Handler entfernen
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Formatter erstellen
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # Console-Handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
    
    # File-Handler
    if log_to_file:
        try:
            # Log-Verzeichnis erstellen - funktioniert für Skript und EXE
            import sys
            if getattr(sys, 'frozen', False):
                # Running as compiled EXE
                base_path = Path(sys.executable).parent
            else:
                # Running as script
                base_path = Path(__file__).parent.parent.parent
            
            log_dir = base_path / "logs"
            log_dir.mkdir(exist_ok=True)
            
            # Log-Datei mit Datum
            log_filename = f"registry_manager_{datetime.now().strftime('%Y%m%d')}.log"
            log_path = log_dir / log_filename
            
            # Rotating File Handler (max 10MB, 5 Backups)
            file_handler = logging.handlers.RotatingFileHandler(
                log_path, 
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(file_handler)
            
            # Info-Nachricht
            logging.info(f"Logging eingerichtet - Log-Datei: {log_path}")
            
        except Exception as e:
            # Fallback: nur Console-Logging
            logging.error(f"Fehler beim Einrichten des File-Handlers: {e}")


def get_logger(name: str) -> logging.Logger:
    """
    Logger für ein bestimmtes Modul abrufen
    
    Args:
        name: Name des Moduls (normalerweise __name__)
        
    Returns:
        Konfigurierter Logger
    """
    return logging.getLogger(name)


def log_exception(logger: logging.Logger, message: str = "Unerwarteter Fehler"):
    """
    Exception mit Stack-Trace loggen
    
    Args:
        logger: Logger-Instanz
        message: Zusätzliche Fehlermeldung
    """
    logger.exception(f"{message}:")


def set_log_level(level: str):
    """
    Log-Level zur Laufzeit ändern
    
    Args:
        level: Neuer Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    try:
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)
        
        # Alle Handler aktualisieren
        for handler in root_logger.handlers:
            handler.setLevel(numeric_level)
            
        logging.info(f"Log-Level geändert auf: {level.upper()}")
        
    except Exception as e:
        logging.error(f"Fehler beim Ändern des Log-Levels: {e}")


def cleanup_old_logs(days: int = 30):
    """
    Alte Log-Dateien aufräumen
    
    Args:
        days: Alter in Tagen, ab dem Dateien gelöscht werden
    """
    try:
        log_dir = Path(__file__).parent.parent.parent / "logs"
        
        if not log_dir.exists():
            return
        
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        deleted_count = 0
        for log_file in log_dir.glob("registry_manager_*.log*"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                log_file.unlink()
                deleted_count += 1
        
        if deleted_count > 0:
            logging.info(f"{deleted_count} alte Log-Dateien gelöscht")
            
    except Exception as e:
        logging.error(f"Fehler beim Aufräumen der Log-Dateien: {e}")


class RegistryManagerLogger:
    """
    Spezieller Logger für Registry Manager mit zusätzlichen Funktionen
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._operation_stack = []
    
    def start_operation(self, operation: str):
        """
        Neue Operation starten (für verschachtelte Operationen)
        
        Args:
            operation: Name der Operation
        """
        self._operation_stack.append(operation)
        self.logger.info(f"START: {operation}")
    
    def end_operation(self, success: bool = True, message: str = ""):
        """
        Operation beenden
        
        Args:
            success: Erfolg der Operation
            message: Zusätzliche Nachricht
        """
        if not self._operation_stack:
            return
        
        operation = self._operation_stack.pop()
        status = "SUCCESS" if success else "FAILED"
        log_message = f"END: {operation} - {status}"
        
        if message:
            log_message += f" - {message}"
        
        if success:
            self.logger.info(log_message)
        else:
            self.logger.error(log_message)
    
    def log_registry_access(self, key_path: str, action: str, success: bool = True):
        """
        Registry-Zugriff loggen
        
        Args:
            key_path: Registry-Key-Pfad
            action: Aktion (READ, WRITE, DELETE, etc.)
            success: Erfolg der Aktion
        """
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"REGISTRY {action} {status}: {key_path}")
    
    def log_file_operation(self, filepath: str, action: str, success: bool = True):
        """
        Datei-Operation loggen
        
        Args:
            filepath: Dateipfad
            action: Aktion (READ, WRITE, DELETE, etc.)
            success: Erfolg der Aktion
        """
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"FILE {action} {status}: {filepath}")
    
    def debug(self, message: str):
        """Debug-Nachricht"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Info-Nachricht"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Warning-Nachricht"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Error-Nachricht"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Critical-Nachricht"""
        self.logger.critical(message)
    
    def exception(self, message: str):
        """Exception mit Stack-Trace"""
        self.logger.exception(message)