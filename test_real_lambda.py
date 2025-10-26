from pymodbus.client import ModbusTcpClient

c = ModbusTcpClient('192.168.178.125', port=502)
if c.connect():
    print('Connected to real Lambda')
    # Test read without slave id
    r1 = c.read_holding_registers(address=1000, count=1)
    print(f'Register 1000 (no slave): {r1.registers[0] if not r1.isError() else r1}')
    
    # Test read with slave id 1
    r2 = c.read_holding_registers(address=1000, count=1, slave=1)
    print(f'Register 1000 (slave=1): {r2.registers[0] if not r2.isError() else r2}')
else:
    print('Failed to connect')
c.close()
