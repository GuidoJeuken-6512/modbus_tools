#!/usr/bin/env python3
"""Teste uint32 Register als Big-Endian 32-Bit Register"""

from pymodbus.client import ModbusTcpClient
import struct

def test_uint32_registers():
    print("Teste uint32 Register als Big-Endian 32-Bit...")

    client = ModbusTcpClient('localhost', port=5020)

    try:
        if client.connect():
            print("OK: Verbindung erfolgreich!")

            # Teste uint32 Register 1020 (sollte 1000000 sein)
            print("\nTeste Register 1020 (uint32, sollte 1000000 sein)...")
            result = client.read_holding_registers(address=1020, count=2)

            if result.isError():
                print(f"FEHLER: {result}")
            else:
                high_word, low_word = result.registers
                print(f"Raw Werte: High={high_word} (0x{high_word:04x}), Low={low_word} (0x{low_word:04x})")
                
                # Big-Endian: High-Word zuerst
                uint32_value = (high_word << 16) | low_word
                print(f"Big-Endian uint32: {uint32_value}")
                print(f"Erwartet: 1000000")
                print(f"Korrekt: {'OK' if uint32_value == 1000000 else 'FEHLER'}")

            # Teste uint32 Register 1022 (sollte 3000000 sein)
            print("\nTeste Register 1022 (uint32, sollte 3000000 sein)...")
            result = client.read_holding_registers(address=1022, count=2)

            if result.isError():
                print(f"FEHLER: {result}")
            else:
                high_word, low_word = result.registers
                print(f"Raw Werte: High={high_word} (0x{high_word:04x}), Low={low_word} (0x{low_word:04x})")
                
                # Big-Endian: High-Word zuerst
                uint32_value = (high_word << 16) | low_word
                print(f"Big-Endian uint32: {uint32_value}")
                print(f"Erwartet: 3000000")
                print(f"Korrekt: {'OK' if uint32_value == 3000000 else 'FEHLER'}")

            # Teste uint32 Register 1120 (sollte 10000 sein)
            print("\nTeste Register 1120 (uint32, sollte 10000 sein)...")
            result = client.read_holding_registers(address=1120, count=2)

            if result.isError():
                print(f"FEHLER: {result}")
            else:
                high_word, low_word = result.registers
                print(f"Raw Werte: High={high_word} (0x{high_word:04x}), Low={low_word} (0x{low_word:04x})")
                
                # Big-Endian: High-Word zuerst
                uint32_value = (high_word << 16) | low_word
                print(f"Big-Endian uint32: {uint32_value}")
                print(f"Erwartet: 10000")
                print(f"Korrekt: {'OK' if uint32_value == 10000 else 'FEHLER'}")

            # Teste uint32 Register 1122 (sollte 30000 sein)
            print("\nTeste Register 1122 (uint32, sollte 30000 sein)...")
            result = client.read_holding_registers(address=1122, count=2)

            if result.isError():
                print(f"FEHLER: {result}")
            else:
                high_word, low_word = result.registers
                print(f"Raw Werte: High={high_word} (0x{high_word:04x}), Low={low_word} (0x{low_word:04x})")
                
                # Big-Endian: High-Word zuerst
                uint32_value = (high_word << 16) | low_word
                print(f"Big-Endian uint32: {uint32_value}")
                print(f"Erwartet: 30000")
                print(f"Korrekt: {'OK' if uint32_value == 30000 else 'FEHLER'}")

        else:
            print("FEHLER: Verbindung fehlgeschlagen!")

    except Exception as e:
        print(f"FEHLER: {e}")
    finally:
        client.close()
        print("\nVerbindung geschlossen.")

if __name__ == "__main__":
    test_uint32_registers()
