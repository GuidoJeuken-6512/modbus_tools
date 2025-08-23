from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusServerContext
from pymodbus.datastore import ModbusSlaveContext, ModbusSequentialDataBlock
import yaml
import os
import logging

# Server configuration constants
MODBUS_SERVER_PORT = 5020  # Standard Modbus TCP port is 502, but we use 5020 for testing

# Logging configuration constants
LOG_ERRORS = True
LOG_WRITE_REGISTERS = True
LOG_READ_REGISTERS = True

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class LoggingSlaveContext(ModbusSlaveContext):
    def getValues(self, fx, address, count=1):
        values = super().getValues(fx, address, count)
        if LOG_READ_REGISTERS:
            function_name = {
                1: "read_coils",
                2: "read_discrete_inputs",
                3: "read_holding_registers",
                4: "read_input_registers"
            }.get(fx, f"unknown_function_{fx}")
            # Format values for better readability
            formatted_values = []
            for val in values:
                if isinstance(val, (int, float)):
                    formatted_values.append(f"0x{val:04x} ({val})")
                else:
                    formatted_values.append(str(val))
            logger.info(f"Read Request - Function: {function_name}, Address: {address}, Count: {count}")
            logger.info(f"Read Response - Values: {formatted_values}")
        return values

    def setValues(self, fx, address, values):
        # pymodbus 3.x: setValues -> set_values
        if LOG_WRITE_REGISTERS:
            function_name = {
                5: "write_single_coil",
                6: "write_single_register",
                15: "write_multiple_coils",
                16: "write_multiple_registers"
            }.get(fx, f"unknown_function_{fx}")
            
            # Format values for better readability
            formatted_values = []
            for val in values:
                if isinstance(val, (int, float)):
                    formatted_values.append(f"0x{val:04x} ({val})")
                else:
                    formatted_values.append(str(val))
            
            logger.info(f"Write Request - Function: {function_name}, Address: {address}")
            logger.info(f"Write Values: {formatted_values}")
        
        # Verify the write operation
        super().setValues(fx, address, values)
        # Read back the values to verify
        written_values = super().getValues(fx, address, len(values))
        if written_values != values and LOG_ERRORS:
            logger.error(f"Write verification failed at address {address}!")
            logger.error(f"Attempted to write: {values}")
            logger.error(f"Actually written: {written_values}")

def load_registers(config_file):
    with open(config_file, 'r') as file:
        registers = yaml.safe_load(file)['registers']
        # Sort registers by address to ensure proper initialization order
        return sorted(registers, key=lambda x: x['address'])

def setup_modbus_server(registers):
    # Determine maximum address needed for each block type
    max_hr_addr = 0
    max_ir_addr = 0
    max_co_addr = 0
    
    # First pass: determine block sizes
    for reg in registers:
        addr = reg['address']
        reg_type = reg['type']
        mode = reg['mode']
        
        # Account for 32-bit registers
        size = 2 if reg_type in ['int32', 'uint32'] else 1
        end_addr = addr + size
        
        if mode == 'holding':
            max_hr_addr = max(max_hr_addr, end_addr)
        elif mode == 'input':
            max_ir_addr = max(max_ir_addr, end_addr)
        elif mode == 'coil':
            max_co_addr = max(max_co_addr, end_addr)

    logger.info(f"Initializing blocks - HR: {max_hr_addr}, IR: {max_ir_addr}, CO: {max_co_addr}")

    # Create data blocks with sufficient size and initialize with zeros
    # Add +1 to size to account for zero-based addressing
    hr_size = max_hr_addr + 1
    ir_size = max_ir_addr + 1
    co_size = max_co_addr + 1

    hr_block = ModbusSequentialDataBlock(0, [0] * hr_size) if max_hr_addr > 0 else None
    ir_block = ModbusSequentialDataBlock(0, [0] * ir_size) if max_ir_addr > 0 else None
    co_block = ModbusSequentialDataBlock(0, [0] * co_size) if max_co_addr > 0 else None

    # Create slave context first
    store = LoggingSlaveContext(
        hr=hr_block if hr_block else ModbusSequentialDataBlock(0, [0]),
        ir=ir_block if ir_block else ModbusSequentialDataBlock(0, [0]),
        co=co_block if co_block else ModbusSequentialDataBlock(0, [0]),
        di=ModbusSequentialDataBlock(0, [0])  # Add empty discrete inputs block
    )

    # Second pass: initialize values
    for reg in registers:
        addr = reg['address']
        reg_type = reg['type']
        mode = reg['mode']
        value = int(reg['initial_value'])
        
        logger.info(f"Setting register - Address: {addr}, Type: {reg_type}, Mode: {mode}, Value: 0x{value:x} ({value})")
        
        # Handle 32-bit values
        if reg_type in ['int32', 'uint32']:
            values = [(value >> 16) & 0xFFFF, value & 0xFFFF]
            logger.info(f"32-bit register split: [0x{values[0]:04x}, 0x{values[1]:04x}]")
        else:
            values = [value]
        
        try:
            if mode == 'holding':
                # Use the correct function code (3) and address
                store.setValues(3, addr, values)
                # Verify the write
                written = store.getValues(3, addr, len(values))
                if written != values:
                    logger.error(f"Verification failed for register {addr}!")
                    logger.error(f"Expected: {values}, Got: {written}")
                    # Try to read the surrounding registers to debug
                    surrounding = store.getValues(3, max(0, addr-1), min(3, hr_size-addr))
                    logger.error(f"Surrounding registers ({max(0, addr-1)}-{min(addr+1, hr_size-1)}): {surrounding}")
            elif mode == 'input':
                store.setValues(4, addr, values)  # 4 = input registers
            elif mode == 'coil':
                store.setValues(1, addr, values)  # 1 = coils
        except Exception as e:
            logger.error(f"Failed to set register {addr}: {e}")
            logger.error(f"Block size - HR: {hr_size}, IR: {ir_size}, CO: {co_size}")
    
    # Verify all registers after initialization
    logger.info("\nVerifying all registers after initialization:")
    for reg in registers:
        addr = reg['address']
        if reg['mode'] == 'holding':
            size = 2 if reg['type'] in ['int32', 'uint32'] else 1
            values = store.getValues(3, addr, size)
            logger.info(f"Register {addr}: {[f'0x{v:04x} ({v})' for v in values]}")
    
    context = ModbusServerContext(slaves=store, single=True)
    return context

def print_registers(registers):
    print("----- Register Overview -----")
    for reg in registers:
        print(f"Address: {reg['address']}, Type: {reg['type']}, Mode: {reg['mode']}, Initial Value: {reg['initial_value']}")
    print("--------------------------")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(base_dir, 'registers.yaml')  # YAML liegt jetzt im selben Verzeichnis wie server.py
    registers = load_registers(config_file)
    
    # Debug: Print all registers
    print_registers(registers)
    
    context = setup_modbus_server(registers)
    logger.info(f"Modbus TCP Server running on port {MODBUS_SERVER_PORT}...")
    try:
        StartTcpServer(
            context=context,
            address=("0.0.0.0", MODBUS_SERVER_PORT)
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise

if __name__ == "__main__":
    main()