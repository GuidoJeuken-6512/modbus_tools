from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext, ModbusSequentialDataBlock
import yaml
import os

def load_registers(config_file):
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)['registers']

def setup_modbus_server(registers):
    # Dynamisch die maximale Adresse bestimmen (inkl. 32-Bit-Register)
    max_addr = 0
    for reg in registers:
        addr = reg['address']
        reg_type = reg['type']
        # 32-Bit Register belegen 2 Adressen
        if reg_type in ['int32', 'uint32']:
            addr += 1
        if addr > max_addr:
            max_addr = addr

    coils = [0] * (max_addr + 2)
    holding_registers = [0] * (max_addr + 2)

    for reg in registers:
        addr = reg['address']
        reg_type = reg['type']
        mode = reg['mode']
        value = reg['initial_value']
        if mode == 'coil':
            if reg_type in ['int32', 'uint32']:
                coils[addr] = (int(value) >> 16) & 0xFFFF
                coils[addr + 1] = int(value) & 0xFFFF
            else:
                coils[addr] = int(value)
        elif mode == 'holding':
            if reg_type in ['int32', 'uint32']:
                holding_registers[addr] = (int(value) >> 16) & 0xFFFF
                holding_registers[addr + 1] = int(value) & 0xFFFF
            else:
                holding_registers[addr] = int(value)

    co_block = ModbusSequentialDataBlock(0, coils)
    hr_block = ModbusSequentialDataBlock(0, holding_registers)
    co_block.zero_mode = True
    hr_block.zero_mode = True

    store = ModbusSlaveContext(
        co=co_block,
        hr=hr_block
    )
    context = ModbusServerContext(slaves=store, single=True)
    return context

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(base_dir, 'config', 'registers.yaml')
    registers = load_registers(config_file)
    context = setup_modbus_server(registers)
    print("Modbus TCP Server läuft auf Port 502...")
    StartTcpServer(context, address=("192.168.178.22", 502))

if __name__ == "__main__":
    main()