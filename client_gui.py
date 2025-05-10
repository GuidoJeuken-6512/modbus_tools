import tkinter as tk
from tkinter import ttk, messagebox
from pymodbus.client import ModbusTcpClient
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Register type definitions
REGISTER_TYPES = {
    "Temperature (0.1°C)": {"type": "holding", "scale": 10.0, "unit": "°C"},
    "Temperature (0.01°C)": {"type": "holding", "scale": 100.0, "unit": "°C"},
    "Power (0.1 kW)": {"type": "holding", "scale": 10.0, "unit": "kW"},
    "Energy (kWh)": {"type": "holding", "scale": 1.0, "unit": "kWh"},
    "State": {"type": "holding", "scale": 1.0, "unit": ""},
    "Error": {"type": "holding", "scale": 1.0, "unit": ""},
    "Raw Holding Register": {"type": "holding", "scale": 1.0, "unit": ""},
    "Raw Input Register": {"type": "input", "scale": 1.0, "unit": ""}
}

def query_modbus():
    host_ip = host_ip_entry.get()
    try:
        register = int(register_entry.get())
    except ValueError:
        messagebox.showerror("Input Error", "Register must be an integer.")
        return

    register_type = register_type_combobox.get()
    if register_type not in REGISTER_TYPES:
        messagebox.showerror("Input Error", "Invalid register type.")
        return

    reg_info = REGISTER_TYPES[register_type]
    count = 2 if "32bit" in register_type else 1

    try:
        client = ModbusTcpClient(host_ip)
        if not client.connect():
            messagebox.showerror("Connection Error", "Unable to connect to Modbus server.")
            return

        try:
            # Read one register before and after to verify addressing
            safe_start = max(0, register - 1)
            safe_count = min(count + 2, 3)
            
            if reg_info["type"] == "holding":
                response = client.read_holding_registers(address=safe_start, count=safe_count)
            else:
                response = client.read_input_registers(address=safe_start, count=safe_count)

            if not hasattr(response, 'registers'):
                messagebox.showerror("Modbus Error", "Error reading register.")
                return

            # Log raw values with addresses
            values = response.registers
            for i, value in enumerate(values):
                addr = safe_start + i
                logger.info(f"Register {addr}: 0x{value:04x} ({value})")

            # Extract and scale the requested register value
            if register > safe_start:
                values = values[1:]  # Remove the extra register at the start
            if len(values) > count:
                values = values[:-1]  # Remove the extra register at the end

            if count == 2:  # 32-bit value
                value = (values[0] << 16) | values[1]
            else:
                value = values[0]

            # Scale the value
            scaled_value = value / reg_info["scale"]
            
            # Format the result message
            if reg_info["unit"]:
                result = f"Register {register}:\nRaw Value: 0x{value:04x} ({value})\nScaled Value: {scaled_value:.2f} {reg_info['unit']}"
            else:
                result = f"Register {register}:\nRaw Value: 0x{value:04x} ({value})"

            # Show the result
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, result)

        except Exception as e:
            messagebox.showerror("Modbus Error", f"Error reading register: {str(e)}")
        finally:
            client.close()

    except Exception as e:
        messagebox.showerror("Error", str(e))

# Create the main application window
root = tk.Tk()
root.title("Lambda Heat Pump Modbus Client")

# Create main frame
main_frame = ttk.Frame(root, padding="10")
main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Host IP input
host_ip_label = ttk.Label(main_frame, text="Host IP:")
host_ip_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
host_ip_entry = ttk.Entry(main_frame)
host_ip_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
host_ip_entry.insert(0, "localhost")

# Register input
register_label = ttk.Label(main_frame, text="Register:")
register_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
register_entry = ttk.Entry(main_frame)
register_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

# Register type selection
register_type_label = ttk.Label(main_frame, text="Register Type:")
register_type_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
register_type_combobox = ttk.Combobox(main_frame, values=list(REGISTER_TYPES.keys()))
register_type_combobox.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
register_type_combobox.set("Temperature (0.1°C)")

# Query button
query_button = ttk.Button(main_frame, text="Query Register", command=query_modbus)
query_button.grid(row=3, column=0, columnspan=2, pady=10)

# Result text area
result_text = tk.Text(main_frame, height=5, width=40)
result_text.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

# Configure grid weights
main_frame.columnconfigure(1, weight=1)

# Run the application
root.mainloop()