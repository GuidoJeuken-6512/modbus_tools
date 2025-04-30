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
