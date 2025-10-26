#!/usr/bin/env python3
"""Einfacher Modbus-Verbindungstest"""

from pymodbus.client import ModbusTcpClient
import time

def test_connection():
    print("Teste Modbus-Verbindung...")
    
    # Verbindung zu localhost:5020
    client = ModbusTcpClient('localhost', port=5020)
    
    try:
        print("Versuche Verbindung...")
        if client.connect():
            print("OK: Verbindung erfolgreich!")
            
            # Teste Register 1000
            print("Lese Register 1000...")
            result = client.read_holding_registers(address=1000, count=1)
            
            if result.isError():
                print(f"FEHLER beim Lesen: {result}")
            else:
                print(f"OK: Register 1000: {result.registers[0]}")
                
        else:
            print("FEHLER: Verbindung fehlgeschlagen!")
            
    except Exception as e:
        print(f"FEHLER: {e}")
    finally:
        client.close()
        print("Verbindung geschlossen.")

if __name__ == "__main__":
    test_connection()

