"""Modbus Server GUI mit Tkinter."""
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
import time
import os
import yaml
from server_threaded import ModbusServerThread, load_registers
from register_manager import (
    load_state, save_state, update_register_value, get_register_value,
    get_value_text, is_wp2_register, REGISTER_MAPPINGS,
    filter_registers_for_mode
)


class ModbusGUI:
    """Haupt-GUI-Klasse."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Modbus Server GUI")
        self.root.geometry("1400x800")
        
        # State management
        self.state = load_state()
        self.log_queue = queue.Queue()
        self.server_thread = None
        self.accumulator_timer = None
        self.registers = load_registers('registers.yaml')
        
        # Register variable widgets dict and widget references
        self.register_vars = {}
        self.register_widgets = {}  # Store widget references for show/hide
        self.register_group_widgets = {}  # Store group frame references for show/hide
        
        # Store default values from registers.yaml
        self.default_values = {}
        for reg in self.registers:
            if reg['address'] in REGISTER_MAPPINGS:
                self.default_values[reg['address']] = reg['initial_value']
        
        self.create_widgets()
        self.start_polling()
        
    def create_widgets(self):
        """Erstelle GUI-Widgets."""
        # Top bar with buttons
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.start_btn = tk.Button(top_frame, text="Start Server", 
                                   command=self.start_server, width=15)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(top_frame, text="Stop Server", 
                                  command=self.stop_server, width=15, 
                                  state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Main content area with 3 columns
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Column 1: WP1 + Common registers
        col1_frame = tk.LabelFrame(main_frame, text="WP1 + Common Config")
        col1_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        col1_canvas = tk.Canvas(col1_frame)
        col1_scrollbar = tk.Scrollbar(col1_frame, orient="vertical", 
                                      command=col1_canvas.yview)
        self.col1_scrollable_frame = tk.Frame(col1_canvas)
        
        self.col1_scrollable_frame.bind(
            "<Configure>",
            lambda e: col1_canvas.configure(
                scrollregion=col1_canvas.bbox("all"))
        )
        
        col1_canvas.create_window((0, 0), window=self.col1_scrollable_frame,
                                  anchor="nw")
        col1_canvas.configure(yscrollcommand=col1_scrollbar.set)
        
        col1_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        col1_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Column 2: WP2 registers
        col2_frame = tk.LabelFrame(main_frame, text="WP2 Config")
        col2_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        col2_canvas = tk.Canvas(col2_frame)
        col2_scrollbar = tk.Scrollbar(col2_frame, orient="vertical",
                                      command=col2_canvas.yview)
        self.col2_scrollable_frame = tk.Frame(col2_canvas)
        
        self.col2_scrollable_frame.bind(
            "<Configure>",
            lambda e: col2_canvas.configure(
                scrollregion=col2_canvas.bbox("all"))
        )
        
        col2_canvas.create_window((0, 0), window=self.col2_scrollable_frame,
                                  anchor="nw")
        col2_canvas.configure(yscrollcommand=col2_scrollbar.set)
        
        col2_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        col2_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Column 3: Mode & Logging controls
        col3_frame = tk.LabelFrame(main_frame, text="Mode & Logging")
        col3_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # WP Mode
        mode_label = tk.Label(col3_frame, text="Mode:", font=("Arial", 10, "bold"))
        mode_label.pack(pady=5)
        
        self.wp_mode_var = tk.IntVar(value=self.state["heat_pump_mode"])
        
        wp1_radio = tk.Radiobutton(col3_frame, text="1 WP", variable=self.wp_mode_var,
                                   value=1, command=self.on_mode_changed)
        wp1_radio.pack(anchor=tk.W, padx=10)
        
        wp2_radio = tk.Radiobutton(col3_frame, text="2 WP", variable=self.wp_mode_var,
                                   value=2, command=self.on_mode_changed)
        wp2_radio.pack(anchor=tk.W, padx=10)
        
        # Log Filter
        filter_label = tk.Label(col3_frame, text="Log Filter:", 
                               font=("Arial", 10, "bold"))
        filter_label.pack(pady=(20, 5))
        
        self.log_filter_var = tk.StringVar(value="ALL")
        
        tk.Radiobutton(col3_frame, text="Alle", variable=self.log_filter_var,
                      value="ALL", command=self.apply_log_filter).pack(anchor=tk.W, padx=10)
        tk.Radiobutton(col3_frame, text="Nur Write", variable=self.log_filter_var,
                      value="WRITE", command=self.apply_log_filter).pack(anchor=tk.W, padx=10)
        tk.Radiobutton(col3_frame, text="Nur Read", variable=self.log_filter_var,
                      value="READ", command=self.apply_log_filter).pack(anchor=tk.W, padx=10)
        
        tk.Button(col3_frame, text="Clear Logs", 
                 command=self.clear_logs).pack(pady=10, padx=5)
        
        # Create register controls
        self.create_register_controls()
        
        # Log output at bottom
        log_frame = tk.LabelFrame(self.root, text="Log Output")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=140)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.configure(state=tk.DISABLED)
        
    def create_register_controls(self):
        """Erstelle Register-Kontroll-Elemente."""
        # Group registers by component
        hp1_registers = [(0, 1), (1000, 1003)]  # ambient + HP1
        hp2_registers = [(1100, 1103)]
        boiler1_registers = [(2001, 2001)]
        boiler2_registers = [(2101, 2101)]
        buffer1_registers = [(3001, 3001)]
        buffer2_registers = [(3101, 3101)]
        solar1_registers = [(4001, 4001)]
        hc1_registers = [(5001, 5001)]
        hc2_registers = [(5101, 5101)]
        
        # Column 1 widgets
        self.create_register_group(self.col1_scrollable_frame, "Ambient", 
                                   [hp1_registers[0]])
        self.create_register_group(self.col1_scrollable_frame, "Heat Pump 1", 
                                   [hp1_registers[1]])
        self.create_register_group(self.col1_scrollable_frame, "Boiler 1", 
                                   boiler1_registers)
        self.create_register_group(self.col1_scrollable_frame, "Buffer 1", 
                                   buffer1_registers)
        self.create_register_group(self.col1_scrollable_frame, "Heating Circuit 1",
                                   hc1_registers)
        self.create_register_group(self.col1_scrollable_frame, "Solar 1",
                                   solar1_registers)
        
        # Column 2 widgets (WP2 components)
        self.create_register_group(self.col2_scrollable_frame, "Heat Pump 2",
                                   hp2_registers)
        self.create_register_group(self.col2_scrollable_frame, "Boiler 2",
                                   boiler2_registers)
        self.create_register_group(self.col2_scrollable_frame, "Buffer 2",
                                   buffer2_registers)
        self.create_register_group(self.col2_scrollable_frame, "Heating Circuit 2",
                                   hc2_registers)
        
        # Load initial values from state
        self.load_register_values()
        
        # Initially hide WP2 registers if mode is 1 WP
        if self.wp_mode_var.get() == 1:
            for group_name, frame_widget in self.register_group_widgets.items():
                if "2" in group_name or "WP2" in group_name:
                    frame_widget.pack_forget()
        
    def create_register_group(self, parent, group_name, addresses):
        """Erstelle eine Register-Gruppe."""
        frame = tk.Frame(parent, relief=tk.RAISED, borderwidth=1)
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        label = tk.Label(frame, text=group_name, font=("Arial", 9, "bold"))
        label.pack()
        
        # Store group frame reference
        self.register_group_widgets[group_name] = frame
        
        for addr_range in addresses:
            for addr in range(addr_range[0], addr_range[-1] + 1):
                if addr in REGISTER_MAPPINGS:
                    self.create_register_control(frame, addr)
    
    def create_register_control(self, parent, address):
        """Erstelle ein einzelnes Register-Kontroll-Element."""
        mapping = REGISTER_MAPPINGS[address]
        name = mapping["name"]
        
        frame = tk.Frame(parent)
        frame.pack(fill=tk.X, padx=10, pady=2)
        
        label = tk.Label(frame, text=f"{name}:", width=20, anchor=tk.W)
        label.pack(side=tk.LEFT)
        
        var = tk.StringVar()
        self.register_vars[address] = var
        
        combobox = ttk.Combobox(frame, textvariable=var, width=25, 
                               state="readonly")
        combobox.pack(side=tk.LEFT)
        
        # Store widget reference for show/hide functionality
        self.register_widgets[address] = frame
        
        # Populate options
        if mapping["mapping"]:
            options = [f"{k} - {v}" for k, v in mapping["mapping"].items()]
            combobox['values'] = options
        else:
            combobox['values'] = ["No mapping available"]
        
        # Set callback
        combobox.bind("<<ComboboxSelected>>", 
                     lambda e, a=address: self.on_register_changed(a))
        
    def load_register_values(self):
        """Lade Register-Werte aus State oder Default-Werten."""
        for addr, var in self.register_vars.items():
            # First try to get saved value from state
            saved_value = get_register_value(self.state, addr)
            
            # If no saved value, use default from registers.yaml
            if saved_value is None:
                saved_value = self.default_values.get(addr)
            
            # Set the value in the GUI
            if saved_value is not None:
                mapping = REGISTER_MAPPINGS[addr]
                if mapping["mapping"]:
                    # Find the option that matches the value
                    options = [f"{k} - {v}" for k, v in mapping["mapping"].items()]
                    for option in options:
                        if option.startswith(str(saved_value) + " -"):
                            var.set(option)
                            break
    
    def on_register_changed(self, address):
        """Wird aufgerufen wenn ein Register geändert wird."""
        var = self.register_vars[address]
        selected = var.get()
        if selected and selected != "No mapping available":
            # Extract numeric value and text
            parts = selected.split(" - ", 1)
            value_str = parts[0]
            text = parts[1] if len(parts) > 1 else ""
            
            try:
                value = int(value_str)
                update_register_value(self.state, address, value)
                
                # Update server if running
                if self.server_thread and self.server_thread.running:
                    self.server_thread.update_register_value(address, value)
                
                # Log with mapping text
                if text:
                    self.add_log(f"Register {address} changed to {value} ({text})")
                else:
                    self.add_log(f"Register {address} changed to {value}")
            except ValueError:
                pass
    
    def on_mode_changed(self):
        """WP-Modus wurde geändert."""
        self.state["heat_pump_mode"] = self.wp_mode_var.get()
        save_state(self.state)
        
        # Show/hide WP2 register groups
        wp2_enabled = self.wp_mode_var.get() == 2
        for group_name, frame_widget in self.register_group_widgets.items():
            if "2" in group_name or "WP2" in group_name:
                if wp2_enabled:
                    frame_widget.pack(fill=tk.X, padx=5, pady=5, before=None)
                else:
                    frame_widget.pack_forget()
        
    def start_server(self):
        """Starte den Modbus-Server."""
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # Filter registers based on WP mode
        hp_mode = self.wp_mode_var.get()
        filtered_registers = filter_registers_for_mode(self.registers, hp_mode)
        
        self.add_log(f"Starting server with {len(filtered_registers)} registers (WP mode: {hp_mode})")
        
        self.server_thread = ModbusServerThread(self.log_queue, filtered_registers)
        self.server_thread.start()
        
        self.add_log("Server started on port 5020")
        
        # Start accumulator timer
        self.start_accumulator_timer()
        
    def stop_server(self):
        """Stoppe den Modbus-Server."""
        if self.server_thread:
            self.server_thread.stop()
            self.server_thread = None
        
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        # Stop accumulator timer
        if self.accumulator_timer:
            self.accumulator_timer.cancel()
        
        self.add_log("Server stopped")
        
    def start_accumulator_timer(self):
        """Starte Timer für Auto-Inkrementierung (alle 10 Sekunden)."""
        if self.server_thread and self.server_thread.running:
            # Increment accumulator registers
            accumulator_addrs = [1020, 1022]  # WP1
            
            if self.wp_mode_var.get() == 2:  # Add WP2
                accumulator_addrs.extend([1120, 1122])
            
            for addr in accumulator_addrs:
                current = get_register_value(self.state, addr, 0)
                new_value = current + 1
                update_register_value(self.state, addr, new_value)
                
                if self.server_thread:
                    self.server_thread.update_register_value(addr, new_value)
        
        # Schedule next update
        self.accumulator_timer = self.root.after(10000, self.start_accumulator_timer)
    
    def apply_log_filter(self):
        """Filter Log-Ausgabe."""
        # Will be handled in polling
        pass
    
    def clear_logs(self):
        """Lösche Log-Ausgabe."""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def add_log(self, message, log_type="INFO"):
        """Füge eine Log-Nachricht hinzu."""
        self.log_text.configure(state=tk.NORMAL)
        
        timestamp = time.strftime('%H:%M:%S')
        color_tags = {"READ": "green", "WRITE": "blue", "ERROR": "red"}
        
        self.log_text.insert(tk.END, f"{timestamp} [{log_type}] {message}\n")
        
        if log_type in color_tags:
            start = f"{timestamp} [{log_type}]"
            self.log_text.tag_add(log_type, 
                                 f"end-{len(message)+len(start)+1}c", 
                                 f"end-{len(message)}c")
            self.log_text.tag_config(log_type, foreground=color_tags[log_type])
        
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def start_polling(self):
        """Starte Polling für Log-Queue."""
        self.poll_log_queue()
        self.root.after(1000, self.start_polling)
    
    def poll_log_queue(self):
        """Poll Log-Queue und zeige neue Einträge an."""
        while not self.log_queue.empty():
            try:
                log_msg = self.log_queue.get(timeout=0.1)
                
                # Apply filter
                if self.log_filter_var.get() != "ALL":
                    if self.log_filter_var.get() != log_msg["type"]:
                        continue
                
                # Format message
                addr = log_msg["address"]
                log_type = log_msg["type"]
                values = log_msg.get("values", "")
                
                message = f"[{log_type}] Addr: {addr}"
                if values:
                    message += f", Val: {values}"
                
                self.add_log(message, log_type)
                
            except queue.Empty:
                break


def main():
    """Hauptfunktion."""
    root = tk.Tk()
    app = ModbusGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
