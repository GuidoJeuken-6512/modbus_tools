import tkinter as tk
from tkinter import ttk, messagebox
from pymodbus.client import ModbusTcpClient

def query_modbus():
    host_ip = host_ip_entry.get()
    register = register_entry.get()
    register_type = register_type_combobox.get()

    if not host_ip or not register or not register_type:
        messagebox.showerror("Input Error", "Please fill in all fields.")
        return

    try:
        register = int(register)
    except ValueError:
        messagebox.showerror("Input Error", "Register must be an integer.")
        return

    try:
        client = ModbusTcpClient(host_ip)
        if not client.connect():
            messagebox.showerror("Connection Error", "Unable to connect to Modbus server.")
            return

        if register_type == "Holding Register":
            response = client.read_holding_registers(register)
        elif register_type == "Input Register":
            response = client.read_input_registers(register)
        else:
            messagebox.showerror("Input Error", "Invalid register type.")
            return

        if response.isError():
            messagebox.showerror("Modbus Error", "Error reading register.")
        else:
            messagebox.showinfo("Modbus Response", f"Value: {response.registers[0]}")

        client.close()
    except Exception as e:
        messagebox.showerror("Error", str(e))

# Create the main application window
root = tk.Tk()
root.title("Modbus TCP Client")

# Host IP input
host_ip_label = tk.Label(root, text="Host IP:")
host_ip_label.grid(row=0, column=0, padx=10, pady=5, sticky="e")
host_ip_entry = tk.Entry(root)
host_ip_entry.grid(row=0, column=1, padx=10, pady=5)
# Pre-fill the host IP field with a default value
host_ip_entry.insert(0, "192.168.178.22")

# Register input
register_label = tk.Label(root, text="Register:")
register_label.grid(row=1, column=0, padx=10, pady=5, sticky="e")
register_entry = tk.Entry(root)
register_entry.grid(row=1, column=1, padx=10, pady=5)
# Pre-fill the register field with a default value
register_entry.insert(0, "1011")

# Register type selection
register_type_label = tk.Label(root, text="Register Type:")
register_type_label.grid(row=2, column=0, padx=10, pady=5, sticky="e")
register_type_combobox = ttk.Combobox(root, values=["Holding Register", "Input Register"])
register_type_combobox.grid(row=2, column=1, padx=10, pady=5)
# Pre-select the register type as 'Holding Register'
register_type_combobox.set("Holding Register")

# Query button
query_button = tk.Button(root, text="Query", command=query_modbus)
query_button.grid(row=3, column=0, columnspan=2, pady=10)

# Run the application
root.mainloop()