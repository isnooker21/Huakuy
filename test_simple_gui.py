#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import queue
from datetime import datetime

# Mock classes for testing without MT5
class MockTradingSystem:
    def __init__(self):
        self.mt5_connected = False
        self.trading_active = False
        self.positions = []
        self.buy_volume = 0.0
        self.sell_volume = 0.0
        self.root = None
        self.log_queue = queue.Queue()
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        try:
            self.log_queue.put_nowait(formatted_msg)
        except:
            pass
    
    def connect_mt5(self):
        time.sleep(1)  # Simulate connection time
        self.mt5_connected = True
        self.log("Mock MT5 connection successful")
        return True
    
    def disconnect_mt5(self):
        self.mt5_connected = False
        self.trading_active = False
        self.log("Mock MT5 disconnected")
    
    def scan_available_terminals(self):
        time.sleep(2)  # Simulate scan time
        return [
            {'display_name': 'Mock Terminal 1', 'path': '/mock/path1'},
            {'display_name': 'Mock Terminal 2', 'path': '/mock/path2'}
        ]
    
    def update_positions(self):
        # Mock position update
        pass
    
    def trading_loop(self):
        """Mock trading loop"""
        while self.trading_active:
            self.log("Mock trading cycle...")
            time.sleep(5)

class SimplifiedTradingGUI:
    def __init__(self):
        self.trading_system = MockTradingSystem()
        self.setup_gui()
        self.update_loop()

    def setup_gui(self):
        """Setup simple, reliable GUI"""
        self.root = tk.Tk()
        self.root.title("AI Gold Grid Trading System v3.0 - Simplified")
        self.root.geometry("1000x700")
        
        # Simple header
        header_frame = tk.Frame(self.root)
        header_frame.pack(fill='x', padx=10, pady=5)
        
        title_label = tk.Label(header_frame, text="AI Gold Grid Trading System v3.0 - Simplified", 
                              font=('Arial', 14, 'bold'))
        title_label.pack(side='left')
        
        self.connection_status = tk.Label(header_frame, text="Disconnected", 
                                        fg='red', font=('Arial', 10, 'bold'))
        self.connection_status.pack(side='right')
        
        # Control panel
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # Connection controls
        conn_frame = tk.LabelFrame(control_frame, text="Connection", padx=5, pady=5)
        conn_frame.pack(side='left', padx=(0, 10))
        
        self.connect_btn = tk.Button(conn_frame, text="Connect MT5", command=self.connect_mt5)
        self.connect_btn.pack(side='left', padx=2)
        
        self.disconnect_btn = tk.Button(conn_frame, text="Disconnect", command=self.disconnect_mt5)
        self.disconnect_btn.pack(side='left', padx=2)
        
        # Terminal controls
        terminal_frame = tk.LabelFrame(control_frame, text="Terminal", padx=5, pady=5)
        terminal_frame.pack(side='left', padx=(0, 10))
        
        self.scan_btn = tk.Button(terminal_frame, text="Scan Terminals", command=self.scan_terminals)
        self.scan_btn.pack(side='left', padx=2)
        
        self.terminal_var = tk.StringVar()
        self.terminal_combobox = ttk.Combobox(terminal_frame, textvariable=self.terminal_var, 
                                            state='readonly', width=25)
        self.terminal_combobox.pack(side='left', padx=2)
        self.terminal_combobox.bind('<<ComboboxSelected>>', self.on_terminal_selected)
        
        # Trading controls
        trading_frame = tk.LabelFrame(control_frame, text="Trading", padx=5, pady=5)
        trading_frame.pack(side='left')
        
        self.start_btn = tk.Button(trading_frame, text="Start Trading", command=self.start_trading)
        self.start_btn.pack(side='left', padx=2)
        
        self.stop_btn = tk.Button(trading_frame, text="Stop Trading", command=self.stop_trading)
        self.stop_btn.pack(side='left', padx=2)
        
        # Status info
        status_frame = tk.Frame(self.root)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        self.terminal_info_label = tk.Label(status_frame, text="Click 'Scan Terminals' to find MT5 terminals")
        self.terminal_info_label.pack(side='left')
        
        # Positions display
        pos_frame = tk.LabelFrame(self.root, text="Positions")
        pos_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create Treeview for positions
        self.positions_tree = ttk.Treeview(pos_frame, columns=('Symbol', 'Type', 'Volume', 'Price', 'Profit'), show='headings')
        self.positions_tree.heading('Symbol', text='Symbol')
        self.positions_tree.heading('Type', text='Type')
        self.positions_tree.heading('Volume', text='Volume')
        self.positions_tree.heading('Price', text='Price')
        self.positions_tree.heading('Profit', text='Profit')
        
        pos_scrollbar = ttk.Scrollbar(pos_frame, orient='vertical', command=self.positions_tree.yview)
        self.positions_tree.configure(yscrollcommand=pos_scrollbar.set)
        
        self.positions_tree.pack(side='left', fill='both', expand=True)
        pos_scrollbar.pack(side='right', fill='y')
        
        # Stats
        stats_frame = tk.Frame(self.root)
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        self.stats_label = tk.Label(stats_frame, text="Stats: No positions", font=('Arial', 9))
        self.stats_label.pack(side='left')
        
        # Log display
        log_frame = tk.LabelFrame(self.root, text="Log")
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.log_display = scrolledtext.ScrolledText(log_frame, height=8, font=('Courier', 9))
        self.log_display.pack(fill='both', expand=True)
        
        self.trading_system.root = self.root

    def connect_mt5(self):
        """Connect to MT5"""
        success = self.trading_system.connect_mt5()
        if success:
            self.connection_status.configure(text="Connected", fg='green')
            messagebox.showinfo("Success", "Connected to MT5")
        else:
            self.connection_status.configure(text="Disconnected", fg='red')
            messagebox.showerror("Error", "Failed to connect to MT5")
    
    def disconnect_mt5(self):
        """Disconnect from MT5"""
        self.stop_trading()
        self.trading_system.disconnect_mt5()
        self.connection_status.configure(text="Disconnected", fg='red')
    
    def scan_terminals(self):
        """Scan for available terminals"""
        try:
            self.scan_btn.config(state='disabled')
            self.terminal_info_label.config(text="Scanning terminals...")
            
            def scan_thread():
                try:
                    terminals = self.trading_system.scan_available_terminals()
                    self.root.after(0, self.update_terminal_list, terminals)
                except Exception as e:
                    self.root.after(0, lambda: self.scan_error(str(e)))
            
            threading.Thread(target=scan_thread, daemon=True).start()
            
        except Exception as e:
            self.scan_error(str(e))
    
    def update_terminal_list(self, terminals):
        """Update terminal dropdown list"""
        try:
            self.terminal_combobox['values'] = []
            
            if terminals:
                values = []
                for terminal in terminals:
                    display_name = terminal.get('display_name', 'Unknown Terminal')
                    values.append(display_name)
                
                self.terminal_combobox['values'] = values
                if values:
                    self.terminal_combobox.set(values[0])
                    self.on_terminal_selected()
                
                self.terminal_info_label.config(text=f"Found {len(terminals)} terminal(s)")
            else:
                self.terminal_info_label.config(text="No terminals found")
            
        except Exception as e:
            self.terminal_info_label.config(text=f"Error: {str(e)}")
        finally:
            self.scan_btn.config(state='normal')
    
    def scan_error(self, error_msg):
        """Handle scan error"""
        self.terminal_info_label.config(text=f"Scan failed: {error_msg}")
        self.scan_btn.config(state='normal')
    
    def on_terminal_selected(self, event=None):
        """Handle terminal selection"""
        try:
            selected = self.terminal_var.get()
            if selected:
                self.terminal_info_label.config(text=f"Selected: {selected}")
        except Exception as e:
            self.terminal_info_label.config(text=f"Selection error: {str(e)}")
    
    def start_trading(self):
        """Start automated trading"""
        if not self.trading_system.mt5_connected:
            messagebox.showerror("Error", "Please connect to MT5 first")
            return
        
        if not self.trading_system.trading_active:
            self.trading_system.trading_active = True
            self.trading_thread = threading.Thread(target=self.trading_system.trading_loop, daemon=True)
            self.trading_thread.start()
            
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            messagebox.showinfo("Success", "Trading started")
    
    def stop_trading(self):
        """Stop automated trading"""
        if self.trading_system.trading_active:
            self.trading_system.trading_active = False
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
    
    def update_positions_display(self):
        """Update positions in treeview"""
        try:
            # Clear existing items
            for item in self.positions_tree.get_children():
                self.positions_tree.delete(item)
            
            # Add current positions
            for position in self.trading_system.positions:
                self.positions_tree.insert('', 'end', values=(
                    position.symbol,
                    position.type,
                    f"{position.volume:.2f}",
                    f"{position.open_price:.5f}",
                    f"{position.profit:.2f}"
                ))
        except Exception as e:
            pass  # Silent error handling for display
    
    def update_stats_display(self):
        """Update statistics display"""
        try:
            total_positions = len(self.trading_system.positions)
            buy_volume = self.trading_system.buy_volume
            sell_volume = self.trading_system.sell_volume
            
            stats_text = f"Positions: {total_positions} | Buy: {buy_volume:.2f} | Sell: {sell_volume:.2f}"
            self.stats_label.config(text=stats_text)
        except Exception as e:
            self.stats_label.config(text="Stats: Error loading")
    
    def update_log_display(self):
        """Update log display"""
        try:
            if hasattr(self.trading_system, 'log_queue'):
                while True:
                    try:
                        log_entry = self.trading_system.log_queue.get_nowait()
                        self.log_display.insert(tk.END, f"{log_entry}\n")
                        self.log_display.see(tk.END)
                    except queue.Empty:
                        break
        except Exception as e:
            pass  # Silent error handling for log display

    def update_loop(self):
        """Simple GUI update loop"""
        try:
            if self.trading_system.mt5_connected:
                self.trading_system.update_positions()
                self.update_positions_display()
                self.update_stats_display()
            
            self.update_log_display()
            
        except Exception as e:
            print(f"GUI update error: {str(e)}")
        
        # Schedule next update (every 3 seconds)
        self.root.after(3000, self.update_loop)

    def run(self):
        """Start the simplified GUI application"""
        self.trading_system.log("AI Gold Grid Trading System v3.0 Started")
        self.trading_system.log("Simplified GUI Interface Loaded")
        self.trading_system.log("Ready for MT5 connection")
        self.root.mainloop()

if __name__ == "__main__":
    app = SimplifiedTradingGUI()
    app.run()