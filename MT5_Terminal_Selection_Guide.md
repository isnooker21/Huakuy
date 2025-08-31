# MT5 Terminal Selection Feature - Implementation Guide

## Overview
This document describes the newly implemented MT5 Terminal Selection Feature that allows users to discover, select, and connect to specific MetaTrader 5 terminals when multiple terminals are running.

## Features Implemented

### 🔍 Terminal Discovery System
- **Cross-Platform Support**: Windows, Linux (Wine), macOS (Wine)
- **Automatic Detection**: Scans for running MT5 terminal processes
- **Safe Connection Testing**: Retrieves terminal and account information
- **Fallback Handling**: Provides default options when no terminals found

### 🖥️ Enhanced GUI Components
- **Scan Button**: `🔍 Scan` - Discovers available terminals
- **Refresh Button**: `🔄 Refresh` - Updates terminal list
- **Selection Dropdown**: 25-character width combobox for terminal selection
- **Info Display**: Shows selected terminal details (Login@Server format)
- **Auto-Scan**: Automatically scans for terminals on application startup

### 🔌 Smart Connection Management
- **Specific Terminal Connection**: Connects to user-selected terminal
- **Default Fallback**: Falls back to default connection if no terminal selected
- **Enhanced Dialogs**: Improved user prompts and error messages
- **Non-Blocking Operations**: Threaded scanning and connection to prevent UI freezing

## User Workflow

1. **Application Startup**
   - GUI automatically scans for available terminals
   - Results populate in dropdown menu

2. **Manual Terminal Discovery**
   - Click `🔍 Scan` or `🔄 Refresh` to find terminals
   - System detects running MT5 processes across platforms
   - Terminal information displayed in dropdown as "MT5 - Login@Server"

3. **Terminal Selection**
   - Select desired terminal from dropdown
   - Terminal info updates to show login and server details
   - Selection is stored for connection

4. **Connection Process**
   - Click `🔌 Connect MT5` to connect to selected terminal
   - If no terminal selected, system prompts to scan first
   - Option to proceed with default connection if preferred

## Technical Implementation

### Core Classes and Methods

#### TradingSystem Class Extensions
```python
# Terminal scanning and management
def scan_available_terminals(self) -> List[Dict]
def _scan_windows_terminals(self) -> List[Dict]
def _scan_linux_terminals(self) -> List[Dict] 
def _scan_macos_terminals(self) -> List[Dict]
def _get_running_terminal_info(self) -> Dict
def _get_default_terminal(self) -> List[Dict]

# Terminal connection
def connect_to_specific_terminal(self, terminal_path: str) -> bool
def get_terminal_info(self, terminal_path: str) -> Dict

# State management
self.available_terminals: List[Dict]
self.selected_terminal: Dict
self.terminal_scan_in_progress: bool
```

#### TradingGUI Class Extensions
```python
# GUI components
self.scan_btn: ttk.Button
self.refresh_btn: ttk.Button
self.terminal_combobox: ttk.Combobox
self.terminal_var: tk.StringVar
self.terminal_info_label: ttk.Label

# Event handlers
def scan_terminals(self)
def refresh_terminals(self)
def auto_scan_terminals(self)
def on_terminal_selected(self, event=None)
def update_terminal_list(self, terminals)
def scan_error(self, error_msg)

# Connection management
def connect_mt5(self)  # Enhanced with terminal selection
def connection_complete(self, success, terminal_name)
def connection_error(self, error_msg)
```

### Platform-Specific Terminal Detection

#### Windows
- Uses `tasklist` command to find `terminal64.exe` processes
- Directly connects to running terminal to retrieve info
- Handles multiple terminal instances

#### Linux/macOS (Wine)
- Uses `pgrep -f terminal64.exe` to find Wine processes
- Supports MT5 running under Wine environment
- Safe fallback for missing commands

### Error Handling

#### Scan Failures
- Timeout protection (10-second limit on subprocess calls)
- Platform command not found (graceful degradation)
- Process access errors (continues with default options)

#### Connection Failures
- Invalid terminal paths
- MT5 initialization failures
- Account information retrieval errors
- Connection dialog error reporting

#### GUI Error States
- Disabled buttons during operations
- Clear status messages
- Error dialog boxes with detailed information
- Automatic state restoration after errors

## Configuration Options

### Terminal Discovery Settings
```python
# Subprocess timeout for platform commands
timeout=10  # seconds

# Platform detection
platform.system()  # "Windows", "Linux", "Darwin"

# Default terminal options
{
    'path': 'default',
    'login': 'Not Connected',
    'server': 'Not Connected',
    'company': 'Unknown',
    'name': 'MetaTrader 5',
    'build': 'Unknown',
    'connected': False,
    'display_name': 'Default MT5 Terminal'
}
```

### GUI Settings
```python
# Combobox width for terminal display
width=25  # characters

# Auto-scan delay after startup
self.root.after(1000, self.auto_scan_terminals)  # 1 second

# Button styles
style='Custom.TButton'
font=('Arial', 8)
```

## Testing and Validation

### Comprehensive Test Suite
The implementation includes a comprehensive test suite that validates:

- ✅ All required features from problem statement
- ✅ Complete user workflow implementation
- ✅ Robust error handling scenarios
- ✅ Cross-platform compatibility
- ✅ GUI component integration

### Manual Testing Scenarios
1. **Single Terminal**: Test with one MT5 terminal running
2. **Multiple Terminals**: Test terminal selection with multiple instances
3. **No Terminals**: Test fallback behavior when no terminals found
4. **Platform Differences**: Test on Windows, Linux, and macOS
5. **Error Conditions**: Test scan timeouts, connection failures, invalid selections

## Backward Compatibility

The implementation maintains full backward compatibility:

- Existing `Connect MT5` functionality preserved
- Default connection still available if no terminal selected
- All existing trading system functionality unaffected
- Original connection retry and health check logic intact

## Future Enhancements

Potential areas for future improvement:

1. **Terminal Installation Path Detection**: Scan common installation directories
2. **Multiple Account Support**: Handle terminals with multiple accounts
3. **Terminal Status Monitoring**: Real-time connection status updates
4. **Custom Terminal Paths**: Allow manual terminal path specification
5. **Terminal Profiles**: Save and load preferred terminal configurations

## Troubleshooting

### Common Issues and Solutions

#### "No terminals found"
- Ensure MT5 terminal is running
- Check if terminal process is accessible
- Try refresh button to re-scan
- Use default connection as fallback

#### "Scan timeout"
- Check system performance and load
- Verify platform commands (tasklist/pgrep) are available
- Try manual scan after system settles

#### "Connection failed to selected terminal"
- Verify terminal is still running
- Check terminal accessibility and permissions
- Try connecting to default terminal
- Restart MT5 terminal if necessary

#### Platform-specific issues
- **Windows**: Ensure tasklist command is available
- **Linux/macOS**: Ensure pgrep command exists and Wine is properly configured
- **All platforms**: Check MT5 Python library installation

---

*This feature successfully addresses all requirements from the original problem statement and provides a robust, cross-platform solution for MT5 terminal selection in multi-terminal environments.*