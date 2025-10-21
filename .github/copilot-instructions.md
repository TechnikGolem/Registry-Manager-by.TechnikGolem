# Registry File Manager - Copilot Instructions

Dieses Projekt ist ein Python-basiertes Registry-File-Management-System mit GUI.

## Projekt-Übersicht
- **Hauptziel**: Verwaltung von Windows Registry-Files (.reg)
- **Funktionen**: Erstellen, Sammeln, Dokumentieren und Status-Überprüfung
- **Technologie**: Python mit tkinter GUI
- **Zielgruppe**: Windows-Systemadministratoren und Power-User

## Kernfunktionen
1. **Registry-File-Erstellung**: Einfache Erstellung neuer .reg-Files
2. **Sammlung & Organisation**: Zentrale Verwaltung aller Registry-Files
3. **Dokumentation**: Beschreibung und Kategorisierung jeder Datei
4. **Status-Überprüfung**: Überprüfung ob Registry-Einträge aktiv sind
5. **Import/Export**: Backup und Wiederherstellung von Registry-Sammlungen

## Technische Spezifikationen
- **Sprache**: Python 3.8+
- **GUI-Framework**: tkinter (Standard-Python-Bibliothek)
- **Registry-Zugriff**: winreg Modul
- **Dateiformate**: .reg, .json (für Metadaten)
- **Betriebssystem**: Windows (Registry-spezifisch)

## Projektstruktur
```
/registry_manager/
├── src/
│   ├── gui/                 # GUI-Module
│   ├── registry/            # Registry-Operationen
│   ├── database/            # Datenbank/Storage
│   └── utils/               # Hilfsfunktionen
├── reg_files/               # Gesammelte .reg-Files
├── docs/                    # Dokumentation
├── tests/                   # Unit-Tests
└── config/                  # Konfigurationsdateien
```

## Entwicklungsrichtlinien
- Verwende aussagekräftige deutsche Kommentare
- Implementiere umfangreiche Fehlerbehandlung
- Berücksichtige Windows-Registry-Sicherheit
- Erstelle Backups vor Registry-Änderungen
- Verwende logging für Debugging