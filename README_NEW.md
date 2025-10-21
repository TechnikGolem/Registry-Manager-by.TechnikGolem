# 🗂️ Registry File Manager v1.0

**Portable Windows Registry Manager mit SQLite-Datenbank, Gruppen-Management und Auto-Restart**

Ein professionelles Tool zur Verwaltung, Organisation und Anwendung von Windows Registry-Files (.reg) mit moderner GUI.

![Windows](https://img.shields.io/badge/Windows-10%2F11-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Hauptfeatures

### 📦 **Portable App**
- ✅ Komplette Anwendung in einer EXE-Datei
- ✅ Embedded Registry-Files in SQLite-Datenbank
- ✅ Keine Installation erforderlich
- ✅ Alle Daten in einer portablen Datei

### 🗂️ **Gruppen-Management**
- ✅ REG-Dateien in Gruppen organisieren
- ✅ Custom Icons (📁📂🗂️📋⭐🎯🔧⚙️🎨🚀)
- ✅ Gruppenwechsel (automatisch aus alter Gruppe entfernt)
- ✅ "Ohne Gruppe" für nicht-gruppierte REGs

### 🎯 **Registry-Operationen**
- ✅ **Erstellen** - Neue REG-Dateien mit GUI
- ✅ **Einbetten** - In Datenbank speichern
- ✅ **Aktivieren** - Registry-Änderungen anwenden
- ✅ **Deaktivieren** - Echtes Löschen mit `[-KEY]` Syntax
- ✅ **Status prüfen** - Erkennt aktive/inaktive Einträge
- ✅ **Löschen** - Aus Sammlung oder von Festplatte

### 🔄 **Neustart-Funktionen**
- ✅ **Explorer neu starten** - Für Kontextmenü-Updates
- ✅ **Windows neu starten** - Mit Auto-Wiederstart
  - RunOnce Registry-Eintrag
  - App öffnet sich automatisch nach Neustart
  - Zeigt aktualisierten Status

### 🛡️ **Sicherheit**
- ✅ Automatische Backups vor Registry-Änderungen
- ✅ Bestätigungs-Dialoge
- ✅ Detailliertes Logging
- ✅ Wiederherstellungs-Funktionen

## 🚀 Installation

### Als EXE (Empfohlen)
1. Download `RegistryManager.exe` aus Releases
2. Starte die EXE - fertig!
3. Alle Daten in `registry_manager.db`

### Aus Source
```bash
git clone https://github.com/DEIN-USERNAME/registry-file-manager.git
cd registry-file-manager
python -m venv .venv
.venv\Scripts\activate
pip install pyinstaller
python main.py
```

### EXE selbst erstellen
```bash
python build_exe.py
# EXE: dist/RegistryManager.exe
```

## 📋 Verwendung

### 1. REG einbetten
```
Klick "REG einbetten" → Datei wählen → In Datenbank gespeichert!
Original bleibt erhalten
```

### 2. Gruppe erstellen
```
Klick "📁 Gruppe erstellen" → Name + Icon → Fertig
Rechtsklick auf REG → "Gruppen" → Gruppe wählen
```

### 3. Registry anwenden
```
REG auswählen → Rechtsklick → "🟢 Aktivieren"
Automatisches Backup → Registry-Änderung → Fertig!
```

### 4. Nach Änderung neu starten
```
🔄 Explorer neu starten - Für Kontextmenüs
🔄 PC neu starten - Mit Auto-Wiederstart der App!
```

## 🗄️ Technologie

- **GUI**: tkinter
- **Datenbank**: SQLite3
- **Registry**: winreg (Windows API)
- **Build**: PyInstaller
- **Encoding**: UTF-8-sig, UTF-16, CP1252, Latin1

## 📁 Projektstruktur

```
registry-file-manager/
├── main.py                      # Einstiegspunkt
├── build_exe.py                 # EXE-Builder
├── src/
│   ├── gui/                     # GUI-Module
│   │   ├── main_window.py       # Hauptfenster
│   │   ├── reg_editor.py        # REG-Editor
│   │   └── settings_window.py   # Einstellungen
│   ├── registry/                # Registry-Ops
│   │   ├── reg_parser.py        # Parser
│   │   ├── reg_creator.py       # Creator
│   │   └── status_checker.py    # Status
│   ├── database/                # Datenbank
│   │   └── sqlite_db.py         # SQLite DB
│   └── utils/                   # Tools
│       ├── system_restart.py    # Neustart
│       ├── backup_manager.py    # Backups
│       └── content_analyzer.py  # Analyse
└── registry_manager.db          # SQLite DB
```

## ⚙️ Datenbank-Schema

```sql
-- Embedded REGs
CREATE TABLE embedded_regs (
    id TEXT PRIMARY KEY,
    name TEXT,
    content TEXT,
    status TEXT,
    category TEXT,
    -- ...
);

-- Gruppen
CREATE TABLE groups (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE,
    icon TEXT,
    -- ...
);

-- Zuordnung (n:m)
CREATE TABLE reg_groups (
    reg_id TEXT,
    group_id TEXT,
    PRIMARY KEY (reg_id, group_id)
);
```

## ⚠️ Wichtig

- **Admin-Rechte** für Registry-Zugriff nötig
- **Backups** werden automatisch erstellt
- **Deaktivieren** löscht Keys mit `[-HKEY_...]`
- **Embedded REGs** bleiben in DB auch wenn Original weg

## 🐛 Bekannte Limits

- Nur Windows
- Admin-Rechte erforderlich
- DB wächst mit Anzahl REGs

## 📜 Lizenz

MIT License

## 🤝 Mitwirken

PRs willkommen!

1. Fork
2. Feature Branch
3. Commit
4. Push
5. Pull Request

---

**Mit ❤️ entwickelt für effizientes Registry-Management**
