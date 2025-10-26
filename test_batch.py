#!/usr/bin/env python3
"""Teste Batch-Read mit gemischten gültigen/ungültigen Registern"""

from pymodbus.client import ModbusTcpClient

def test_batch_read():
    print("Teste Batch-Read mit gemischten Registern...")

    client = ModbusTcpClient('localhost', port=5020)

    try:
        if client.connect():
            print("OK: Verbindung erfolgreich!")

            # Teste Batch-Read von 1004-1009 (sollte funktionieren)
            print("Lese Batch 1004-1009...")
            result = client.read_holding_registers(address=1004, count=6)

            if result.isError():
                print(f"FEHLER: {result}")
            else:
                print(f"OK: Batch 1004-1009: {result.registers}")

            # Teste Batch-Read von 2003 (sollte funktionieren)
            print("Lese Register 2003...")
            result = client.read_holding_registers(address=2003, count=1)

            if result.isError():
                print(f"FEHLER: {result}")
            else:
                print(f"OK: Register 2003: {result.registers[0]}")

            # Teste Batch-Read von 3003-3009 (sollte funktionieren)
            print("Lese Batch 3003-3009...")
            result = client.read_holding_registers(address=3003, count=7)

            if result.isError():
                print(f"FEHLER: {result}")
            else:
                print(f"OK: Batch 3003-3009: {result.registers}")

        else:
            print("FEHLER: Verbindung fehlgeschlagen!")

    except Exception as e:
        print(f"FEHLER: {e}")
    finally:
        client.close()
        print("Verbindung geschlossen.")

if __name__ == "__main__":
    test_batch_read()
