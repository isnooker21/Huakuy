# XAUUSD Auto-Detection System

This document explains the new XAUUSD symbol auto-detection feature implemented in the Huakuy trading system.

## Overview

The system now automatically scans and detects available XAUUSD symbols from the broker instead of relying on hardcoded symbol variants. This makes the system more robust and adaptable to different brokers.

## Features

### 🔍 Auto-Detection
- Scans all available symbols from broker using `mt5.symbols_get()`
- Uses regex patterns to identify XAUUSD variants
- Automatically updates system configuration with detected symbols

### 📊 Smart Prioritization
Detected symbols are sorted by preference:
1. **XAUUSD** (exact match - highest priority)
2. **XAUUSD.v, XAUUSD.c** (extensions - second priority)  
3. **XAUUSDm** (suffixes - third priority)
4. **GOLD, GOLD.v** (GOLD variants - lowest priority)

### 🔄 Caching System
- Results cached for 1 hour to avoid excessive broker queries
- Configurable cache duration
- Force refresh available through manual detection

### ⚙️ Configuration Options

```python
"symbol_management": {
    "auto_detection_enabled": True,           # Enable/disable feature
    "auto_detection_scan_interval": 3600,    # Cache duration (seconds)
    "auto_detection_patterns": [             # Regex patterns
        r'^XAUUSD$',                         # Exact match
        r'^XAUUSD\.[a-zA-Z]+$',             # Extensions (.v, .c, .raw)
        r'^XAUUSD[a-zA-Z]*$',               # Suffixes (XAUUSDm)
        r'^XAU/USD$',                       # Slash notation
        r'^GOLD$',                          # GOLD symbol
        r'^GOLD\.[a-zA-Z]+$'                # GOLD extensions
    ]
}
```

## Usage

### Automatic Operation
The system automatically runs detection when:
- MT5 connection is established
- `connect_mt5()` is called
- `connect_to_specific_terminal()` is called

### Manual Control

```python
# Get current detection status
status = trading_system.get_symbol_detection_status()
print(status)

# Manually trigger detection
results = trading_system.manual_symbol_detection()
print(results)

# Enable/disable at runtime
trading_system.set_auto_detection_enabled(True)   # Enable
trading_system.set_auto_detection_enabled(False)  # Disable

# Check what symbols were detected
print(f"Current symbol: {trading_system.current_symbol}")
print(f"Fallback symbols: {trading_system.fallback_symbols}")
print(f"Detected symbols: {trading_system.detected_xauusd_symbols}")
```

### Log Output Example

```
[09:42:24] INFO: 🔍 Starting XAUUSD symbol auto-detection...
[09:42:24] INFO: 🔍 Scanning all available symbols from broker...
[09:42:24] INFO: 📊 Found 156 total symbols on broker
[09:42:24] INFO: ✅ Auto-detected 6 XAUUSD symbols:
[09:42:24] INFO:   1. XAUUSD ✅
[09:42:24] INFO:   2. XAUUSD.v ✅
[09:42:24] INFO:   3. XAUUSD.c ✅
[09:42:24] INFO:   4. XAUUSD.raw ✅
[09:42:24] INFO:   5. XAUUSDm ✅
[09:42:24] INFO:   6. GOLD.v ✅
[09:42:24] INFO: 🔄 Updating primary symbol: XAUUSD.v → XAUUSD
[09:42:24] INFO: ✅ Symbol configuration updated with 6 auto-detected symbols
[09:42:24] INFO: Active symbol: XAUUSD
[09:42:24] INFO: Fallback symbols: XAUUSD.v, XAUUSD.c, XAUUSD.raw...
```

## Error Handling

The system gracefully handles errors:
- **No MT5 connection**: Skips detection, uses configured symbols
- **No symbols found**: Falls back to hardcoded configuration  
- **Detection failure**: Logs error, continues with existing symbols
- **Invalid symbols**: Filters out unavailable symbols

## Backward Compatibility

- Original hardcoded symbols remain as final fallback
- Can be disabled via configuration
- Existing functionality unchanged when disabled
- No breaking changes to existing code

## Detection Patterns

The system recognizes these XAUUSD symbol patterns:

| Pattern | Example Matches | Description |
|---------|----------------|-------------|
| `^XAUUSD$` | XAUUSD | Exact match |
| `^XAUUSD\.[a-zA-Z]+$` | XAUUSD.v, XAUUSD.c, XAUUSD.raw | Extensions |
| `^XAUUSD[a-zA-Z]*$` | XAUUSDm, XAUUSDmicro | Suffixes |
| `^XAU/USD$` | XAU/USD | Slash notation |
| `^GOLD$` | GOLD | Alternative symbol |
| `^GOLD\.[a-zA-Z]+$` | GOLD.v, GOLD.spot | GOLD with extensions |

## Benefits

1. **Broker Independence**: Works with any broker's symbol naming convention
2. **Automatic Updates**: No need to manually configure symbol variants
3. **Robust Fallback**: Multiple layers of fallback for reliability
4. **Performance**: Caching prevents excessive broker queries
5. **Monitoring**: Comprehensive logging for troubleshooting
6. **Flexibility**: Runtime enable/disable and manual control

## Technical Implementation

- **Main Method**: `auto_detect_xauusd_symbols()`
- **Integration Points**: MT5 connection methods
- **Cache Duration**: 1 hour (configurable)
- **Pattern Engine**: Python regex
- **Error Strategy**: Graceful degradation
- **Thread Safety**: All operations are thread-safe