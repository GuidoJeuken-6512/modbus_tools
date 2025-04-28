# Modbus Tools

## Übersicht (Deutsch)

Dieses Projekt enthält zwei Hauptkomponenten:

### 1. Modbus Client (`modbus_client.py`)
- Grafische Benutzeroberfläche (GUI) zur Abfrage von Modbus TCP Servern
- Ermöglicht das Auslesen von Holding- und Input-Register
- Voreingestellte Werte für Host-IP, Register und Registertyp, aber frei änderbar
- Zeigt die Antwort des Servers in einem Dialogfenster an

### 2. Modbus Server (`server.py`)
- Implementiert einen einfachen Modbus TCP Server
- Dient zu Test- und Entwicklungszwecken
- Registerwerte können über Konfigurationsdateien /config/register.yaml) angepasst werden

## Usage (English)

This project contains two main components:

### 1. Modbus Client (`modbus_client.py`)
- Graphical user interface (GUI) for querying Modbus TCP servers
- Allows reading holding and input registers
- Pre-filled values for host IP, register, and register type (all editable)
- Displays the server response in a dialog window

### 2. Modbus Server (`server.py`)
- Implements a simple Modbus TCP server
- Intended for testing and development
- Register values can be customized via configuration files

---

**Hinweis/Note:**
Für beide Komponenten wird Python benötigt. Weitere Details zur Konfiguration und Nutzung finden sich im Quellcode und in den Konfigurationsdateien im `config/`-Verzeichnis.
