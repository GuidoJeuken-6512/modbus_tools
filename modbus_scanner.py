import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pymodbus.client import ModbusTcpClient
import csv
import threading
import time
import logging
from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ModbusScanner:
    def __init__(self, root):
        self.root = root
        self.root.title("Modbus Register Scanner")
        self.root.geometry("800x600")

        # Scanner state
        self.scanning = False
        self.scan_thread = None
        self.found_registers = []

        # Create GUI
        self.create_widgets()

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configuration frame
        config_frame = ttk.LabelFrame(
            main_frame, text="Scanner Configuration", padding="10"
        )
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E),
                          pady=(0, 10))

        # Server IP
        ttk.Label(config_frame, text="Server IP:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        self.ip_entry = ttk.Entry(config_frame, width=20)
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.ip_entry.insert(0, "192.168.178.125")

        # Port
        ttk.Label(config_frame, text="Port:").grid(
            row=0, column=2, padx=5, pady=5, sticky="e"
        )
        self.port_entry = ttk.Entry(config_frame, width=10)
        self.port_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.port_entry.insert(0, "502")

        # Register range
        ttk.Label(config_frame, text="Start Register:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        self.start_entry = ttk.Entry(config_frame, width=10)
        self.start_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.start_entry.insert(0, "0")

        ttk.Label(config_frame, text="Stop Register:").grid(
            row=1, column=2, padx=5, pady=5, sticky="e"
        )
        self.stop_entry = ttk.Entry(config_frame, width=10)
        self.stop_entry.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        self.stop_entry.insert(0, "1000")

        # Register type
        ttk.Label(config_frame, text="Register Type:").grid(
            row=2, column=0, padx=5, pady=5, sticky="e"
        )
        self.register_type = ttk.Combobox(
            config_frame, values=["Holding Registers", "Input Registers"],
            width=15
        )
        self.register_type.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.register_type.set("Holding Registers")

        # Scan delay
        ttk.Label(config_frame, text="Delay (ms):").grid(
            row=2, column=2, padx=5, pady=5, sticky="e"
        )
        self.delay_entry = ttk.Entry(config_frame, width=10)
        self.delay_entry.grid(row=2, column=3, padx=5, pady=5, sticky="w")
        self.delay_entry.insert(0, "50")

        # Retry settings
        ttk.Label(config_frame, text="Max Retries:").grid(
            row=3, column=0, padx=5, pady=5, sticky="e"
        )
        self.retry_entry = ttk.Entry(config_frame, width=10)
        self.retry_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        self.retry_entry.insert(0, "3")

        ttk.Label(config_frame, text="Timeout (s):").grid(
            row=3, column=2, padx=5, pady=5, sticky="e"
        )
        self.timeout_entry = ttk.Entry(config_frame, width=10)
        self.timeout_entry.grid(row=3, column=3, padx=5, pady=5, sticky="w")
        self.timeout_entry.insert(0, "5")

        # Control buttons
        button_frame = ttk.Frame(config_frame)
        button_frame.grid(row=4, column=0, columnspan=4, pady=10)

        self.scan_button = ttk.Button(
            button_frame, text="Start Scan", command=self.start_scan
        )
        self.scan_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(
            button_frame, text="Stop Scan", command=self.stop_scan,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.export_button = ttk.Button(
            button_frame, text="Export CSV", command=self.export_csv,
            state=tk.DISABLED
        )
        self.export_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(
            button_frame, text="Clear Results", command=self.clear_results
        )
        self.clear_button.pack(side=tk.LEFT, padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E),
                           pady=5)

        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to scan")
        self.status_label.grid(row=2, column=0, columnspan=1, pady=5, sticky="w")
        
        # Connection status label
        self.connection_status = ttk.Label(main_frame, text="", foreground="green")
        self.connection_status.grid(row=2, column=1, columnspan=1, pady=5, sticky="e")

        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Scan Results",
                                       padding="10")
        results_frame.grid(row=3, column=0, columnspan=2,
                           sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))

        # Treeview for results
        columns = ("Register", "Value (Hex)", "Value (Dec)", "Type")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings",
                                 height=15)

        # Configure columns
        self.tree.heading("Register", text="Register")
        self.tree.heading("Value (Hex)", text="Value (Hex)")
        self.tree.heading("Value (Dec)", text="Value (Dec)")
        self.tree.heading("Type", text="Type")

        self.tree.column("Register", width=100)
        self.tree.column("Value (Hex)", width=120)
        self.tree.column("Value (Dec)", width=120)
        self.tree.column("Type", width=150)

        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL,
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

    def start_scan(self):
        """Start the scanning process"""
        try:
            start_reg = int(self.start_entry.get())
            stop_reg = int(self.stop_entry.get())
            delay = int(self.delay_entry.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric "
                                                "values.")
            return

        if start_reg >= stop_reg:
            messagebox.showerror("Input Error", "Start register must be less "
                                                "than stop register.")
            return

        if stop_reg - start_reg > 10000:
            messagebox.showwarning("Warning", "Large range selected. This may "
                                              "take a long time.")

        self.scanning = True
        self.scan_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.export_button.config(state=tk.DISABLED)

        # Clear previous results
        self.clear_results()

        # Start scan in separate thread
        self.scan_thread = threading.Thread(
            target=self.scan_registers, args=(start_reg, stop_reg, delay)
        )
        self.scan_thread.daemon = True
        self.scan_thread.start()

    def stop_scan(self):
        """Stop the scanning process"""
        self.scanning = False
        self.scan_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Scan stopped by user")

    def create_client(self, ip, port):
        """Create and connect Modbus client with retry logic"""
        max_retries = 3
        retry_delay = 1  # seconds
        timeout = 5
        
        try:
            timeout = int(self.timeout_entry.get())
        except ValueError:
            timeout = 5
        
        for attempt in range(max_retries):
            try:
                client = ModbusTcpClient(ip, port=port, timeout=timeout)
                if client.connect():
                    logger.info(f"Connected to {ip}:{port} (attempt {attempt + 1})")
                    return client
                else:
                    logger.warning(f"Connection attempt {attempt + 1} failed")
                    client.close()
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} error: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
        
        return None

    def read_register_with_retry(self, client, register, reg_type, max_retries=None):
        """Read a single register with retry logic and auto-reconnect"""
        if max_retries is None:
            try:
                max_retries = int(self.retry_entry.get())
            except ValueError:
                max_retries = 3
                
        for attempt in range(max_retries):
            try:
                if reg_type == "Holding Registers":
                    response = client.read_holding_registers(
                        address=register, count=1)
                else:
                    response = client.read_input_registers(
                        address=register, count=1)

                if hasattr(response, 'registers') and response.registers:
                    return response.registers[0]
                else:
                    return None

            except Exception as exc:
                logger.warning(f"Error reading register {register} "
                              f"(attempt {attempt + 1}): {exc}")
                
                # Check if it's a connection error
                error_str = str(exc).lower()
                if any(keyword in error_str for keyword in 
                       ["10054", "connection", "reset", "closed", "timeout"]):
                    logger.info("Connection lost, attempting to reconnect...")
                    client.close()
                    
                    # Try to reconnect
                    ip = self.ip_entry.get()
                    port = int(self.port_entry.get())
                    new_client = self.create_client(ip, port)
                    if new_client:
                        # Update the client reference
                        client = new_client
                        logger.info("Reconnected successfully")
                    else:
                        logger.error("Failed to reconnect")
                        return None
                else:
                    # For other errors, just retry with exponential backoff
                    if attempt < max_retries - 1:
                        sleep_time = 0.5 * (2 ** attempt)  # Exponential backoff
                        time.sleep(sleep_time)
        
        return None

    def scan_registers(self, start_reg, stop_reg, delay):
        """Scan registers in a separate thread with robust connection handling"""
        ip = self.ip_entry.get()
        port = int(self.port_entry.get())
        reg_type = self.register_type.get()

        # Create initial connection
        self.root.after(0, lambda: self.connection_status.config(
            text="Connecting...", foreground="orange"))
        client = self.create_client(ip, port)
        if not client:
            self.root.after(0, lambda: messagebox.showerror(
                "Connection Error", f"Unable to connect to {ip}:{port}"))
            self.root.after(0, lambda: self.connection_status.config(
                text="Connection Failed", foreground="red"))
            self.root.after(0, self.stop_scan)
            return
        
        self.root.after(0, lambda: self.connection_status.config(
            text="Connected", foreground="green"))

        try:
            total_registers = stop_reg - start_reg + 1
            found_count = 0
            consecutive_errors = 0
            max_consecutive_errors = 10

            for i, register in enumerate(range(start_reg, stop_reg + 1)):
                if not self.scanning:
                    break

                # Read register with retry logic
                value = self.read_register_with_retry(client, register, reg_type)
                
                if value is not None:
                    found_count += 1
                    consecutive_errors = 0  # Reset error counter

                    # Add to results
                    result = {
                        'register': register,
                        'value_hex': f"0x{value:04X}",
                        'value_dec': value,
                        'type': reg_type
                    }
                    self.found_registers.append(result)

                    # Update GUI in main thread
                    self.root.after(0, lambda r=result:
                                   self.add_result_to_tree(r))

                    logger.info(f"Found register {register}: "
                               f"0x{value:04X} ({value})")
                else:
                    consecutive_errors += 1
                    
                    # If too many consecutive errors, try to reconnect
                    if consecutive_errors >= max_consecutive_errors:
                        logger.warning("Too many consecutive errors, "
                                      "attempting to reconnect...")
                        self.root.after(0, lambda: self.connection_status.config(
                            text="Reconnecting...", foreground="orange"))
                        client.close()
                        client = self.create_client(ip, port)
                        if not client:
                            logger.error("Failed to reconnect, stopping scan")
                            self.root.after(0, lambda: self.connection_status.config(
                                text="Connection Lost", foreground="red"))
                            break
                        else:
                            self.root.after(0, lambda: self.connection_status.config(
                                text="Reconnected", foreground="green"))
                        consecutive_errors = 0

                # Update progress
                progress = int((i + 1) / total_registers * 100)
                self.root.after(0, lambda p=progress:
                              self.progress.config(value=p))
                self.root.after(0, lambda i=i, t=total_registers,
                              f=found_count:
                              self.status_label.config(
                                  text=f"Scanning... {i+1}/{t} "
                                       f"registers, {f} found"))

                # Delay between reads
                if delay > 0:
                    time.sleep(delay / 1000.0)

            # Scan completed
            self.root.after(0, lambda: self.status_label.config(
                text=f"Scan completed. Found {found_count} active "
                     f"registers."))
            self.root.after(0, self.stop_scan)
            if found_count > 0:
                self.root.after(0, lambda: self.export_button.config(
                    state=tk.NORMAL))

        except Exception as exc:
            error_msg = f"Scan error: {str(exc)}"
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            self.root.after(0, self.stop_scan)
        finally:
            if client:
                client.close()

    def add_result_to_tree(self, result):
        """Add a result to the treeview"""
        self.tree.insert("", "end", values=(
            result['register'],
            result['value_hex'],
            result['value_dec'],
            result['type']
        ))

    def clear_results(self):
        """Clear all results"""
        self.tree.delete(*self.tree.get_children())
        self.found_registers.clear()
        self.progress.config(value=0)
        self.status_label.config(text="Ready to scan")
        self.connection_status.config(text="", foreground="green")

    def export_csv(self):
        """Export results to CSV file"""
        if not self.found_registers:
            messagebox.showwarning("No Data", "No results to export.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save scan results"
        )

        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Register', 'Value (Hex)', 'Value (Dec)',
                                     'Type', 'Timestamp'])

                    for result in self.found_registers:
                        writer.writerow([
                            result['register'],
                            result['value_hex'],
                            result['value_dec'],
                            result['type'],
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        ])

                messagebox.showinfo("Export Complete",
                                    f"Results exported to {filename}")
                logger.info(f"Exported {len(self.found_registers)} "
                            f"registers to {filename}")

            except Exception as exc:
                messagebox.showerror("Export Error",
                                     f"Failed to export CSV: {str(exc)}")


def main():
    root = tk.Tk()
    ModbusScanner(root)
    root.mainloop()


if __name__ == "__main__":
    main()