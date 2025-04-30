from pymodbus.client import ModbusTcpClient
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def read_register_group(client, name, start_addr, count, scale_factors=None):
    """Read a group of registers and apply scaling if needed"""
    logger.info(f"\nReading {name} (Address: {start_addr}, Count: {count})")
    
    # Read one extra register before and after to verify addressing
    safe_start = max(0, start_addr - 1)
    safe_count = min(count + 2, 9999 - safe_start)
    
    result = client.read_holding_registers(address=safe_start, count=safe_count)
    
    if not hasattr(result, 'registers'):
        logger.error(f"Error reading {name}: {result}")
        return None
        
    values = result.registers
    
    # Log all raw values with their addresses
    for i, value in enumerate(values):
        addr = safe_start + i
        logger.info(f"Register {addr}: 0x{value:04x} ({value})")
    
    # Extract the requested registers
    if start_addr > safe_start:
        values = values[1:]  # Remove the extra register at the start
    if len(values) > count:
        values = values[:count]  # Remove the extra register at the end
    
    if scale_factors:
        scaled_values = []
        for i, value in enumerate(values):
            if i < len(scale_factors) and scale_factors[i] is not None:
                scaled_values.append(value / scale_factors[i])
            else:
                scaled_values.append(value)
        return scaled_values
    return values

def test_read_registers():
    client = ModbusTcpClient('localhost', port=502)
    
    try:
        if not client.connect():
            logger.error("Failed to connect to server")
            return

        # Read Temperature Settings (5050-5051)
        logger.info("\nTesting Temperature Settings")
        temp_values = read_register_group(
            client,
            "Temperature Settings",
            start_addr=5050,
            count=2,
            scale_factors=[10, 10]  # Both values are temperatures with 0.1°C resolution
        )
        
        if temp_values:
            print("\nTemperature Settings:")
            print(f"Flow Line Offset: {temp_values[0]:.1f}°C")
            print(f"Target Room Temperature: {temp_values[1]:.1f}°C")

        # Read Solar Sensors (4000-4005)
        solar_values = read_register_group(
            client,
            "Solar Sensors",
            start_addr=4000,
            count=6,
            scale_factors=[None, None, 10, 10, 10, None]  # Scale factors for temperatures
        )
        
        if solar_values:
            print("\nSolar Sensors:")
            print(f"Error Number: {solar_values[0]}")
            print(f"Operating State: {solar_values[1]}")
            print(f"Collector Temperature: {solar_values[2]:.1f}°C")
            print(f"Storage Temperature: {solar_values[3]:.1f}°C")
            print(f"Power Current: {solar_values[4]/10:.1f} kW")
            print(f"Energy Total: {solar_values[5]} kWh")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    print("Starting Modbus client test...")
    test_read_registers() 