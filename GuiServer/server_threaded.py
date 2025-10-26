"""Threading-fähiger Modbus-Server mit GUI-Integration."""
import threading
import queue
from datetime import datetime
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusServerContext
from pymodbus.datastore import ModbusDeviceContext, ModbusSequentialDataBlock
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse

import yaml
import os

MODBUS_SERVER_PORT = 5020


class LoggingSlaveContext(ModbusDeviceContext):
    """Modbus Slave Context mit Queue-basiertem Logging."""
    
    def __init__(self, log_queue=None, valid_addresses=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_queue = log_queue
        self._last_write_values = {}
        self.valid_addresses = valid_addresses or set()
        
    def log_message(self, msg_type, address, count, values=None, function=None):
        """Sende Log-Nachricht an GUI."""
        if self.log_queue is not None:
            log_msg = {
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "type": msg_type,
                "address": address,
                "count": count,
                "values": values,
                "function": function
            }
            try:
                self.log_queue.put(log_msg, timeout=0.1)
            except queue.Full:
                pass
    
    def getValues(self, fx, address, count=1):
        """Lesen mit Logging."""
        # Different validation for single vs batch reads
        if count == 1:
            # Single register read - strict validation
            if address not in self.valid_addresses:
                exception_code = 2  # Illegal Data Address
                self.log_message("ERROR", address, count, f"Invalid single register address - Exception Code {exception_code}", f"read_function_{fx}")
                return ExceptionResponse(fx, exception_code)
        else:
            # Batch read - less strict validation
            # Only validate if address is completely outside the valid range
            min_valid_addr = min(self.valid_addresses) if self.valid_addresses else 0
            max_valid_addr = max(self.valid_addresses) if self.valid_addresses else 0
            
            # Allow reading beyond valid addresses - just return zeros for undefined registers
            # Only throw exception for addresses that are completely out of range
            if address < min_valid_addr or address > max_valid_addr + 1000:  # Allow some buffer
                exception_code = 2  # Illegal Data Address
                self.log_message("ERROR", address, count, f"Address completely out of range - Exception Code {exception_code}", f"read_function_{fx}")
                return ExceptionResponse(fx, exception_code)

        values = super().getValues(fx, address, count)
        function_name = {
            1: "read_coils",
            2: "read_discrete_inputs",
            3: "read_holding_registers",
            4: "read_input_registers"
        }.get(fx, f"unknown_function_{fx}")

        # Format values
        formatted_values = []
        for val in values:
            if isinstance(val, (int, float)):
                formatted_values.append(f"0x{val:04x} ({val})")
            else:
                formatted_values.append(str(val))

        self.log_message("READ", address, count, formatted_values, function_name)
        return values
    
    def setValues(self, fx, address, values):
        """Schreiben mit Logging."""
        # Check if the requested addresses are valid
        # Only validate if address is completely outside the valid range
        min_valid_addr = min(self.valid_addresses) if self.valid_addresses else 0
        max_valid_addr = max(self.valid_addresses) if self.valid_addresses else 0
        
        # Allow writing beyond valid addresses - just ignore undefined registers
        # Only throw exception for addresses that are completely out of range
        if address < min_valid_addr or address > max_valid_addr + 1000:  # Allow some buffer
            exception_code = 2  # Illegal Data Address
            self.log_message("ERROR", address, len(values), f"Address completely out of range - Exception Code {exception_code}", f"write_function_{fx}")
            return ExceptionResponse(fx, exception_code)

        function_name = {
            5: "write_single_coil",
            6: "write_single_register",
            15: "write_multiple_coils",
            16: "write_multiple_registers"
        }.get(fx, f"unknown_function_{fx}")

        # Format values
        formatted_values = []
        for val in values:
            if isinstance(val, (int, float)):
                formatted_values.append(f"0x{val:04x} ({val})")
            else:
                formatted_values.append(str(val))

        # Store previous value for comparison
        old_value = self._last_write_values.get(address, None)

        self.log_message("WRITE", address, len(values),
                        formatted_values, function_name)

        # Actual write
        super().setValues(fx, address, values)

        # Store new value
        if len(values) > 0:
            self._last_write_values[address] = values[0]
    
    def update_register(self, address, value):
        """Live-Update eines Registers (für GUI)."""
        self.setValues(3, address, [value])


class ModbusServerThread(threading.Thread):
    """Thread für Modbus-Server."""
    
    def __init__(self, log_queue, registers, port=5020):
        super().__init__(daemon=True)
        self.log_queue = log_queue
        self.registers = registers
        self.port = port
        self.running = False
        self.context = None
        
    def run(self):
        """Starte den Modbus-Server."""
        self.running = True
        try:
            context = setup_modbus_server(self.registers, self.log_queue)
            self.context = context
            
            StartTcpServer(
                context=context,
                address=("0.0.0.0", self.port)
            )
        except Exception as e:
            if self.log_queue:
                self.log_message("ERROR", 0, 0, f"Server error: {e}")
        
    def stop(self):
        """Stoppe den Server."""
        self.running = False
        
    def log_message(self, msg_type, address, count, values=None, function=None):
        """Log-Nachricht senden."""
        if self.log_queue is not None:
            log_msg = {
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "type": msg_type,
                "address": address,
                "count": count,
                "values": values,
                "function": function
            }
            try:
                self.log_queue.put(log_msg, timeout=0.1)
            except queue.Full:
                pass
    
    def update_register_value(self, address, value):
        """Update Register-Wert von außen (GUI)."""
        if self.context:
            # Get the slave context for slave id 1
            slaves = self.context[1]  # Get slave id 1
            if hasattr(slaves, 'update_register'):
                slaves.update_register(address, value)


def load_registers(config_file):
    """Lade Register aus YAML."""
    with open(config_file, 'r') as file:
        registers = yaml.safe_load(file)['registers']
        return sorted(registers, key=lambda x: x['address'])


def setup_modbus_server(registers, log_queue=None):
    """Setup Modbus Server mit Logging."""
    # Build set of valid addresses
    valid_addresses = set()
    for reg in registers:
        addr = reg['address']
        reg_type = reg['type']
        # Add all addresses for this register (handle 32-bit)
        if reg_type in ['int32', 'uint32']:
            valid_addresses.add(addr)
            valid_addresses.add(addr + 1)
        else:
            valid_addresses.add(addr)
    
    # Determine block sizes
    max_hr_addr = 0
    max_ir_addr = 0
    max_co_addr = 0
    
    for reg in registers:
        addr = reg['address']
        reg_type = reg['type']
        mode = reg['mode']
        
        size = 2 if reg_type in ['int32', 'uint32'] else 1
        end_addr = addr + size
        
        if mode == 'holding':
            max_hr_addr = max(max_hr_addr, end_addr)
        elif mode == 'input':
            max_ir_addr = max(max_ir_addr, end_addr)
        elif mode == 'coil':
            max_co_addr = max(max_co_addr, end_addr)
    
    # Create blocks
    hr_size = max_hr_addr + 1
    ir_size = max_ir_addr + 1
    co_size = max_co_addr + 1
    
    hr_block = (ModbusSequentialDataBlock(0, [0] * hr_size) 
                if max_hr_addr > 0 else None)
    ir_block = (ModbusSequentialDataBlock(0, [0] * ir_size) 
                if max_ir_addr > 0 else None)
    co_block = (ModbusSequentialDataBlock(0, [0] * co_size) 
                if max_co_addr > 0 else None)
    
    # Create slave context with logging and valid addresses
    store = LoggingSlaveContext(
        log_queue=log_queue,
        valid_addresses=valid_addresses,
        hr=hr_block if hr_block else ModbusSequentialDataBlock(0, [0]),
        ir=ir_block if ir_block else ModbusSequentialDataBlock(0, [0]),
        co=co_block if co_block else ModbusSequentialDataBlock(0, [0]),
        di=ModbusSequentialDataBlock(0, [0])
    )
    
    # Initialize values
    for reg in registers:
        addr = reg['address']
        reg_type = reg['type']
        mode = reg['mode']
        value = int(reg['initial_value'])
        
        # Handle 32-bit values - Big-Endian format
        if reg_type in ['int32', 'uint32']:
            # Big-Endian: High word first, then low word
            high_word = (value >> 16) & 0xFFFF
            low_word = value & 0xFFFF
            values = [high_word, low_word]
        else:
            values = [value]
        
        try:
            if mode == 'holding':
                store.setValues(3, addr, values)
            elif mode == 'input':
                store.setValues(4, addr, values)
            elif mode == 'coil':
                store.setValues(1, addr, values)
        except Exception as e:
            if log_queue:
                log_msg = {
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "type": "ERROR",
                    "address": addr,
                    "count": 0,
                    "values": f"Failed to set: {e}",
                    "function": None
                }
                try:
                    log_queue.put(log_msg, timeout=0.1)
                except queue.Full:
                    pass
    
    # Create context with slave id 1 (Lambda expects Unit ID 1)
    # Map slave id 1 to our store
    slaves = {1: store}
    context = ModbusServerContext(slaves, single=False)
    return context