# Modbus Tools

**Languages:** [English](#english) | [Deutsch](#deutsch)

---

<a id="english"></a>
## Overview (English)

*([Zum deutschen Abschnitt springen](#deutsch))*

This project contains Modbus client tools, a Modbus server with GUI, and a few helper/test scripts.

### 1. Modbus Client (GUI) (`client_gui.py`)
- Graphical user interface (GUI) for querying Modbus TCP servers
- Allows reading holding and input registers
- Configurable Modbus port (default: 5020)
- Pre-filled values for host IP, register, and register type (all editable)
- Displays the server response in a dialog window

### 2. Modbus Client (CLI) (`client_cli.py`)
- Command-line tool for automated Modbus TCP queries
- Reads predefined register groups (e.g., temperature, solar) and applies scaling automatically
- Extensive logging (INFO/ERROR) for debugging and development
- Example usage: `python client_cli.py`
- Ideal for automated tests and quick register value checks
- Register addresses and scaling factors can be adjusted in the code

### 3. Modbus Register Scanner (`modbus_scanner.py`)
- GUI tool for scanning an address range on a Modbus TCP server
- Scans holding or input registers over a configurable start/stop range
- Exports results as CSV, and as a formatted Excel file if `openpyxl` is installed
- Runs the scan in a background thread so the GUI stays responsive
- Useful for exploring unknown/new Modbus devices (or the simulator)

### 4. Modbus Server with GUI (`GuiServer/`)
- Simulates a Modbus TCP server for Lambda heat pumps (1 or 2 heat pumps)
- Full graphical control over all Modbus registers
- Runs on port 5020
- Replaces the former CLI-only server that used to live at the project root (`server.py`), which has been removed

#### Key features of the GUI version:

**Register configuration:**
- All state registers adjustable via dropdown menus
- Mapping texts from `GuiServer/const_mapping.py` (e.g. "Heating", "Cooling", "Ready")
- Persistent storage in `GuiServer/server_state.json`
- All changes take effect without restarting the server

**Heat pump mode:**
- Switch between 1 and 2 heat pumps
- In 2-HP mode: all registers for HP2 are shown
- In 1-HP mode: HP2 registers are hidden
- The server automatically filters only the relevant registers based on the mode
- The mode switch is locked while the server is running (prevents inconsistent register sets)

**Simulation modes:**
- Configurable operating mode (heating, hot water, cooling, defrost) via `MODE_CASCADE` in `const_mapping.py`
- Switching the mode automatically sets the associated HP, HC, boiler, and buffer registers of all active heat pumps
- Configurable word order (high-word-first / low-word-first) for 32-bit registers

**Auto-increment:**
- Accumulator registers (power consumption, thermal energy) increase every 10 seconds
- Can be switched on and off via the "Energie-Akkumulation (alle 10s)" checkbox
- The increment per interval is editable in the GUI, separately for electrical (registers 1020/1120) and thermal (1022/1122) energy
- Defaults: 10 (electrical) and 40 (thermal); edits take effect immediately with the next interval, no server restart required
- Invalid input (empty, non-numeric, negative) marks the field red and keeps the previous value active
- Works for HP1 and (if enabled) HP2
- Values and the configured increments are persisted (`electrical_increment` / `thermal_increment` in `server_state.json`)

**Live logging:**
- Displays all Modbus read/write operations
- Filter options: "All", "Write only", "Read only"
- Shows written values including mapping texts
- Scrollbar for long log history

**Modbus error responses:**
- Returns correct Modbus exceptions for invalid registers
- Prevents false autodetect results in the Lambda integration
- Returns Exception Code 2 (Illegal Data Address) for non-existent registers

**Three-column layout:**
- Column 1: HP1 + shared components (ambient, solar, boiler 1, buffer 1, HC 1, E-manager)
- Column 2: HP2 components (boiler 2, buffer 2, HC 2) - hidden in 1-HP mode
- Column 3: HP mode switch, operating mode, accumulator settings (on/off plus the electrical and thermal increment fields), 32-bit word order, and log filter
- Bottom: log output spanning the full width

#### Using the GUI version:

```bash
cd GuiServer
python GuiServer.py
```

**Startup behavior:**
1. GUI opens with the server stopped
2. Select 1-HP or 2-HP mode
3. Configure registers via dropdown menus
4. Click "Start Server"
5. Modbus server runs on port 5020 with slave ID 1
6. All changes are applied immediately
7. Accumulators increase automatically every 10 seconds by the increments configured in column 3

**Persistence:**
- All configuration is stored in `GuiServer/server_state.json`
- The last values are loaded on restart
- Accumulator values continue from where they left off

**Integration with Lambda Home Assistant:**
- Server runs with slave ID 1 (Lambda expects unit ID 1)
- Returns correct Modbus error responses for invalid registers
- Supports all Lambda registers from `registers.yaml`
- Automatically filters only relevant registers based on 1/2-HP mode
- Fully compatible with the Lambda Home Assistant integration

### 5. Test scripts (project root, `test_*.py`)
Small standalone scripts for manually testing the running GUI server (`GuiServer/GuiServer.py`) via a `pymodbus` client against `localhost:5020`. No test framework (e.g. `pytest`) — just run `python <file>.py` directly while the server is running.

- `test_connection.py` – simple connection test, reads register 1000
- `test_batch.py` – batch read across a range with valid/invalid registers
- `test_exception.py` – checks that an invalid register address (9999) correctly returns a Modbus exception
- `test_uint32.py` – checks correct big-endian encoding of 32-bit registers (e.g. register 1020)
- `test_accumulator.py` – checks that accumulator registers auto-increment as expected
- `test_real_lambda.py` – connection test against a real Lambda device (not the simulator), adjust the address in the script

### Other files in the project root

- `const_mapping.py` – outdated copy of the mapping texts from `GuiServer/const_mapping.py`. Not imported by any script in the project root, kept only as legacy leftover.
- `registers.yaml` – register configuration; used as a reference in the root, while `GuiServer/registers.yaml` is the authoritative copy.
- `server_state.json` – outdated state leftover from the removed root `server.py`; the file actually in use is `GuiServer/server_state.json`.

### Installation

#### Dependencies

```bash
pip install pymodbus pyyaml tkinter
```

The Excel export in `modbus_scanner.py` additionally requires `openpyxl` (optional, see `requirements.txt`).

#### Directory structure

```
modbus_tools/
├── registers.yaml               # Register configuration (reference)
├── const_mapping.py             # Outdated copy, unused (see above)
├── client_gui.py                # GUI Modbus client
├── client_cli.py                # CLI Modbus client
├── modbus_scanner.py            # Register scanner with CSV/Excel export
├── test_connection.py           # Test script: connection
├── test_batch.py                # Test script: batch read
├── test_exception.py            # Test script: Modbus exceptions
├── test_uint32.py               # Test script: 32-bit registers
├── test_accumulator.py          # Test script: accumulator registers
├── test_real_lambda.py          # Test script: real Lambda device
└── GuiServer/                   # GUI server with extended features
    ├── GuiServer.py              # Main GUI application
    ├── server_threaded.py       # Threaded Modbus server
    ├── register_manager.py      # State management
    ├── server_state.json        # Persistent configuration (auto-generated)
    ├── registers.yaml           # Register configuration
    └── const_mapping.py         # Mapping texts
```

---

<a id="deutsch"></a>
## Übersicht (Deutsch)

*([Jump to the English section](#english))*

Dieses Projekt enthält Modbus-Client-Werkzeuge, einen Modbus-Server mit GUI sowie einige Hilfs- und Testskripte.

### 1. Modbus Client (GUI) (`client_gui.py`)
- Grafische Benutzeroberfläche (GUI) zur Abfrage von Modbus TCP Servern
- Ermöglicht das Auslesen von Holding- und Input-Register
- Konfigurierbarer Modbus Port (Standard: 5020)
- Voreingestellte Werte für Host-IP, Register und Registertyp, aber frei änderbar
- Zeigt die Antwort des Servers in einem Dialogfenster an

### 2. Modbus Client (Kommandozeile) (`client_cli.py`)
- Kommandozeilen-Tool für automatisierte Modbus TCP Abfragen
- Liest vordefinierte Registergruppen (z.B. Temperatur, Solar) und skaliert Werte automatisch
- Umfangreiches Logging (INFO/ERROR) für Debugging und Entwicklung
- Beispielaufruf: `python client_cli.py`
- Ideal für automatisierte Tests und zur schnellen Überprüfung von Registerwerten
- Registeradressen und Skalierungsfaktoren sind im Code anpassbar

### 3. Modbus Register Scanner (`modbus_scanner.py`)
- Grafisches Tool zum Scannen eines Adressbereichs eines Modbus TCP Servers
- Durchsucht wahlweise Holding- oder Input-Register über einen konfigurierbaren Start-/Stop-Bereich
- Exportiert die Ergebnisse als CSV, bei installiertem `openpyxl` zusätzlich als formatierte Excel-Datei
- Läuft als eigenständiger Scan in einem Hintergrund-Thread, damit die GUI währenddessen reagibel bleibt
- Nützlich, um unbekannte oder neue Modbus-Geräte (bzw. den Simulator) initial zu erkunden

### 4. Modbus Server mit GUI (`GuiServer/`)
- Simuliert einen Modbus-TCP-Server für Lambda Wärmepumpen (1 oder 2 Wärmepumpen)
- Grafische Oberfläche mit vollständiger Kontrolle über alle Modbus-Register
- Läuft auf Port 5020
- Ersetzt den früheren, rein Kommandozeilen-basierten Server im Projekt-Root (`server.py`), der aus dem Projekt entfernt wurde

#### Hauptfeatures der GUI-Version:

**Register-Konfiguration:**
- Alle State-Register über Dropdown-Menüs anpassbar
- Mapping-Texte aus `GuiServer/const_mapping.py` (z.B. "Heating", "Cooling", "Ready")
- Persistente Speicherung in `GuiServer/server_state.json`
- Alle Änderungen werden ohne Server-Neustart übernommen

**Wärmepumpen-Modus:**
- Umschaltung zwischen 1 und 2 Wärmepumpen
- Bei 2-WP-Modus: Alle Register für WP2 werden angezeigt
- Bei 1-WP-Modus: WP2-Register werden ausgeblendet
- Server filtert automatisch nur relevante Register basierend auf Modus
- Die Modus-Umschaltung ist gesperrt, solange der Server läuft (verhindert inkonsistente Registersätze)

**Simulationsmodi:**
- Konfigurierbare Betriebsart (Heizen, Warmwasser, Kühlen, Abtauen) über `MODE_CASCADE` in `const_mapping.py`
- Setzt beim Wechsel automatisch die zugehörigen HP-, HC-, Boiler- und Buffer-Register aller aktiven Wärmepumpen
- Konfigurierbare Wortreihenfolge (High-Word-first / Low-Word-first) für 32-Bit-Register

**Auto-Inkrementierung:**
- Akkumulator-Register (Power Consumption, Thermal Energy) erhöhen sich alle 10 Sekunden
- Über die Checkbox "Energie-Akkumulation (alle 10s)" ein- und ausschaltbar
- Das Inkrement pro Intervall ist in der GUI editierbar, getrennt für elektrische (Register 1020/1120) und thermische Energie (1022/1122)
- Standardwerte: 10 (elektrisch) und 40 (thermisch); Änderungen wirken sofort ab dem nächsten Intervall, ohne Server-Neustart
- Ungültige Eingaben (leer, nicht numerisch, negativ) färben das Feld rot, der bisherige Wert bleibt aktiv
- Funktioniert für WP1 und (bei aktiviert) WP2
- Werte und eingestellte Inkremente werden persistent gespeichert (`electrical_increment` / `thermal_increment` in `server_state.json`)

**Live-Logging:**
- Anzeige aller Modbus Read/Write-Operationen
- Filterfunktion: "Alle", "Nur Write", "Nur Read"
- Zeigt geschriebene Werte inkl. Mapping-Texten
- Scrollbar für langen Log-Verlauf

**Modbus-Fehlermeldungen:**
- Gibt korrekte Modbus-Exceptions für ungültige Register zurück
- Verhindert fälschliche Autodetect-Ergebnisse bei Lambda-Integration
- Ausgabe von Exception Code 2 (Illegal Data Address) für nicht vorhandene Register

**Dreispaltiges Layout:**
- Spalte 1: WP1 + gemeinsame Komponenten (Ambient, Solar, Boiler 1, Buffer 1, HC 1, E-Manager)
- Spalte 2: WP2-Komponenten (Boiler 2, Buffer 2, HC 2) - ausgeblendet bei 1-WP-Modus
- Spalte 3: WP-Modus-Schalter, Betriebsart, Akkumulator-Einstellungen (An/Aus sowie die Eingabefelder für elektrisches und thermisches Inkrement), 32-Bit-Wortreihenfolge und Log-Filter
- Unten: Log-Ausgabe über volle Breite

#### Verwendung der GUI-Version:

```bash
cd GuiServer
python GuiServer.py
```

**Startup-Verhalten:**
1. GUI öffnet sich mit Server-Stop-Button
2. Wählen Sie 1-WP oder 2-WP Modus
3. Konfigurieren Sie Register über Dropdown-Menüs
4. Klicken Sie "Start Server"
5. Modbus-Server läuft auf Port 5020 mit Slave ID 1
6. Alle Änderungen werden sofort übernommen
7. Akkumulatoren erhöhen sich automatisch alle 10 Sekunden um die in Spalte 3 eingestellten Inkremente

**Speicherung:**
- Alle Konfigurationen werden in `GuiServer/server_state.json` gespeichert
- Bei Neustart werden die letzten Werte geladen
- Akkumulator-Werte werden fortgesetzt

**Integration mit Lambda Home Assistant:**
- Server läuft mit Slave ID 1 (Lambda erwartet Unit ID 1)
- Gibt korrekte Modbus-Fehlermeldungen für ungültige Register zurück
- Unterstützt alle Lambda-Register aus `registers.yaml`
- Filtert automatisch nur relevante Register basierend auf 1/2-WP-Modus
- Vollständig kompatibel mit der Lambda Home Assistant Integration

### 5. Testskripte (Projekt-Root, `test_*.py`)
Kleine, eigenständige Skripte zum manuellen Testen des laufenden GUI-Servers (`GuiServer/GuiServer.py`) via `pymodbus`-Client gegen `localhost:5020`. Kein Test-Framework (z.B. `pytest`), einfach direkt mit `python <datei>.py` ausführbar, während der Server läuft.

- `test_connection.py` – einfacher Verbindungstest, liest Register 1000
- `test_batch.py` – Batch-Lesezugriff über einen Bereich mit gültigen/ungültigen Registern
- `test_exception.py` – prüft, ob eine ungültige Register-Adresse (9999) korrekt eine Modbus-Exception liefert
- `test_uint32.py` – prüft das korrekte Big-Endian-Encoding von 32-Bit-Registern (z.B. Register 1020)
- `test_accumulator.py` – prüft, ob sich Akkumulator-Register wie erwartet automatisch erhöhen
- `test_real_lambda.py` – Verbindungstest gegen ein echtes Lambda-Gerät (nicht den Simulator), Adresse im Skript anpassen

### Sonstige Dateien im Projekt-Root

- `const_mapping.py` – veraltete Kopie der Mapping-Texte aus `GuiServer/const_mapping.py`. Wird von keinem Skript im Projekt-Root importiert und ist nur als Altlast vorhanden.
- `registers.yaml` – Register-Konfiguration; wird sowohl als Referenz im Root als auch (maßgeblich) von `GuiServer/registers.yaml` verwendet.
- `server_state.json` – veralteter State-Rest des entfernten Root-`server.py`; die aktuell genutzte Datei liegt unter `GuiServer/server_state.json`.

### Installation

#### Abhängigkeiten

```bash
pip install pymodbus pyyaml tkinter
```

Für den Excel-Export in `modbus_scanner.py` wird zusätzlich `openpyxl` benötigt (optional, siehe `requirements.txt`).

#### Verzeichnisstruktur

```
modbus_tools/
├── registers.yaml               # Register-Konfiguration (Referenz)
├── const_mapping.py             # Veraltete Kopie, ungenutzt (siehe oben)
├── client_gui.py                # GUI Modbus Client
├── client_cli.py                # CLI Modbus Client
├── modbus_scanner.py            # Register-Scanner mit CSV/Excel-Export
├── test_connection.py           # Testskript: Verbindung
├── test_batch.py                # Testskript: Batch-Lesezugriff
├── test_exception.py            # Testskript: Modbus-Exceptions
├── test_uint32.py               # Testskript: 32-Bit-Register
├── test_accumulator.py          # Testskript: Akkumulator-Register
├── test_real_lambda.py          # Testskript: echtes Lambda-Gerät
└── GuiServer/                   # GUI Server mit erweiterten Features
    ├── GuiServer.py              # Haupt-GUI-Anwendung
    ├── server_threaded.py       # Threaded Modbus Server
    ├── register_manager.py      # State-Management
    ├── server_state.json        # Persistente Konfiguration (auto-generiert)
    ├── registers.yaml           # Register-Konfiguration
    └── const_mapping.py         # Mapping-Texte
```

---

**Hinweis/Note:**
Für beide Komponenten wird Python benötigt. Weitere Details zur Konfiguration und Nutzung finden sich im Quellcode und in den Konfigurationsdateien im `config/`-Verzeichnis.

---

**Abhängigkeiten/Dependencies:**

Für das Einlesen der Registerkonfiguration im Server wird das Python-Modul `PyYAML` benötigt. Die C-optimierte Variante `_yaml` wird automatisch verwendet, wenn verfügbar, um die Verarbeitung zu beschleunigen. Es ist keine direkte Nutzung von `_yaml` im eigenen Code notwendig.

The server uses the Python module `PyYAML` to read the register configuration. The C-optimized `_yaml` module is used automatically if available to speed up processing. There is no need to use `_yaml` directly in your own code.

---

**Entwickelt für/Developed for:**

Diese Modbus Tools wurden speziell für die Entwicklung und das Testen der [Lambda Home Assistant Integration](https://github.com/GuidoJeuken-6512/lambda) erstellt. Sie ermöglichen das einfache Simulieren und Abfragen von Modbus-Registerwerten, wie sie von der Integration benötigt werden.

These Modbus tools were specifically developed for the [Lambda Home Assistant integration](https://github.com/GuidoJeuken-6512/lambda). They allow easy simulation and querying of Modbus register values as required by the integration.

---

**Haftungsausschluss/Disclaimer:**

Die Nutzung dieser Software erfolgt auf eigene Gefahr. Es wird keine Haftung für Schäden, Datenverluste oder sonstige Folgen übernommen, die durch die Verwendung der Software entstehen. Jeglicher Regressanspruch ist ausgeschlossen.

Use of this software is at your own risk. No liability is accepted for any damages, data loss, or other consequences resulting from the use of this software. Any claims for compensation are excluded.
