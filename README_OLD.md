# Registry File Manager

Ein umfassendes Tool zur Verwaltung von Windows Registry-Files (.reg) mit grafischer Benutzeroberfläche.

## 🚀 Funktionen

### Kernfunktionen
- **Registry-File-Erstellung**: Einfache Erstellung neuer .reg-Dateien mit intuitivem Editor
- **Sammlung & Organisation**: Zentrale Verwaltung aller Registry-Files mit Kategorisierung
- **Dokumentation**: Detaillierte Beschreibung und Metadaten für jede Datei
- **Status-Überprüfung**: Überprüfung ob Registry-Einträge tatsächlich aktiv sind
- **Import/Export**: Backup und Wiederherstellung von Registry-Sammlungen

### Erweiterte Features
- **Vorlagen-System**: Vordefinierte Templates für häufige Registry-Tweaks
- **Status-Monitoring**: Visueller Vergleich zwischen .reg-Dateien und aktueller Registry
- **Sicherheitsprüfung**: Warnungen vor potentiell gefährlichen Registry-Änderungen
- **Batch-Operationen**: Mehrere Registry-Files gleichzeitig verarbeiten
- **Such- und Filterfunktionen**: Schnelles Finden bestimmter Registry-Einträge

## 📋 Systemanforderungen

- **Betriebssystem**: Windows 10/11 (Registry-spezifisch)
- **Python**: Version 3.8 oder höher
- **GUI-Framework**: tkinter (standardmäßig in Python enthalten)
- **Berechtigung**: Administrator-Rechte für Registry-Zugriff empfohlen

## 🛠️ Installation

### 1. Repository klonen oder herunterladen
```bash
git clone <repository-url>
cd "Reg Organizer TG"
```

### 2. Python-Abhängigkeiten
Das Projekt nutzt ausschließlich Python-Standard-Bibliotheken:
- `tkinter` - GUI-Framework
- `winreg` - Windows Registry-Zugriff
- `json` - Datenbank/Konfiguration
- `logging` - Protokollierung
- `pathlib` - Dateisystem-Operationen

### 3. Anwendung starten
```bash
python main.py
```

## 📖 Verwendung

### Registry-File erstellen
1. **Datei → Neue REG-Datei erstellen** oder Toolbar-Button "Neue REG-Datei"
2. Datei-Informationen eingeben (Name, Titel, Beschreibung)
3. Registry-Einträge hinzufügen:
   - Registry-Key-Pfad angeben
   - Wert-Name und -Typ auswählen
   - Wert-Daten eingeben
4. Vorschau prüfen und speichern

### Status prüfen
1. Registry-File aus der Sammlung auswählen
2. **Registry → Status prüfen** oder Toolbar-Button "Status prüfen"
3. Ergebnisse im **Status-Tab** ansehen:
   - ✅ Grün: Werte stimmen überein
   - ⚠️ Orange: Werte sind unterschiedlich  
   - ❌ Rot: Werte/Keys fehlen

### Sammlung verwalten
- **Import**: Bestehende .reg-Dateien in die Sammlung importieren
- **Export**: Komplette Sammlung mit Dokumentation exportieren
- **Dokumentation**: Titel, Kategorie und Beschreibung für jede Datei
- **Suche**: Nach Dateinamen, Beschreibung oder Kategorien filtern

## 🗂️ Projektstruktur

```
Reg Organizer TG/
├── main.py                 # Hauptanwendung
├── src/                    # Quellcode
│   ├── gui/               # GUI-Module
│   │   ├── main_window.py # Hauptfenster
│   │   ├── reg_editor.py  # Registry-Editor
│   │   └── status_display.py # Status-Anzeige
│   ├── registry/          # Registry-Operationen
│   │   ├── reg_creator.py # .reg-Datei-Erstellung
│   │   ├── reg_parser.py  # .reg-Datei-Parser
│   │   └── status_checker.py # Status-Überprüfung
│   ├── database/          # Datenbank/Storage
│   │   └── registry_db.py # JSON-basierte Datenbank
│   └── utils/             # Hilfsfunktionen
│       └── logger.py      # Logging-System
├── reg_files/             # Gesammelte .reg-Dateien
├── config/                # Konfigurationsdateien
├── docs/                  # Dokumentation
├── logs/                  # Log-Dateien
└── README.md             # Diese Datei
```

## 🔧 Konfiguration

### Log-Level anpassen
In `src/utils/logger.py` können Log-Einstellungen angepasst werden:
```python
setup_logging(
    log_level="INFO",      # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_to_file=True,      # In Datei loggen
    log_to_console=True    # In Konsole loggen
)
```

### Vorlagen erweitern
Neue Registry-Vorlagen in `src/registry/reg_creator.py` hinzufügen:
```python
templates = {
    'meine_vorlage': {
        'keys': {
            'HKEY_CURRENT_USER\\Software\\MeinKey': {
                'values': {
                    'MeinWert': {'type': 'REG_DWORD', 'data': 1}
                }
            }
        }
    }
}
```

## ⚠️ Sicherheitshinweise

### Registry-Manipulation
- **Backup erstellen**: Immer vor größeren Änderungen ein Registry-Backup erstellen
- **Administrator-Rechte**: Für Systemeinstellungen erforderlich
- **Vorsicht bei HKLM**: Besondere Vorsicht bei HKEY_LOCAL_MACHINE Änderungen
- **Testen**: Änderungen erst in einer VM oder Testumgebung testen

### Empfohlener Workflow
1. Registry-Backup erstellen (`Registry → Backup erstellen`)
2. .reg-Datei mit Tool erstellen und prüfen
3. Status vor Anwendung überprüfen
4. .reg-Datei anwenden
5. Funktionalität testen
6. Bei Problemen: Backup wiederherstellen

## 🐛 Problembehandlung

### Häufige Probleme

**Fehler: "Import konnte nicht aufgelöst werden"**
- Lösung: Python-Pfad prüfen, Anwendung aus Hauptverzeichnis starten

**Registry-Zugriff verweigert**
- Lösung: Als Administrator ausführen, Benutzerrechte prüfen

**Datei kann nicht gespeichert werden**
- Lösung: Schreibrechte für Zielverzeichnis prüfen

**Status-Prüfung schlägt fehl**
- Lösung: Registry-Key-Pfad validieren, Berechtigung prüfen

### Log-Dateien
Detaillierte Fehlermeldungen finden sich in:
- `logs/registry_manager_YYYYMMDD.log`

### Debug-Modus
Für detaillierte Logs Debug-Modus aktivieren:
```python
setup_logging(log_level="DEBUG")
```

## 📝 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe LICENSE-Datei für Details.

## 🤝 Beitragen

Beiträge sind willkommen! Bitte:
1. Fork des Repositories erstellen
2. Feature-Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Änderungen committen (`git commit -m 'Add some AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request öffnen

## 📧 Support

Bei Fragen oder Problemen:
- Issue im Repository erstellen
- Log-Dateien mit Fehlerbeschreibung bereitstellen
- Systemkonfiguration angeben (Windows-Version, Python-Version)

## 🎯 Roadmap

### Geplante Features
- [ ] Registry-Diff-Tool (Vergleich zweier Registry-Zustände)
- [ ] Automatische Backup-Erstellung vor .reg-Anwendung
- [ ] Registry-Key-Browser mit Suche
- [ ] Export in verschiedene Formate (XML, CSV)
- [ ] Kommandozeilen-Interface
- [ ] Plugin-System für Erweiterungen
- [ ] Registry-Monitoring (Änderungen in Echtzeit)
- [ ] Mehrsprachigkeit (English, Deutsch)

### Verbesserungen
- [ ] Performance-Optimierung für große Registry-Files
- [ ] Erweiterte Such- und Filterfunktionen
- [ ] Bessere Integration mit Windows-Explorer
- [ ] Erweiterte Vorlagen-Verwaltung
- [ ] Import/Export für andere Registry-Tools

---

**Registry File Manager v1.0** - Ein Tool von Registry-Enthusiasten für Registry-Enthusiasten! 🚀# Registry-Manager-by-TechnikGolem
