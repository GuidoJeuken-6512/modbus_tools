"""Register Manager für GUI - State-Persistierung und Mapping."""
import json
import os
from const_mapping import (
    HP_ERROR_STATE, HP_STATE, HP_OPERATING_STATE,
    BOIL_OPERATING_STATE, BUFF_OPERATING_STATE, HC_OPERATING_STATE,
    SOL_OPERATING_STATE, MAIN_AMBIENT_OPERATING_STATE
)

STATE_FILE = "server_state.json"

# Register-Adressen für State-Mappings
REGISTER_MAPPINGS = {
    0: {
        "name": "Error Number",
        "mapping": None,
        "description": "ambient_error_number"
    },
    1: {
        "name": "Operating State",
        "mapping": MAIN_AMBIENT_OPERATING_STATE,
        "description": "ambient_operating_state"
    },
    1000: {
        "name": "Error State",
        "mapping": HP_ERROR_STATE,
        "description": "hp1_error_state"
    },
    1002: {
        "name": "State",
        "mapping": HP_STATE,
        "description": "hp1_state"
    },
    1003: {
        "name": "Operating State",
        "mapping": HP_OPERATING_STATE,
        "description": "hp1_operating_state"
    },
    1100: {
        "name": "Error State",
        "mapping": HP_ERROR_STATE,
        "description": "hp2_error_state"
    },
    1102: {
        "name": "State",
        "mapping": HP_STATE,
        "description": "hp2_state"
    },
    1103: {
        "name": "Operating State",
        "mapping": HP_OPERATING_STATE,
        "description": "hp2_operating_state"
    },
    2001: {
        "name": "Operating State",
        "mapping": BOIL_OPERATING_STATE,
        "description": "boiler1_operating_state"
    },
    2101: {
        "name": "Operating State",
        "mapping": BOIL_OPERATING_STATE,
        "description": "boiler2_operating_state"
    },
    3001: {
        "name": "Operating State",
        "mapping": BUFF_OPERATING_STATE,
        "description": "buffer1_operating_state"
    },
    3101: {
        "name": "Operating State",
        "mapping": BUFF_OPERATING_STATE,
        "description": "buffer2_operating_state"
    },
    4001: {
        "name": "Operating State",
        "mapping": SOL_OPERATING_STATE,
        "description": "solar1_operating_state"
    },
    5001: {
        "name": "Operating State",
        "mapping": HC_OPERATING_STATE,
        "description": "hc1_operating_state"
    },
    5101: {
        "name": "Operating State",
        "mapping": HC_OPERATING_STATE,
        "description": "hc2_operating_state"
    },
}

# Akkumulator-Register
ACCUMULATOR_REGISTERS = [1020, 1022, 1120, 1122]

def is_wp2_register(address):
    """Prüft ob Register zu WP2 gehört (1100-1199)."""
    return 1100 <= address < 1200

def is_wp1_register(address):
    """Prüft ob Register zu WP1 gehört (1000-1099)."""
    return 1000 <= address < 1100

def is_wp2_device_register(address):
    """Prüft ob Register zu WP2-Geräten gehört (2100-2199, 3100-3199, 5100-5199)."""
    return (2100 <= address < 2200 or  # Boiler 2
            3100 <= address < 3200 or  # Buffer 2
            5100 <= address < 5200)    # HC 2

def is_accumulator_register(address):
    """Prüft ob Register ein Akkumulator-Register ist."""
    return address in ACCUMULATOR_REGISTERS

def filter_registers_for_mode(registers, hp_mode):
    """
    Filtert Register basierend auf WP-Modus.
    Bei 1 WP werden alle WP2-Register entfernt.
    """
    if hp_mode == 2:
        return registers  # Alle Register bei 2 WP-Modus
    
    # Bei 1 WP-Modus: Nur WP1 und gemeinsame Register behalten
    filtered = []
    for reg in registers:
        addr = reg['address']
        
        # WP2-Register entfernen (1100-1199)
        if is_wp2_register(addr):
            continue
        
        # WP2-Geräte-Register entfernen (2100-2199, 3100-3199, 5100-5199)
        if is_wp2_device_register(addr):
            continue
        
        filtered.append(reg)
    
    return filtered

def get_register_mapping(address):
    """Gibt das Mapping-Dictionary für ein Register zurück."""
    return REGISTER_MAPPINGS.get(address, {"name": f"Register {address}", "mapping": None, "description": ""})

def get_value_text(address, value):
    """Konvertiert einen numerischen Wert in einen lesbaren Text basierend auf dem Mapping."""
    mapping = get_register_mapping(address)
    if mapping["mapping"] and value in mapping["mapping"]:
        return mapping["mapping"][value]
    return str(value)

def load_state():
    """Lädt den gespeicherten State aus der JSON-Datei."""
    if not os.path.exists(STATE_FILE):
        return {
            "heat_pump_mode": 1,
            "registers": {},
            "last_accumulated_values": {}
        }
    
    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def save_state(state):
    """Speichert den State in die JSON-Datei."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def update_register_value(state, address, value):
    """Aktualisiert einen Register-Wert im State."""
    state["registers"][str(address)] = value
    save_state(state)

def get_register_value(state, address, default_value=None):
    """Holt einen Register-Wert aus dem State."""
    return state["registers"].get(str(address), default_value)

def update_accumulated_value(state, address, value):
    """Aktualisiert einen Akkumulator-Wert im State."""
    state["last_accumulated_values"][str(address)] = value
    save_state(state)

def get_accumulated_value(state, address, default_value=0):
    """Holt einen Akkumulator-Wert aus dem State."""
    return state["last_accumulated_values"].get(str(address), default_value)
