# Modbus Tools

## Übersicht (Deutsch)

Dieses Projekt enthält drei Hauptkomponenten:

### 1. Modbus Client (GUI) (`modbus_client.py`)
- Grafische Benutzeroberfläche (GUI) zur Abfrage von Modbus TCP Servern
- Ermöglicht das Auslesen von Holding- und Input-Register
- Voreingestellte Werte für Host-IP, Register und Registertyp, aber frei änderbar
- Zeigt die Antwort des Servers in einem Dialogfenster an

### 2. Modbus Client (Kommandozeile) (`client.py`)
- Kommandozeilen-Tool für automatisierte Modbus TCP Abfragen
- Liest vordefinierte Registergruppen (z.B. Temperatur, Solar) und skaliert Werte automatisch
- Umfangreiches Logging (INFO/ERROR) für Debugging und Entwicklung
- Beispielaufruf: `python client.py`
- Ideal für automatisierte Tests und zur schnellen Überprüfung von Registerwerten
- Registeradressen und Skalierungsfaktoren sind im Code anpassbar

### 3. Modbus Server (`server.py`)
- Implementiert einen einfachen Modbus TCP Server
- Dient zu Test- und Entwicklungszwecken
- Registerwerte können über Konfigurationsdateien (`config/register.yaml`) angepasst werden

#### Server Logging-Konfiguration
Der Server bietet flexible Logging-Optionen, die über Konstanten am Anfang der `server.py` gesteuert werden können:

```python
# Logging-Konfigurationskonstanten
LOG_ERRORS = True        # Steuert das Logging von Fehlermeldungen
LOG_WRITE_REGISTERS = True  # Steuert das Logging von Schreiboperationen
LOG_READ_REGISTERS = False  # Steuert das Logging von Leseoperationen
```

Verfügbare Logging-Optionen:
1. **Fehler-Logging** (`LOG_ERRORS`)
   - Bei `True`: Loggt alle Fehlermeldungen, einschließlich Schreibverifizierungsfehler
   - Bei `False`: Unterdrückt Fehlermeldungen
   - Standard: `True`

2. **Register-Schreib-Logging** (`LOG_WRITE_REGISTERS`)
   - Bei `True`: Loggt alle Schreiboperationen auf Register
   - Bei `False`: Unterdrückt Schreiboperationen-Logs
   - Standard: `True`

3. **Register-Lese-Logging** (`LOG_READ_REGISTERS`)
   - Bei `True`: Loggt alle Leseoperationen von Registern
   - Bei `False`: Unterdrückt Leseoperationen-Logs
   - Standard: `False`

## Usage (English)

This project contains three main components:

### 1. Modbus Client (GUI) (`modbus_client.py`)
- Graphical user interface (GUI) for querying Modbus TCP servers
- Allows reading holding and input registers
- Pre-filled values for host IP, register, and register type (all editable)
- Displays the server response in a dialog window

### 2. Modbus Client (CLI) (`client.py`)
- Command-line tool for automated Modbus TCP queries
- Reads predefined register groups (e.g., temperature, solar) and applies scaling automatically
- Extensive logging (INFO/ERROR) for debugging and development
- Example usage: `python client.py`
- Ideal for automated tests and quick register value checks
- Register addresses and scaling factors can be adjusted in the code

### 3. Modbus Server (`server.py`)
- Implements a simple Modbus TCP server
- Intended for testing and development
- Register values can be customized via configuration files (`config/register.yaml`)

#### Server Logging Configuration
The server provides flexible logging options that can be configured through constants at the beginning of `server.py`:

```python
# Logging configuration constants
LOG_ERRORS = True        # Controls logging of error messages
LOG_WRITE_REGISTERS = True  # Controls logging of write operations
LOG_READ_REGISTERS = False  # Controls logging of read operations
```

Available logging options:
1. **Error Logging** (`LOG_ERRORS`)
   - When `True`: Logs all error messages, including write verification failures
   - When `False`: Suppresses error messages
   - Default: `True`

2. **Write Register Logging** (`LOG_WRITE_REGISTERS`)
   - When `True`: Logs all write operations to registers
   - When `False`: Suppresses write operation logs
   - Default: `True`

3. **Read Register Logging** (`LOG_READ_REGISTERS`)
   - When `True`: Logs all read operations from registers
   - When `False`: Suppresses read operation logs
   - Default: `False`

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
