#!/usr/bin/env python3
"""Teste Exception-Handling für ungültige Register-Adressen"""

from pymodbus.client import ModbusTcpClient

def test_invalid_register():
    print("Teste ungültige Register-Adresse...")

    client = ModbusTcpClient('localhost', port=5020)

    try:
        if client.connect():
            print("OK: Verbindung erfolgreich!")

            # Teste ein ungültiges Register (z.B. 9999)
            print("Lese ungültiges Register 9999...")
            result = client.read_holding_registers(address=9999, count=1)

            if result.isError():
                print(f"FEHLER: {result}")
                print(f"Exception Code: {result.exception_code}")
                print(f"Function Code: {result.function_code}")
            else:
                print(f"OK: Register 9999: {result.registers[0]}")

        else:
            print("FEHLER: Verbindung fehlgeschlagen!")

    except Exception as e:
        print(f"FEHLER: {e}")
    finally:
        client.close()
        print("Verbindung geschlossen.")

if __name__ == "__main__":
    test_invalid_register()
