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
    filter_registers_for_mode, encode_32bit, decode_32bit
)
from const_mapping import MODE_CASCADE, MODES_BY_VALUE


class ModbusGUI:
    """Haupt-GUI-Klasse."""

    OPERATING_MODE_DISPLAY = {
        "heating": "Heizen",
        "hot_water": "Warmwasser",
        "cooling": "Kühlen",
        "defrost": "Defrost",
    }
    OPERATING_MODE_DISPLAY_REVERSE = {v: k for k, v in OPERATING_MODE_DISPLAY.items()}

    DEFAULT_INCREMENTS = {
        "electrical_increment": 10,
        "thermal_increment": 40,
    }
    INCREMENT_LABELS = {
        "electrical_increment": "Elektrisches Inkrement",
        "thermal_increment": "Thermisches Inkrement",
    }

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
        
        self.wp1_radio = tk.Radiobutton(col3_frame, text="1 WP", variable=self.wp_mode_var,
                                   value=1, command=self.on_mode_changed)
        self.wp1_radio.pack(anchor=tk.W, padx=10)

        self.wp2_radio = tk.Radiobutton(col3_frame, text="2 WP", variable=self.wp_mode_var,
                                   value=2, command=self.on_mode_changed)
        self.wp2_radio.pack(anchor=tk.W, padx=10)

        # Betriebsart (Operating Mode)
        op_mode_label = tk.Label(col3_frame, text="Betriebsart:",
                                 font=("Arial", 10, "bold"))
        op_mode_label.pack(pady=(20, 5))

        self.operating_mode_var = tk.StringVar(
            value=self.OPERATING_MODE_DISPLAY[self.determine_initial_operating_mode()])

        op_mode_combo = ttk.Combobox(col3_frame, textvariable=self.operating_mode_var,
                                     values=list(self.OPERATING_MODE_DISPLAY.values()),
                                     state="readonly", width=15)
        op_mode_combo.pack(anchor=tk.W, padx=10)
        op_mode_combo.bind("<<ComboboxSelected>>", self.on_operating_mode_changed)

        # Energie-Akkumulation Toggle
        self.accumulator_enabled_var = tk.BooleanVar(
            value=self.state.get("accumulator_enabled", True))

        accumulator_check = tk.Checkbutton(
            col3_frame, text="Energie-Akkumulation (alle 10s)",
            variable=self.accumulator_enabled_var,
            command=self.on_accumulator_toggle)
        accumulator_check.pack(anchor=tk.W, padx=10, pady=(20, 5))

        # Inkremente pro Akkumulations-Intervall (sofort wirksam)
        increment_label = tk.Label(col3_frame, text="Inkrement pro Intervall:",
                                   font=("Arial", 10, "bold"))
        increment_label.pack(pady=(10, 5))

        self.increment_vars = {}
        self.create_increment_control(col3_frame, "Elektrisch:", "electrical_increment")
        self.create_increment_control(col3_frame, "Thermisch:", "thermal_increment")

        # 32-bit Register-Reihenfolge
        int32_order_label = tk.Label(col3_frame, text="32-bit Register-Reihenfolge:",
                                     font=("Arial", 10, "bold"))
        int32_order_label.pack(pady=(20, 5))

        self.int32_order_var = tk.StringVar(
            value=self.state.get("int32_register_order", "high_first"))

        tk.Radiobutton(col3_frame, text="High-Word zuerst", variable=self.int32_order_var,
                      value="high_first", command=self.on_int32_order_changed).pack(anchor=tk.W, padx=10)
        tk.Radiobutton(col3_frame, text="Low-Word zuerst", variable=self.int32_order_var,
                      value="low_first", command=self.on_int32_order_changed).pack(anchor=tk.W, padx=10)

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

        # Newly (de-)aktivierte Wärmepumpe(n) auf die aktuelle Betriebsart bringen
        self.apply_operating_mode(self.state.get("operating_mode", "heating"))

    def determine_initial_operating_mode(self):
        """Ermittelt die Start-Betriebsart aus dem tatsächlich gespeicherten HP1-Register (1003),
        statt aus dem separaten (ggf. fehlenden oder veralteten) 'operating_mode'-State-Key."""
        hp1_state = get_register_value(self.state, 1003)
        if hp1_state is None:
            hp1_state = self.default_values.get(1003)

        mode = MODES_BY_VALUE.get(hp1_state, self.state.get("operating_mode", "heating"))

        self.state["operating_mode"] = mode
        save_state(self.state)
        return mode

    def on_operating_mode_changed(self, event=None):
        """Betriebsart wurde per Dropdown geändert."""
        mode = self.OPERATING_MODE_DISPLAY_REVERSE[self.operating_mode_var.get()]
        self.state["operating_mode"] = mode
        save_state(self.state)
        self.apply_operating_mode(mode)

    def apply_operating_mode(self, mode):
        """Setzt HP-, HC-, Boiler- und Buffer-Register aller aktiven WPs auf die Betriebsart."""
        cascade = MODE_CASCADE[mode]
        hp_indices = [1, 2] if self.wp_mode_var.get() == 2 else [1]

        for idx in hp_indices:
            offset = (idx - 1) * 100
            self.set_register_value(1003 + offset, cascade["hp"])
            self.set_register_value(5001 + offset, cascade["hc"])
            self.set_register_value(2001 + offset, cascade["boiler"])
            self.set_register_value(3001 + offset, cascade["buffer"])

    def set_register_value(self, address, value):
        """Setzt einen Register-Wert in State, Server und GUI-Combobox."""
        if address not in REGISTER_MAPPINGS:
            return

        update_register_value(self.state, address, value)

        if self.server_thread and self.server_thread.running:
            self.server_thread.update_register_value(address, value)

        var = self.register_vars.get(address)
        if var is not None:
            mapping = REGISTER_MAPPINGS[address]["mapping"]
            if mapping and value in mapping:
                var.set(f"{value} - {mapping[value]}")

        self.add_log(f"Register {address} changed to {value} ({get_value_text(address, value)})")

    def start_server(self):
        """Starte den Modbus-Server."""
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.wp1_radio.config(state=tk.DISABLED)
        self.wp2_radio.config(state=tk.DISABLED)

        # Filter registers based on WP mode
        hp_mode = self.wp_mode_var.get()
        filtered_registers = filter_registers_for_mode(self.registers, hp_mode)

        self.add_log(f"Starting server with {len(filtered_registers)} registers (WP mode: {hp_mode})")

        self.server_thread = ModbusServerThread(self.log_queue, filtered_registers,
                                                int32_order=self.int32_order_var.get())
        self.server_thread.start()

        self.add_log("Server started on port 5020")

        # Start accumulator timer
        self.start_accumulator_timer()

    def stop_server(self):
        """Stoppe den Modbus-Server."""
        if self.server_thread:
            self.server_thread.stop()
            self.server_thread.join(timeout=5)
            if self.server_thread.is_alive():
                self.add_log("WARNING: Server thread did not stop within 5s")
            self.server_thread = None

        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.wp1_radio.config(state=tk.NORMAL)
        self.wp2_radio.config(state=tk.NORMAL)

        # Stop accumulator timer
        if self.accumulator_timer:
            self.root.after_cancel(self.accumulator_timer)
            self.accumulator_timer = None

        self.add_log("Server stopped")
        
    def on_accumulator_toggle(self):
        """Energie-Akkumulation wurde per Checkbox ein-/ausgeschaltet."""
        enabled = self.accumulator_enabled_var.get()
        self.state["accumulator_enabled"] = enabled
        save_state(self.state)
        self.add_log(f"Energie-Akkumulation {'aktiviert' if enabled else 'deaktiviert'}")

    def create_increment_control(self, parent, label_text, state_key):
        """Erstelle ein Eingabefeld für einen Akkumulator-Inkrementwert."""
        frame = tk.Frame(parent)
        frame.pack(fill=tk.X, padx=10, pady=2)

        tk.Label(frame, text=label_text, width=11, anchor=tk.W).pack(side=tk.LEFT)

        var = tk.StringVar(value=str(self.get_increment(state_key)))
        self.increment_vars[state_key] = var

        entry = tk.Entry(frame, textvariable=var, width=8)
        entry.pack(side=tk.LEFT)

        var.trace_add("write",
                      lambda *_: self.on_increment_changed(state_key, entry))

    def get_increment(self, state_key):
        """Liefert den aktuellen Inkrementwert aus dem State."""
        return self.state.get(state_key, self.DEFAULT_INCREMENTS[state_key])

    def on_increment_changed(self, state_key, entry):
        """Inkrementwert wurde bearbeitet - gültige Werte sofort übernehmen."""
        text = self.increment_vars[state_key].get().strip()

        try:
            value = int(text)
            if value < 0:
                raise ValueError(text)
        except ValueError:
            entry.config(bg="#ffcccc")  # ungültige Eingabe markieren, alten Wert behalten
            return

        entry.config(bg="white")

        if self.get_increment(state_key) == value:
            return

        self.state[state_key] = value
        save_state(self.state)
        self.add_log(f"{self.INCREMENT_LABELS[state_key]} auf {value} gesetzt")

    def start_accumulator_timer(self):
        """Starte Timer für Auto-Inkrementierung (alle 10 Sekunden)."""
        try:
            if (self.server_thread and self.server_thread.running
                    and self.accumulator_enabled_var.get()):
                electrical_addrs = [1020]  # compressor_power_consumption_accumulated
                thermal_addrs = [1022]     # compressor_thermal_energy_output_accumulated

                if self.wp_mode_var.get() == 2:  # Add WP2
                    electrical_addrs.append(1120)
                    thermal_addrs.append(1122)

                for addr in electrical_addrs:
                    self.increment_accumulator_register(
                        addr, self.get_increment("electrical_increment"))
                for addr in thermal_addrs:
                    self.increment_accumulator_register(
                        addr, self.get_increment("thermal_increment"))
        finally:
            # Timer immer weiterlaufen lassen, auch wenn eine Inkrementierung fehlschlägt
            self.accumulator_timer = self.root.after(10000, self.start_accumulator_timer)

    def increment_accumulator_register(self, addr, delta):
        """Erhöht einen 32-bit Akkumulator-Registerwert (Worte bei addr/addr+1) um delta."""
        order = self.int32_order_var.get()

        word_a = get_register_value(self.state, addr, 0)
        word_b = get_register_value(self.state, addr + 1, 0)
        current_value = decode_32bit(word_a, word_b, order)

        new_value = current_value + delta
        new_word_a, new_word_b = encode_32bit(new_value, order)

        # Update both registers
        update_register_value(self.state, addr, new_word_a)
        update_register_value(self.state, addr + 1, new_word_b)

        if self.server_thread:
            self.server_thread.update_register_value(addr, new_word_a)
            self.server_thread.update_register_value(addr + 1, new_word_b)

    def on_int32_order_changed(self):
        """32-bit Register-Reihenfolge wurde per Radiobutton geändert."""
        old_order = self.state.get("int32_register_order", "high_first")
        new_order = self.int32_order_var.get()

        self.state["int32_register_order"] = new_order
        save_state(self.state)

        if new_order != old_order:
            self.reencode_32bit_registers(old_order, new_order)

        self.add_log(f"32-bit Register-Reihenfolge geändert: {new_order}")

    def reencode_32bit_registers(self, old_order, new_order):
        """Schreibt alle 32-bit Register neu, sodass ihr Wert beim Wechsel der Wortreihenfolge erhalten bleibt."""
        addresses = {reg['address'] for reg in self.registers
                    if reg['type'] in ('int32', 'uint32')}

        for addr in addresses:
            word_a = get_register_value(self.state, addr, 0)
            word_b = get_register_value(self.state, addr + 1, 0)
            value = decode_32bit(word_a, word_b, old_order)

            new_word_a, new_word_b = encode_32bit(value, new_order)
            update_register_value(self.state, addr, new_word_a)
            update_register_value(self.state, addr + 1, new_word_b)

            if self.server_thread and self.server_thread.running:
                self.server_thread.update_register_value(addr, new_word_a)
                self.server_thread.update_register_value(addr + 1, new_word_b)
    
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
