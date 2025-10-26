#!/usr/bin/env python3
"""Teste Akkumulator-Register Inkrementierung"""

from pymodbus.client import ModbusTcpClient
import time

def test_accumulator_increment():
    print("Teste Akkumulator-Register Inkrementierung...")

    client = ModbusTcpClient('localhost', port=5020)

    try:
        if client.connect():
            print("OK: Verbindung erfolgreich!")

            # Teste Register 1020 (sollte alle 10 Sekunden um 100 erhöht werden)
            print("\nTeste Register 1020 (Akkumulator)...")
            
            # Erste Messung
            result1 = client.read_holding_registers(address=1020, count=2)
            if not result1.isError():
                high1, low1 = result1.registers
                value1 = (high1 << 16) | low1
                print(f"Erste Messung: {value1} (High: {high1}, Low: {low1})")
            
            # Warte 12 Sekunden
            print("Warte 12 Sekunden...")
            time.sleep(12)
            
            # Zweite Messung
            result2 = client.read_holding_registers(address=1020, count=2)
            if not result2.isError():
                high2, low2 = result2.registers
                value2 = (high2 << 16) | low2
                print(f"Zweite Messung: {value2} (High: {high2}, Low: {low2})")
                
                diff = value2 - value1
                print(f"Differenz: {diff}")
                print(f"Erwartet: 10")
                print(f"Korrekt: {'OK' if diff == 10 else 'FEHLER'}")

            # Teste Register 1120 (WP2 Akkumulator)
            print("\nTeste Register 1120 (WP2 Akkumulator)...")
            
            result3 = client.read_holding_registers(address=1120, count=2)
            if not result3.isError():
                high3, low3 = result3.registers
                value3 = (high3 << 16) | low3
                print(f"Aktueller Wert: {value3} (High: {high3}, Low: {low3})")

        else:
            print("FEHLER: Verbindung fehlgeschlagen!")

    except Exception as e:
        print(f"FEHLER: {e}")
    finally:
        client.close()
        print("\nVerbindung geschlossen.")

if __name__ == "__main__":
    test_accumulator_increment()
